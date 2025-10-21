// Run code when the HTML document is fully loaded
document.addEventListener("DOMContentLoaded", function () {
  
  // 🔹 1. Get the canvas element where the chart will be drawn
  const reportCtx = document.getElementById("monthlyReportChart");

  // Only continue if the canvas exists in the DOM
  if (reportCtx) {
    const ctx = reportCtx.getContext("2d"); // context for drawing
    
    // 🔹 2. Initialize an empty Chart.js bar chart
    const reportChart = new Chart(ctx, {
      type: "bar", // chart type = bar chart
      data: {
        labels: [], // initially empty (x-axis labels: months or years)
        datasets: [] // initially empty (bars grouped per barangay or category)
      },
      options: { 
        indexAxis: "x", // bars grow horizontally across the X axis
        responsive: true, // chart resizes automatically
        scales: {
          // X-axis configuration
          x: {
            beginAtZero: true, // x-axis starts from 0
            title: {
              display: true, // show axis title
              text: "Month/Year", // label of the axis
            },
          },
          // Y-axis configuration
          y: {
            beginAtZero: true, // y-axis starts from 0
            title: {
              display: true,
              text: "Number of Referred Patients", // label of the axis
            },
          },
        },
        // 🔹 3. Tooltip configuration (appears when hovering over bars)
        plugins: {
          tooltip: {
            callbacks: {
              // Format the tooltip label
              label: (context) => `${context.parsed.y} patients`,
            },
          },
        },
      },
    });

    // 🔹 4. Function to fetch referral data from backend API
    function fetchReferralData(viewType) {
      const currentYear = new Date().getFullYear(); // get current year
      // Example API endpoint: /analytics/api/referral-statistics/?view_type=monthly&year=2025
      const url = `/analytics/api/referral-statistics/?view_type=${viewType}&year=${currentYear}`;
      
      // Call the API
      fetch(url)
        .then(response => response.json()) // convert response into JSON
        .then(data => {
          // Replace chart labels and datasets with API data
          reportChart.data.labels = data.labels; // e.g. ["Jan", "Feb", "Mar"]
          reportChart.data.datasets = data.datasets; // e.g. [{label:"Barangay A", data:[5,8,12]}, ...]
          reportChart.update(); // redraw the chart with new data
        })
        .catch(error => {
          // If API call fails, log the error and show empty chart
          console.error('Error fetching referral data:', error);
          reportChart.data.labels = [];
          reportChart.data.datasets = [];
          reportChart.update();
        });
    }

    // 🔹 5. Load initial data when page loads
    fetchReferralData('monthly');

    // 🔹 6. Handle dropdown filter change (monthly / yearly)
    document
      .getElementById("reportViewFilter") // get the filter dropdown
      .addEventListener("change", function () {
        const selected = this.value; // get the selected option
        fetchReferralData(selected); // fetch new data based on selection
      });
  }
});
