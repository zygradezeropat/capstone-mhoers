document.addEventListener("DOMContentLoaded", function () {
  // Stacked Bar Chart (Referral Status Overview)
  const stackedBarangayCtx = document
    .getElementById("stackedBarangayChart")
    .getContext("2d");
  const stackedBarangayChart = new Chart(stackedBarangayCtx, {
    type: "bar",
    data: {
      labels: ["Carcor", "Mesaoy", "New Cortez", "Sta. Cruz"],
      datasets: [
        {
          label: "Completed",
          data: [30, 50, 40, 60],
          backgroundColor: "#4e73df",
        },
        {
          label: "Ongoing",
          data: [20, 10, 25, 15],
          backgroundColor: "#36b9cc",
        },
        {
          label: "Cancelled",
          data: [5, 10, 3, 4],
          backgroundColor: "#e74a3b",
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        x: {
          stacked: true,
        },
        y: {
          stacked: true,
        },
      },
      plugins: {
        legend: {
          position: "top",
        },
        title: {
          display: true,
          text: "Referral Status Overview by Barangay",
        },
      },
    },
  });

  // Radar Chart (Barangay Performance Comparison)
  const radarBarangayCtx = document
    .getElementById("radarBarangayChart")
    .getContext("2d");
  const radarBarangayChart = new Chart(radarBarangayCtx, {
    type: "radar",
    data: {
      labels: [
        "Processing Speed",
        "Success Rate",
        "Referral Volume",
        "Follow-up Rate",
        "Customer Satisfaction",
      ],
      datasets: [
        {
          label: "Carcor",
          data: [4, 5, 3, 4, 5],
          backgroundColor: "rgba(78, 115, 223, 0.2)",
          borderColor: "#4e73df",
          borderWidth: 1,
        },
        {
          label: "Mesaoy",
          data: [3, 4, 4, 3, 4],
          backgroundColor: "rgba(28, 200, 138, 0.2)",
          borderColor: "#1cc88a",
          borderWidth: 1,
        },
        {
          label: "New Cortez",
          data: [5, 4, 5, 4, 4],
          backgroundColor: "rgba(54, 185, 204, 0.2)",
          borderColor: "#36b9cc",
          borderWidth: 1,
        },
        {
          label: "Sta. Cruz",
          data: [5, 3, 3, 3, 4],
          backgroundColor: "rgba(54, 185, 204, 0.2)",
          borderColor: "#36b9cc",
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      scale: {
        ticks: {
          beginAtZero: true,
        },
      },
      plugins: {
        title: {
          display: true,
          text: "Barangay Performance Comparison",
        },
      },
    },
  });

  // Grouped Bar Chart (Referral Completion Rate by Barangay)
  const groupedBarangayCtx = document
    .getElementById("groupedBarangayChart")
    .getContext("2d");
  const groupedBarangayChart = new Chart(groupedBarangayCtx, {
    type: "bar",
    data: {
      labels: ["Carcor", "Mesaoy", "New Cortez", "Sta. Cruz"],
      datasets: [
        {
          label: "Completed Referrals",
          data: [50, 60, 45, 70],
          backgroundColor: "#4e73df",
        },
        {
          label: "Ongoing Referrals",
          data: [25, 20, 30, 15],
          backgroundColor: "#36b9cc",
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        x: {
          stacked: false,
        },
        y: {
          beginAtZero: true,
        },
      },
      plugins: {
        legend: {
          position: "top",
        },
        title: {
          display: true,
          text: "Referral Completion Rate by Barangay",
        },
      },
    },
  });
});
