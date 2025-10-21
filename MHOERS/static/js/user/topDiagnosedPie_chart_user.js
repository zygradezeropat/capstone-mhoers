document.addEventListener("DOMContentLoaded", function () {
  const ctx = document.getElementById("topDiagnosedChart").getContext("2d");

  // Initialize top diagnosed chart
  const topDiagnosedChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: [],
      datasets: [
        {
          label: "Number of Diagnoses",
          data: [],
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
      indexAxis: "y",
      responsive: true,
      plugins: {
        legend: {
          display: false,
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

  // Initialize trends chart
  const ttd = document.getElementById("topTrendsDiagnosed").getContext("2d");
  const topTrendsDiagnosed = new Chart(ttd, {
    type: "line",
    data: {
      labels: [],
      datasets: []
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

  // Function to fetch disease diagnosis counts
  function fetchDiseaseCounts() {
    const currentYear = new Date().getFullYear();
    const url = `/analytics/api/disease-diagnosis-counts/?year=${currentYear}`;
    
    fetch(url)
      .then(response => response.json())
      .then(data => {
        // Update top diagnosed chart
        topDiagnosedChart.data.labels = data.labels;
        topDiagnosedChart.data.datasets[0].data = data.counts;
        topDiagnosedChart.update();
      })
      .catch(error => {
        console.error('Error fetching disease counts:', error);
      });
  }

  // Function to fetch monthly diagnosis trends
  function fetchDiagnosisTrends() {
    const currentYear = new Date().getFullYear();
    const url = `/analytics/api/monthly-diagnosis-trends/?year=${currentYear}`;
    
    fetch(url)
      .then(response => response.json())
      .then(data => {
        // Update trends chart
        topTrendsDiagnosed.data.labels = data.months.map(month => {
          const [year, monthNum] = month.split('-');
          const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
          return monthNames[parseInt(monthNum) - 1];
        });
        
        // Create datasets for each disease
        const colors = ["#4e73df", "#1cc88a", "#36b9cc", "#f6c23e", "#e74a3b"];
        topTrendsDiagnosed.data.datasets = data.diseases.slice(0, 5).map((disease, index) => ({
          label: disease,
          data: data.data[disease] || [],
          fill: false,
          borderColor: colors[index % colors.length],
          backgroundColor: colors[index % colors.length],
          tension: 0.4,
        }));
        
        topTrendsDiagnosed.update();
      })
      .catch(error => {
        console.error('Error fetching diagnosis trends:', error);
      });
  }

  // Load initial data
  fetchDiseaseCounts();
  fetchDiagnosisTrends();
});
