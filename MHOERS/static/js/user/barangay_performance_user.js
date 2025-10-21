document.addEventListener("DOMContentLoaded", function () {
  // Stacked Bar Chart (Referral Status Overview)
  const stackedBarangayCtx = document
    .getElementById("stackedBarangayChart")
    .getContext("2d");
  const stackedBarangayChart = new Chart(stackedBarangayCtx, {
    type: "bar",
    data: {
      labels: [],
      datasets: []
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
      labels: [],
      datasets: []
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

  // Function to fetch barangay performance data
  function fetchBarangayPerformance() {
    const currentYear = new Date().getFullYear();
    const url = `/analytics/api/barangay-performance/?year=${currentYear}`;
    
    fetch(url)
      .then(response => response.json())
      .then(data => {
        // Update stacked bar chart (status overview)
        stackedBarangayChart.data.labels = data.status_overview.labels;
        stackedBarangayChart.data.datasets = data.status_overview.datasets;
        stackedBarangayChart.update();

        // Update grouped bar chart (completion rate)
        groupedBarangayChart.data.labels = data.completion_rate.labels;
        groupedBarangayChart.data.datasets = data.completion_rate.datasets;
        groupedBarangayChart.update();
      })
      .catch(error => {
        console.error('Error fetching barangay performance data:', error);
        // Fallback to empty data
        stackedBarangayChart.data.labels = [];
        stackedBarangayChart.data.datasets = [];
        stackedBarangayChart.update();

        groupedBarangayChart.data.labels = [];
        groupedBarangayChart.data.datasets = [];
        groupedBarangayChart.update();
      });
  }

  // Load initial data
  fetchBarangayPerformance();
});
