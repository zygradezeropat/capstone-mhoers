document.addEventListener("DOMContentLoaded", function () {
  // Stacked Bar Chart (Referral Status Overview)
  const stackedBarangayCtx = document
    .getElementById("stackedBarangayChart")
    .getContext("2d");
  const stackedBarangayChart = new Chart(stackedBarangayCtx, {
    type: "bar",
    data: {
      labels: ["January", "February", "March", "April"],
      datasets: [
        {
          label: "Completed",
          data: [30, 14, 43, 55],
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


  // Grouped Bar Chart (Referral Completion Rate by Barangay)
  const groupedBarangayCtx = document
    .getElementById("groupedBarangayChart")
    .getContext("2d");
  const groupedBarangayChart = new Chart(groupedBarangayCtx, {
    type: "bar",
    data: {
      labels: ["2020", "2021", "2022", "2023"],
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
