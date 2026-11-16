from database import get_connection

class Set:
    def __init__(self, weight, reps, rpe):
        self.id = None
        self.exercise_id = None
        self.weight = weight
        self.reps = reps
        self.rpe = rpe
        self.rest_seconds = None
        self.set_order = None

    def __str__(self):
        return f"{self.weight:g} lbs * {self.reps} reps at a RPE of {self.rpe:g}. Total volume: {self.volume():g} | Estimate 1RM: {self.estimate_1rm()} lbs"

    def volume(self):
        return self.weight * self.reps
    
    def estimate_1rm(self):
        return round(self.weight * (1 + self.reps / 30))

    def save(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO sets (
                exercise_id,
                set_order,
                reps,
                weight,
                rpe,
                rest_seconds
            )
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                self.exercise_id,
                self.set_order,
                self.reps,
                self.weight,
                self.rpe,
                self.rest_seconds
            )
        )

        self.id = cursor.lastrowid
        conn.commit()
        conn.close()
    
    

class Exercise:
    def __init__(self, library_id, notes=None):
        self.library_id = library_id
        self.workout_id = None 
        self.notes = notes
        self.sets = []
        self.id = None

    def __str__(self):
        body = "\n".join(str(s) for s in self.sets)
        return f"{self.library_id}\n{body}"

    def add_set(self, new_set):
        new_set.set_order = len(self.sets) + 1 
        self.sets.append(new_set)

    def save(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO exercises (
                workout_id,
                library_id,
                notes
            ) 
            VALUES (?, ?, ?);
            """,
            (
                self.workout_id,
                self.library_id,
                self.notes
            )
        )

        self.id = cursor.lastrowid
        conn.commit()
        conn.close()
        

    

class Workout:
    def __init__(self, date):
        self.date = date
        self.exercises = []
        self.id = None 

    def __str__(self):
        output = f"Workout: {self.date}\n"
        for exercise in self.exercises:
            output += str(exercise) + "\n"
        output += f"Total volume: {self.total_volume()}"
        return output

    def add_exercise(self, new_exercise):
        self.exercises.append(new_exercise)

    def total_volume(self):
        total = 0
        for exercise in self.exercises:
            total = 0
            for s in exercise.sets:
                total += s.volume()
        return total

    def save(self):
        """
        Insert the workout into the database and get the generated id.
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO workouts (date, is_template) VALUES (?, ?);",
            (self.date, 0) 
        )

        # tells the id it just assigned to the new row
        self.id = cursor.lastrowid

        conn.commit()
        conn.close()

        # Cascade the save
        for exercise in self.exercises:
            exercise.workout_id = self.id
            exercise.save()

            for s in exercise.sets:
                s.exercise_id = exercise.id
                s.save()

    @classmethod
    def load(cls, workout_id):
        """
        Load a workout and all its exercises and sets from the database by its id.
        Return a fully populated workout instance; Returns None if not found.
        """
        conn = get_connection()
        cursor = conn.cursor()

        # Fetches workout row
        cursor.execute(
            "SELECT id, date FROM workouts WHERE id = ?;",
            (workout_id,)
        )
        workout_row = cursor.fetchone()

        # If no row exist. Shut it down.
        if workout_row is None:
            conn.close()
            return None

        # Builds Workout instance from the row.
        # Index 0 is id, 1 is date.
        workout = cls(date=workout_row[1])
        workout.id = workout_row[0]

        # Fetches every exercise belonging to this workout
        cursor.execute(
            "SELECT id, library_id, notes FROM exercises WHERE workout_id = ?;",
            (workout_id,)
        )
        exercise_rows = cursor.fetchall()

        # For each exercise it builds an Exercise instance and load its sets
        for ex_row in exercise_rows:
            exercise = Exercise(library_id=ex_row[1], notes=ex_row[2])
            exercise.id = ex_row[0]
            exercise.workout_id = workout.id

            # Fetch this exercise's sets ordered by set_order
            cursor.execute(
                """
                SELECT id, set_order, reps, weight, rpe, rest_seconds
                FROM sets
                WHERE exercise_id = ?
                ORDER BY set_order;
                """,
                (exercise.id,)
            )
            set_rows = cursor.fetchall()

            for s_row in set_rows:
                new_set = Set(weight=s_row[3], reps=s_row[2], rpe=s_row[4])
                new_set.id = s_row[0]
                new_set.set_order = s_row[1]
                new_set.rest_seconds = s_row[5]
                new_set.exercise_id = exercise.id
                exercise.sets.append(new_set)

            workout.exercises.append(exercise)

        conn.close()
        return workout 

    
    
    

workout = Workout("2026-11-09")

bench_exercise = Exercise(library_id=49, notes="felt good today")
bench_exercise.add_set(Set(185, 8, 7))
bench_exercise.add_set(Set(185, 8, 8))
bench_exercise.add_set(Set(185, 7, 9))

workout.add_exercise(bench_exercise)

workout.save()

print(f"Saved workout {workout.id} with exercise {bench_exercise.id}")
print(f"Set ids: {[s.id for s in bench_exercise.sets]}")
print(workout)

loaded = Workout.load(4)
print("---- Loaded from DB ----")
print(loaded)
