from flask import Flask, jsonify, request, render_template
from database import get_connection

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/exercises")
def list_exercises():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, category, equipment FROM exercise_library;")
    rows = cursor.fetchall()

    conn.close()

    # Converts each row into a dict for JSON output
    exercises = []
    for row in rows:
        exercises.append({
            "id": row[0],
            "name": row[1],
            "category": row[2],
            "equipment": row[3]
        })

    return jsonify(exercises)

@app.route("/exercises/<int:exercise_id>")
def get_exercise(exercise_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM exercise_library WHERE id = ?;",
        (exercise_id,)
    )
    row = cursor.fetchone()
    conn.close()

    # If no exercise with that id exists, return 404
    if row is None:
        return jsonify({"error": "Exercise not found"}), 404

    # Dict with all the fields
    exercise = {
        "id": row[0],
        "name": row[1],
        "force": row[2],
        "level": row[3],
        "mechanic": row[4],
        "equipment": row[5],
        "primary_muscles": row[6],
        "secondary_muscles": row[7],
        "category": row[8],
        "instructions": row[9]
    }

    return jsonify(exercise)

@app.route("/workouts", methods=["POST"])
def create_workout():
    # Parse the JSON body sent by the client
    data = request.get_json()

    # Validation to make sure the required field is present
    if not data or "date" not in data:
        return jsonify({"error": "Missing required field: date"}), 400

    date = data["date"]
    is_template = data.get("is_template", 0)
    name = data.get("name")

    # Inserts the new workout
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO workouts (date, is_template, name) VALUES (?, ?, ?);",
        (date, is_template, name)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Returns the new created workout as JSON with 201 status
    return jsonify({
        "id": new_id,
        "date": date,
        "is_template": is_template,
        "name": name
    }), 201

@app.route("/workouts/<int:workout_id>")
def get_workout(workout_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, name, date, is_template FROM workouts WHERE id = ?;",
        (workout_id,)
    )
    workout_row = cursor.fetchone()

    if workout_row is None:
        return jsonify({"error": "Workout not found"}), 404

    workout = {
        "id": workout_row[0],
        "name": workout_row[1],
        "date": workout_row[2],
        "is_template": workout_row[3],
        "exercises": []
    }

    cursor.execute(
        """
        SELECT
            exercises.id,
            exercises.library_id,
            exercises.notes,
            exercise_library.name
        FROM exercises
        JOIN exercise_library ON exercises.library_id = exercise_library.id
        WHERE exercises.workout_id = ?;
        """,
        (workout_id,)
    )
    exercise_rows = cursor.fetchall()

    for ex_row in exercise_rows:
        exercise = {
            "id": ex_row[0],
            "library_id": ex_row[1],
            "notes": ex_row[2],
            "name": ex_row[3],
            "sets": []
        }

        cursor.execute(
            """
            SELECT id, set_order, reps, weight, rpe, rest_seconds
            FROM sets
            WHERE exercise_id = ?
            ORDER BY set_order;
            """,
            (exercise["id"],)
        )
        set_rows = cursor.fetchall()

        for s_row in set_rows:
            exercise["sets"].append({
                "id": s_row[0],
                "set_order": s_row[1],
                "reps": s_row[2],
                "weight": s_row[3],
                "rpe": s_row[4],
                "rest_seconds": s_row[5]
            })

        workout["exercises"].append(exercise)

    conn.close()
    return jsonify(workout)


@app.route("/workouts/<int:workout_id>/exercises", methods=["POST"])
def add_exercise(workout_id):
    data = request.get_json()

    library_id = data.get("library_id") if data else None
    notes = data.get("notes") if data else None

    if library_id is None:
        return jsonify({"error": "Missing library_id"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO exercises (workout_id, library_id, notes) VALUES (?, ?, ?);",
        (workout_id, library_id, notes)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "id": new_id,
        "workout_id": workout_id,
        "library_id": library_id,
        "notes": notes
    }), 201 

@app.route("/exercises/<int:exercise_id>/sets", methods=["POST"])
def add_set(exercise_id):
    data = request.get_json()

    reps = data.get("reps") if data else None
    weight = data.get("weight") if data else None
    rpe = data.get("rpe") if data else None
    rest_seconds = data.get("rest_seconds") if data else None 

    if reps is None or weight is None or rpe is None:
        return jsonify({"error": "Missing required fields: reps, weight, and rpe are required."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM sets WHERE exercise_id = ?;",
        (exercise_id,)
    )
    count_row = cursor.fetchone()

    existing_count = count_row[0]
    set_order = existing_count + 1

    cursor.execute(
        "INSERT INTO sets (exercise_id, reps, weight, rpe, rest_seconds, set_order) VALUES (?, ?, ?, ?, ?, ?);",
        (exercise_id, reps, weight, rpe, rest_seconds, set_order)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "id": new_id,
        "exercise_id": exercise_id,
        "reps": reps,
        "weight": weight,
        "rpe": rpe,
        "rest_seconds": rest_seconds,
        "set_order": set_order
    }), 201

@app.route("/workouts")
def get_workouts():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, date, is_template FROM workouts ORDER BY date DESC;")
    rows = cursor.fetchall()

    conn.close()

    workouts = []
    for row in rows:
        workouts.append({
            "id": row[0],
            "name": row[1],
            "date": row[2],
            "is_template": row[3]
        })

    return jsonify(workouts) 

@app.route("/sets/<int:set_id>", methods=["DELETE"])
def delete_set(set_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM sets WHERE id=?;", (set_id,))

    if cursor.fetchone() is None:
        conn.close()
        return jsonify({"error": "Set not found"}), 404

    cursor.execute("DELETE FROM sets WHERE id=?;", (set_id,))

    conn.commit()
    conn.close()

    return "", 204

@app.route("/exercises/<int:exercise_id>", methods=["DELETE"])
def delete_exercise(exercise_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM exercises WHERE id=?;", (exercise_id,))

    if cursor.fetchone() is None:
        conn.close()
        return jsonify({"error": "Exercise not found"}), 404

    cursor.execute("DELETE FROM sets WHERE exercise_id = ?;", (exercise_id,))
    cursor.execute("DELETE FROM exercises WHERE id = ?;", (exercise_id,))

    conn.commit()
    conn.close()

    return "", 204

@app.route("/workouts/<int:workout_id>", methods=["DELETE"])
def delete_workout(workout_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM workouts WHERE id=?;", (workout_id,))

    if cursor.fetchone() is None:
        conn.close()
        return jsonify({"error": "Workout not found"}), 404

    cursor.execute("""
        DELETE FROM sets 
        WHERE exercise_id IN (
            SELECT id FROM exercises WHERE workout_id = ?
        );
    """, (workout_id,))
    cursor.execute("DELETE FROM exercises WHERE workout_id = ?;", (workout_id,))
    cursor.execute("DELETE FROM workouts WHERE id = ?;", (workout_id,))

    conn.commit()
    conn.close()

    return "", 204