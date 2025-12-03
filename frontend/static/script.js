// ==========================================
// DARK MODE
// ==========================================
const toggle = document.getElementById("theme-toggle");

toggle.addEventListener("click", () => {
    document.body.classList.toggle("dark");

    localStorage.setItem(
        "theme",
        document.body.classList.contains("dark") ? "dark" : "light"
    );
});

// Load saved theme
window.onload = () => {
    const saved = localStorage.getItem("theme");
    if (saved === "dark") {
        document.body.classList.add("dark");
    }
};

// ==========================================
// SEND COMMANDS TO FLASK API
// ==========================================
function sendControl(value) {
    fetch("/api/control", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({device: "motor", value})
    });
}
