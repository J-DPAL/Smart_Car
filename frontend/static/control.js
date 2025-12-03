console.log("Control JS loaded.");

// ----- DARK MODE -----
document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("theme-toggle");

    if (!toggle) return;

    toggle.addEventListener("click", () => {
        document.body.classList.toggle("dark");
        localStorage.setItem(
            "theme",
            document.body.classList.contains("dark") ? "dark" : "light"
        );
    });

    // Load saved preference
    if (localStorage.getItem("theme") === "dark") {
        document.body.classList.add("dark");
    }
});

// ----- CONTROL BUTTONS -----
function sendControl(command) {
    fetch(`/api/control/${command}`, { method: "POST" })
        .then(response => response.json())
        .then(data => console.log("Control response:", data))
        .catch(err => console.error(err));
}
