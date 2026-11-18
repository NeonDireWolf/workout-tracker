// Renders the full detailed view for a single workout
// It gets called when the user clicks a workout in the list
function renderWorkoutDetail(workout) {
    // Grab the container div where details will be rendered 
    const detail = document.getElementById("workout-detail");

    // Wipes anything previously rendered so it doesn't stack details
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

        // Delete button for the exercise
        const deleteExBtn = document.createElement("button");
        deleteExBtn.textContent = "Delete Exercise";
        deleteExBtn.className = "delete-btn";
        deleteExBtn.style.marginLeft = "10px";
        exSection.appendChild(deleteExBtn);

        deleteExBtn.addEventListener("click", () => {
            const sure = confirm(`Delete "${exercise.name}" and all its sets?`);
            if (!sure) return;

            fetch(`/exercises/${exercise.id}`, {method: "DELETE"})
                .then(response => {
                    if (response.status === 204) {
                        // Refreshes detail view
                        fetch(`/workouts/${workout.id}`)
                            .then(r => r.json())
                            .then(detail => renderWorkoutDetail(detail));
                    }
                    else {
                        console.error("Failed to delete exercise:", response.status);
                    }
                });
        });

        // Build a bulleted list of the sets for this exercise
        const setList = document.createElement("ul");
        exercise.sets.forEach(s => {
            const setLi = document.createElement("li");
            // Format each set as weight * reps @ RPE
            if (s.rpe) {
                setLi.textContent = `${s.weight} lbs x ${s.reps} reps @ RPE ${s.rpe}`;
            }
            else {
                setLi.textContent = `${s.weight} lbs x ${s.reps} reps`;
            }

            // Delete button for sets
            const deleteSetBtn = document.createElement("button");
            deleteSetBtn.textContent = "Delete";
            deleteSetBtn.className = "delete-btn";
            deleteSetBtn.style.marginLeft = "10px";
            setLi.appendChild(deleteSetBtn);

            deleteSetBtn.addEventListener("click", () => {
                const sure = confirm("Delete this set?");
                if (!sure) return;

                fetch(`/sets/${s.id}`, {method: "DELETE"})
                    .then(response => {
                        if (response.status === 204) {
                            fetch(`/workouts/${workout.id}`)
                                .then(r => r.json())
                                .then(detail => renderWorkoutDetail(detail));
                        }
                        else {
                            console.error("Failed to delete set:", response.status);
                        }
                    });
            });
            
            setList.appendChild(setLi);
        });

        // Attach the set list to the exercise section
        exSection.appendChild(setList);

        // Button to show the add set form
        const addSetButton = document.createElement("button");
        addSetButton.textContent = "Add Set";
        exSection.appendChild(addSetButton);

        // Form that's hidden until clicked
        const setForm = document.createElement("form");
        setForm.style.display = "none";

        const weightInput = document.createElement("input");
        weightInput.type = "number";
        weightInput.placeholder = "Weight (lbs)";
        weightInput.step = "0.5";
        weightInput.required = true;
        setForm.appendChild(weightInput);

        const repsInput = document.createElement("input");
        repsInput.type = "number";
        repsInput.placeholder = "Reps";
        repsInput.required = true;
        setForm.appendChild(repsInput);

        const rpeInput = document.createElement("input");
        rpeInput.type = "number";
        rpeInput.placeholder = "RPE (optional)";
        rpeInput.step = "0.5";
        rpeInput.min = "1";
        rpeInput.max = "10";
        setForm.appendChild(rpeInput);

        const setSubmit = document.createElement("button");
        setSubmit.type = "submit";
        setSubmit.textContent = "Save Set";
        setForm.appendChild(setSubmit);

        exSection.appendChild(setForm);

        // Clicking on add set reveals the form and will focus on the first input
        addSetButton.addEventListener("click", () => {
            setForm.style.display = "block";
            weightInput.focus();
        });

        // Handle the submit
        setForm.addEventListener("submit", (event) => {
            event.preventDefault();

            // Build the body and only includes RPE if the user entered 
            const body = {
                weight: parseFloat(weightInput.value),
                reps: parseInt(repsInput.value)
            };
            if (rpeInput.value) {
                body.rpe = parseFloat(rpeInput.value);
            }

            fetch(`/exercises/${exercise.id}/sets`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(body)
            })
                .then(response => response.json())
                .then(() => {
                    // Refresh to show the new set
                    fetch(`/workouts/${workout.id}`)
                        .then(r => r.json())
                        .then(detail => renderWorkoutDetail(detail));
                })
                .catch(error => console.error("Failed to log set:", error));
        });

        // Attach the whole exercise section to the detail div
        detail.appendChild(exSection);
    });

    // Build the "Add exercise" section 
    const addSection = document.createElement("div");

    const addHeader = document.createElement("h3");
    addHeader.textContent = "Add an exercise";
    addSection.appendChild(addHeader);

    // Search input for filtering the exercise library
    const searchInput = document.createElement("input");
    searchInput.type = "text";
    searchInput.placeholder = "Search exercises (e.g. bench)";
    addSection.appendChild(searchInput);

    // Empty list that will fill with matching exercises
    const resultsList = document.createElement("ul");
    addSection.appendChild(resultsList);

    // When the user types fetch matching exercises from the API
    searchInput.addEventListener("input", () => {
        const query = searchInput.value.trim();

        // Don't search for empty strings 
        if (query.length < 2) {
            resultsList.innerHTML = "";
            return;
        }

        fetch(`/exercises?search=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(matches => {
                // Clear out old results before showing the new ones
                resultsList.innerHTML = "";

                // Cap it at 10 so it's not overwhelming
                matches.slice(0, 10).forEach(ex => {
                    const li = document.createElement("li");
                    li.textContent = ex.name;
                    li.style.cursor = "pointer";

                    // When clicked POST to add this exercise to the workout
                    li.addEventListener("click", () => {
                        addExerciseToWorkout(workout.id, ex.id);
                    });

                    resultsList.appendChild(li);
                });
            });
    });

    detail.appendChild(addSection);
}

// POST to add an exercise to a workout and refresh the detail section
function addExerciseToWorkout(workoutId, libraryId) {
    fetch(`/workouts/${workoutId}/exercises`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({library_id: libraryId})
    })
        .then(response => response.json())
        .then(() => {
            // Reloads the detail view to show the new exercise 
            fetch(`/workouts/${workoutId}`)
                .then(r => r.json())
                .then(detail => renderWorkoutDetail(detail));
        })
        .catch(error => console.error("Failed to add exercise:", error));
}

// When the page is loaded, fetch the list of workouts from the API
fetch("/workouts")
    .then(response => response.json())
    .then(data => {
        const list = document.getElementById("workout-list");
        data.forEach(workout => {
            const li = document.createElement("li");

            // Name is a clickable span so it is separate from the delete button
            const nameSpan = document.createElement("span");
            const displayName = workout.name || "Untitled workout";
            nameSpan.textContent = `${workout.date} - ${displayName}`;
            nameSpan.style.cursor = "pointer";
            li.appendChild(nameSpan);

            // Delete button next to the name
            const deleteBtn = document.createElement("button");
            deleteBtn.textContent = "Delete";
            deleteBtn.className = "delete-btn";
            deleteBtn.style.marginLeft = "10px";
            li.appendChild(deleteBtn);

            // Clicking on the name loads the detail view
            nameSpan.addEventListener("click", () => {
                fetch(`/workouts/${workout.id}`)
                    .then(response => response.json())
                    .then(detail => renderWorkoutDetail(detail));
            });

            // Clicking Delete removes the workout after asking for confirmation
            deleteBtn.addEventListener("click", () => {
                const sure = confirm(`Delete "${displayName}"? This cannot be undone.`);
                if (!sure) return;

                fetch(`/workouts/${workout.id}`, {method: "DELETE"})
                    .then(response => {
                        if (response.status === 204) {
                            window.location.reload();
                        }
                        else {
                            console.error("Failed to delete:", response.status);
                        }
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

