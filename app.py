from flask import Flask, jsonify, request
from database import get_connection

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"status": "ok", "message": "Workout tracker API is running."})

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

    # Inserts the new workout
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO workouts (date, is_template) VALUES (?, ?);",
        (date, is_template)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Returns the new created workout as JSON with 201 status
    return jsonify({
        "id": new_id,
        "date": date,
        "is_template": is_template
    }), 201

@app.route("/workouts/<int:workout_id>")
def get_workout(workout_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, date, is_template FROM workouts WHERE id = ?;",
        (workout_id,)
    )
    workout_row = cursor.fetchone()

    if workout_row is None:
        return jsonify({"error": "Workout not found"}), 404

    workout = {
        "id": workout_row[0],
        "date": workout_row[1],
        "is_template": workout_row[2],
        "exercises": []
    }

    cursor.execute(
        "SELECT id, library_id, notes FROM exercises WHERE workout_id = ?;",
        (workout_id,)
    )
    exercise_rows = cursor.fetchall()

    for ex_row in exercise_rows:
        exercise = {
            "id": ex_row[0],
            "library_id": ex_row[1],
            "notes": ex_row[2],
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
    