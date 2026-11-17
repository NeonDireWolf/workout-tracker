import sqlite3
import json 

DB_FILENAME = "workouts.db"

def get_connection():
    """
    Open a connection to the SQLite database file. All opertions need a connection.
    """
    # Opens the file if it exist, if not creates it
    conn = sqlite3.connect(DB_FILENAME)
    # Tell SQLite to enforce foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def create_tables():
    """
    Create all four tables if they don't exist
    It's safe to run multiple times; The IF NOT EXISTS skips them if present.
    """
    conn = get_connection()
    cursor = conn.cursor() # what you use to run SQL statements

    # exercise_library: master catalog of lifts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercise_library (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            force TEXT,
            level TEXT,
            mechanic TEXT,
            equipment TEXT,
            primary_muscles TEXT,
            secondary_muscles TEXT,
            category TEXT,
            instructions TEXT
        );
    """)

    # workouts block
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            date TEXT,
            is_template INTEGER DEFAULT 0
        );
    """)

    # exercises block
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_id INTEGER NOT NULL,
            library_id INTEGER NOT NULL,
            notes TEXT,
            FOREIGN KEY (workout_id) REFERENCES workouts(id),
            FOREIGN KEY (library_id) REFERENCES exercise_library(id)
        );
    """)

    # sets block
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise_id INTEGER NOT NULL,
            set_order INTEGER,
            reps INTEGER,
            weight REAL,
            rpe REAL,
            rest_seconds INTEGER,
            FOREIGN KEY (exercise_id) REFERENCES exercises(id)
        );
    """)

    conn.commit() # save the changes to the file
    conn.close() # always close connections when done

def seed_library():
    """
    Read exercises.json and insert each exercise as a row in exercise_library.
    Safe to run only once, running twice will create dupes 
    """
    # Open the JSON file in read mode and parse it into a Python list of dicts
    with open("exercises.json", "r") as f:
        data = json.load(f)

    conn = get_connection()
    cursor = conn.cursor()

    # Loop through every exercise entry in the JSON
    for exercise in data:
        # Pull each field out of dict
        # .get() returns None if the key is missing
        name = exercise.get("name")
        force = exercise.get("force")
        level = exercise.get("level")
        mechanic = exercise.get("mechanic")
        equipment = exercise.get("equipment")
        category = exercise.get("category")

        # List in the JSON. Covert to JSON strings for storage
        primary_muscles = json.dumps(exercise.get("primaryMuscles", []))
        secondary_muscles = json.dumps(exercise.get("secondaryMuscles", []))
        instructions = json.dumps(exercise.get("instructions", []))

        # Insert the row. Using ? placeholders prevents SQL injections
        cursor.execute(
            """
            INSERT INTO exercise_library
                (name, force, level, mechanic, equipment,
                primary_muscles, secondary_muscles, category, instructions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (name, force, level, mechanic, equipment, primary_muscles, secondary_muscles, category, instructions)
        )

    conn.commit()
    conn.close()
    print(f"Seeded {len(data)} exercises into exercise_library.")

def find_exercise_by_name(name):
    """
    Look up an exercise in the library by the exact name.
    Will return the row as a tuple or None if not found.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM exercise_library WHERE name = ?;",
        (name,)
    )

    result = cursor.fetchone()
    conn.close()
    return result

# Only runs when the file is executed directly, not when it's imported from another file
if __name__ == "__main__":
    create_tables()
    # seed_library()
    print("Done.")
    