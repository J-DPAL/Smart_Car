let chart;

function loadHistory() {
    const date = document.getElementById("datePick").value;
    const messageDiv = document.getElementById("chartMessage");
    
    if (!date) {
        messageDiv.textContent = "Please select a date.";
        messageDiv.style.color = "#ff6b6b";
        return;
    }
    
    messageDiv.textContent = "Loading historical data...";
    messageDiv.style.color = "#4a90e2";
    
    fetch(`/api/history?date=${date}`)
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                messageDiv.textContent = `Error: ${data.error}`;
                messageDiv.style.color = "#ff6b6b";
                return;
            }
            
            if (!data.timestamps || data.timestamps.length === 0) {
                messageDiv.textContent = `No data found for ${date}. Try another date.`;
                messageDiv.style.color = "#f39c12";
                if (chart) {
                    chart.destroy();
                    chart = null;
                }
                return;
            }
            
            messageDiv.textContent = `Showing ${data.timestamps.length} data points for ${date}`;
            messageDiv.style.color = "#27ae60";
            
            // Destroy previous chart if exists
            if (chart) chart.destroy();
            
            const ctx = document.getElementById("chart").getContext("2d");

            chart = new Chart(ctx, {
                type: "line",
                data: {
                    labels: data.timestamps.map(ts => {
                        // Format timestamps to show only time (HH:MM:SS)
                        const d = new Date(ts);
                        return d.toLocaleTimeString();
                    }),
                    datasets: [
                        {
                            label: "IR Sensor",
                            data: data.ir,
                            borderColor: "#e74c3c",
                            backgroundColor: "rgba(231, 76, 60, 0.1)",
                            tension: 0.3
                        },
                        {
                            label: "Ultrasonic (cm)",
                            data: data.ultrasonic,
                            borderColor: "#3498db",
                            backgroundColor: "rgba(52, 152, 219, 0.1)",
                            tension: 0.3
                        },
                        {
                            label: "Speed",
                            data: data.speed,
                            borderColor: "#2ecc71",
                            backgroundColor: "rgba(46, 204, 113, 0.1)",
                            tension: 0.3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        title: {
                            display: true,
                            text: `Sensor Data for ${date}`
                        },
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Sensor Values'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Time'
                            },
                            ticks: {
                                maxTicksLimit: 10  // Limit x-axis labels for readability
                            }
                        }
                    }
                }
            });
        })
        .catch(err => {
            console.error("Chart loading error:", err);
            messageDiv.textContent = "Failed to load historical data. Check console for details.";
            messageDiv.style.color = "#ff6b6b";
        });
}
