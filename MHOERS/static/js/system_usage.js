let systemUsageLogsChart = null;

function loadSystemUsageData(year = null) {
  // Get year from filter or use current year
  if (!year) {
    const yearFilter = document.getElementById('systemUsageYearFilter');
    year = yearFilter ? yearFilter.value : new Date().getFullYear();
  }
  
  // Fetch data from API
  fetch(`/analytics/api/system-usage/?year=${year}`)
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log('System Usage Data loaded:', data);
      updateSystemUsageChart(data);
    })
    .catch(error => {
      console.error('Error loading system usage data:', error);
      alert('Failed to load system usage data. Please check the console for details.');
    });
}

function updateSystemUsageChart(data) {
  const ctx = document.getElementById("systemUsageLogsChart");
  if (!ctx) return;
  
  // Destroy existing chart if it exists
  if (systemUsageLogsChart) {
    systemUsageLogsChart.destroy();
  }
  
  // Create new chart with real data
  systemUsageLogsChart = new Chart(ctx.getContext("2d"), {
    type: "line",
    data: {
      labels: data.labels || ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
      datasets: data.datasets || [],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
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
}

document.addEventListener("DOMContentLoaded", function () {
  // Load initial data
  loadSystemUsageData();
  
  // Handle year filter change
  const systemUsageYearFilter = document.getElementById('systemUsageYearFilter');
  if (systemUsageYearFilter) {
    systemUsageYearFilter.addEventListener('change', function() {
      loadSystemUsageData(this.value);
    });
  }
  
  // Load data when System Usage tab is shown
  const systemUsageTab = document.getElementById('tab4-tab');
  if (systemUsageTab) {
    systemUsageTab.addEventListener('shown.bs.tab', function() {
      // Reload data when tab is shown to ensure chart is visible
      if (!systemUsageLogsChart) {
        loadSystemUsageData();
      }
    });
  }
});
