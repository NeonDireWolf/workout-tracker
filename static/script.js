// Renders the full detailed view for a single workout
// It gets called when the user clicks a workout in the list
function renderWorkoutDetail(workout) {
    // Grab the container div where details will be rendered 
    const detail = document.getElementById("workout-detail");

    // Wipes anything previously rendered so we don't stack details
    detail.innerHTML = "";

    // Build the workout title 
    const title = document.createElement("h2");
    title.textContent = workout.name || "Untitled workout";
    detail.appendChild(title);

    // Loop through every exercise in the workout
    workout.exercises.forEach(exercise => {
        // Create a wrapper div for this exercise and its sets 
        const exSection = document.createElement("div");

        // Exercise header (placehold using library_id for now; Will change to real name later)
        const exHeader = document.createElement("h3");
        exHeader.textContent = exercise.name;
        exSection.appendChild(exHeader);

        // Build a bulleted list of the sets for this exercise
        const setList = document.createElement("ul");
        exercise.sets.forEach(s => {
            const setLi = document.createElement("li");
            // Format each set as weight * reps @ RPE
            setLi.textContent = `${s.weight} lbs x ${s.reps} reps @ RPE ${s.rpe}`;
            setList.appendChild(setLi);
        });

        // Attach the set list to the exercise section
        exSection.appendChild(setList);

        // Attach the whole exercise section to the detail div
        detail.appendChild(exSection);
    });
}

// When the page is loaded, fetch the list of workouts from the API
fetch("/workouts")
    .then(response => response.json())
    .then(data => {
        const list = document.getElementById("workout-list");
        data.forEach(workout => {
            const li = document.createElement("li");
            const displayName = workout.name || "Untitled workout";
            li.textContent = `${workout.date} - ${displayName}`;
            li.addEventListener("click", () => {
                fetch(`/workouts/${workout.id}`)
                .then(response => response.json())
                .then(detail => {
                    renderWorkoutDetail(detail);
                });
            });
            list.appendChild(li);
        });
        document.getElementById("status").textContent = `${data.length} workouts logged.`;
    })
    .catch(error => {
        const status = document.getElementById("status");
        status.textContent = "Failed to load workouts.";
        console.error(error);
    });

// Grab the form element and attach a submit handler
const form = document.getElementById("new-workout-form");

form.addEventListener("submit", (event) => {
    // Stop the browser's default form submission (it would reload the page)
    event.preventDefault();

    // Pull the current values from the form's fields
    // FormData for reading form values
    const formData = new FormData(form);
    const name = formData.get("name");
    const date = formData.get("date");

    // Build the request body as a plain object
    const body = {
        name: name,
        date: date
    };

    // POST to the API
    fetch("/workouts", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body)
    })
        .then(response => response.json())
        .then(newWorkout => {
            console.log("Created:", newWorkout);
            // Reset the form so the fields are empty
            form.reset();
            // Reload the page to show the new workout
            // TODO: Will update later to list without reload
            window.location.reload();
        })
        .catch(error => {
            console.error("Failed to create workout:", error);
        });
});

