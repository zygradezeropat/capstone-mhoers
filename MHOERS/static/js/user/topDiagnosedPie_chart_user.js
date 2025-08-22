document.addEventListener("DOMContentLoaded", function () {
  const ctx = document.getElementById("topDiagnosedChart").getContext("2d");

  const topDiagnosedChart = new Chart(ctx, {
    type: "bar", // Change 'pie' to 'bar'
    data: {
      labels: ["Hypertension", "Diabetes", "Flu", "Malaria", "Asthma"],
      datasets: [
        {
          label: "Number of Diagnoses",
          data: [45, 32, 28, 19, 12],
          backgroundColor: [
            "#4e73df",
            "#1cc88a",
            "#36b9cc",
            "#f6c23e",
            "#e74a3b",
          ],
          borderWidth: 1,
        },
      ],
    },
    options: {
      indexAxis: "y", // This makes it horizontal
      responsive: true,
      plugins: {
        legend: {
          display: false, // Usually bar charts don't need legends
        },
        title: {
          display: true,
          text: "Most Common Diagnoses",
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const label = context.label || "";
              const value = context.raw || context.parsed;
              return `${label}: ${value} cases`;
            },
          },
        },
      },
      scales: {
        x: {
          beginAtZero: true,
        },
      },
    },
  });

  // trends diagnosed months
  const ttd = document.getElementById("topTrendsDiagnosed").getContext("2d");

  const topTrendsDiagnosed = new Chart(ttd, {
    type: "line", // LINE chart
    data: {
      labels: ["January", "February", "March", "April", "May", "June"], // X-axis (Time)
      datasets: [
        {
          label: "Hypertension Cases",
          data: [12, 19, 15, 20, 18, 22],
          fill: false,
          borderColor: "#4e73df",
          backgroundColor: "#4e73df",
          tension: 0.4, // smooth curves
        },
        {
          label: "Diabetes Cases",
          data: [8, 11, 13, 9, 14, 17],
          fill: false,
          borderColor: "#1cc88a",
          backgroundColor: "#1cc88a",
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      animation: {
        duration: 1500,
        easing: "easeInOutQuart",
      },
      plugins: {
        title: {
          display: true,
          text: "Diagnosis Trends Over Time",
          font: {
            size: 18,
          },
        },
        tooltip: {
          mode: "index",
          intersect: false,
        },
        legend: {
          position: "top",
        },
      },
      interaction: {
        mode: "nearest",
        axis: "x",
        intersect: false,
      },
      scales: {
        x: {
          title: {
            display: true,
            text: "Months",
          },
        },
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "Number of Cases",
          },
        },
      },
    },
  });
});
