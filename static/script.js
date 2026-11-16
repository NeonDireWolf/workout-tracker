// When the page is loaded, fetch the list of workouts from the API
fetch("/workouts")
    .then(response => response.json())
    .then(data => {
        const list = document.getElementById("workout-list");
        data.forEach(workout => {
            const li = document.createElement("li");
            li.textContent = `${workout.date} - Workout #${workout.id}`;
            list.appendChild(li);
        });
        document.getElementById("status").textContent = `${data.length} workouts logged.`;
    })
    .catch(error => {
        const status = document.getElementById("status");
        status.textContent = "Failed to load workouts.";
        console.error(error);
    });