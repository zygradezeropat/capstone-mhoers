document.addEventListener("DOMContentLoaded", function () {
  const ctx = document.getElementById("systemUsageLogsChart").getContext("2d");

  const systemUsageLogsChart = new Chart(ctx, {
    type: "line", // Line chart to track data over time
    data: {
      labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"], // Labels for months
      datasets: [
        {
          label: "Carcor - Logins",
          data: [30, 45, 60, 80, 70, 90], // Logins data for Carcor
          borderColor: "#4e73df",
          fill: false,
          tension: 0.1, // Smooth the line
        },
        {
          label: "Mesaoy - Logins",
          data: [25, 40, 50, 65, 60, 75], // Logins data for Mesaoy
          borderColor: "#1cc88a",
          fill: false,
          tension: 0.1,
        },
        {
          label: "New Cortez - Logins",
          data: [35, 50, 45, 70, 80, 85], // Logins data for New Cortez
          borderColor: "#36b9cc",
          fill: false,
          tension: 0.1,
        },
        {
          label: "Sta. Cruz - Logins",
          data: [40, 60, 55, 85, 90, 95], // Logins data for Sta. Cruz
          borderColor: "#f6c23e",
          fill: false,
          tension: 0.1,
        },
        {
          label: "Carcor - Reports Generated",
          data: [20, 35, 45, 55, 50, 60], // Reports generated for Carcor
          borderColor: "#ff6347", // You can use a different color for the reports
          fill: false,
          tension: 0.1,
        },
        {
          label: "Mesaoy - Reports Generated",
          data: [15, 25, 35, 45, 50, 60], // Reports generated for Mesaoy
          borderColor: "#ff4500",
          fill: false,
          tension: 0.1,
        },
        {
          label: "New Cortez - Reports Generated",
          data: [25, 40, 50, 60, 70, 80], // Reports generated for New Cortez
          borderColor: "#ff8c00",
          fill: false,
          tension: 0.1,
        },
        {
          label: "Sta. Cruz - Reports Generated",
          data: [30, 50, 60, 70, 80, 90], // Reports generated for Sta. Cruz
          borderColor: "#ffb6c1",
          fill: false,
          tension: 0.1,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: "Barangay System Usage Logs: Logins & Reports Generated",
        },
        legend: {
          position: "top",
        },
      },
      scales: {
        x: {
          title: {
            display: true,
            text: "Months",
          },
        },
        y: {
          title: {
            display: true,
            text: "Count",
          },
          beginAtZero: true,
        },
      },
    },
  });
});
