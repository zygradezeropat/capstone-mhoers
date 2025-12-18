// Run code when the HTML document is fully loaded
document.addEventListener("DOMContentLoaded", function () {
  
  // 🔹 1. Get the canvas element where the chart will be drawn
  const reportCtx = document.getElementById("monthlyReportChart");

  // Only continue if the canvas exists in the DOM
  if (reportCtx) {
    const ctx = reportCtx.getContext("2d"); // context for drawing
    
    // 🔹 2. Initialize an empty Chart.js line chart
    const reportChart = new Chart(ctx, {
      type: "line", // chart type = line chart
      data: {
        labels: [], // initially empty (x-axis labels: months or years)
        datasets: [] // initially empty (lines for each facility/category)
      },
      options: { 
        responsive: true, // chart resizes automatically
        maintainAspectRatio: true,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        scales: {
          // X-axis configuration
          x: {
            title: {
              display: true, // show axis title
              text: "Month/Year", // label of the axis
            },
            grid: {
              display: true,
            },
          },
          // Y-axis configuration
          y: {
            beginAtZero: true, // y-axis starts from 0
            title: {
              display: true,
              text: "Number of Referred Patients", // label of the axis
            },
            grid: {
              display: true,
            },
          },
        },
        // 🔹 3. Tooltip configuration (appears when hovering over points)
        plugins: {
          tooltip: {
            callbacks: {
              // Format the tooltip label
              label: (context) => `${context.dataset.label}: ${context.parsed.y} patients`,
            },
          },
          legend: {
            display: true,
            position: 'top',
          },
        },
        elements: {
          line: {
            tension: 0.4, // Smooth curves (0 = straight lines, 1 = very curved)
            borderWidth: 2,
          },
          point: {
            radius: 4,
            hoverRadius: 6,
          },
        },
      },
    });

    // 🔹 4. Function to fetch referral data from backend API
    function fetchReferralData(viewType, startDate = null, endDate = null) {
      const currentYear = new Date().getFullYear(); // get current year
      // Build URL with parameters
      const params = new URLSearchParams();
      params.append('view_type', viewType);
      params.append('year', currentYear);
      
      // Add date filters if provided
      if (startDate && startDate.trim() !== '') {
        params.append('date_from', startDate);
      }
      if (endDate && endDate.trim() !== '') {
        params.append('date_to', endDate);
      }
      
      const url = `/analytics/api/referral-statistics/?${params.toString()}`;
      
      // Call the API
      fetch(url)
        .then(response => response.json()) // convert response into JSON
        .then(data => {
          // Replace chart labels and datasets with API data
          reportChart.data.labels = data.labels; // e.g. ["Jan", "Feb", "Mar"]
          
          // Process datasets to ensure they have line chart properties
          const processedDatasets = data.datasets.map((dataset, index) => {
            return {
              ...dataset,
              fill: false, // Don't fill area under line
              tension: 0.4, // Smooth curves
              borderWidth: 2,
              pointRadius: 4,
              pointHoverRadius: 6,
              pointBackgroundColor: dataset.borderColor || dataset.backgroundColor,
              pointBorderColor: '#fff',
              pointBorderWidth: 1,
            };
          });
          
          reportChart.data.datasets = processedDatasets;
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

    // 🔹 5. Function to apply filters with validation
    function applyStatFilters() {
      const startDateInput = document.getElementById('statStartDate');
      const endDateInput = document.getElementById('statEndDate');
      const viewFilter = document.getElementById('statViewFilter');
      
      // Reset error states
      if (startDateInput) startDateInput.classList.remove('is-invalid');
      if (endDateInput) endDateInput.classList.remove('is-invalid');
      const existingErrors = document.querySelectorAll('#tab1 .invalid-feedback');
      existingErrors.forEach(error => error.remove());
      
      // Validate date range if both dates are provided
      if (startDateInput && endDateInput && startDateInput.value && endDateInput.value) {
        const startDate = new Date(startDateInput.value);
        const endDate = new Date(endDateInput.value);
        
        if (startDate > endDate) {
          startDateInput.classList.add('is-invalid');
          endDateInput.classList.add('is-invalid');
          const errorDiv = document.createElement('div');
          errorDiv.className = 'invalid-feedback';
          errorDiv.textContent = 'START DATE cannot be greater than END DATE.';
          endDateInput.parentElement.appendChild(errorDiv);
          endDateInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
          return;
        }
      }
      
      // Fetch data with filters (default to monthly if viewFilter doesn't exist)
      const viewType = viewFilter ? viewFilter.value : 'monthly';
      fetchReferralData(
        viewType,
        startDateInput ? startDateInput.value || null : null,
        endDateInput ? endDateInput.value || null : null
      );
    }

    // 🔹 6. Debounce function to limit API calls
    let debounceTimer;
    function debounceApplyFilters() {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(applyStatFilters, 300); // Wait 300ms after last change
    }

    // 🔹 7. Load initial data when page loads
    fetchReferralData('monthly');

    // 🔹 8. Auto-apply filters when date inputs change
    const startDateInput = document.getElementById('statStartDate');
    const endDateInput = document.getElementById('statEndDate');
    
    if (startDateInput) {
      startDateInput.addEventListener('change', function() {
        debounceApplyFilters();
      });
      startDateInput.addEventListener('input', function() {
        debounceApplyFilters();
      });
    }
    
    if (endDateInput) {
      endDateInput.addEventListener('change', function() {
        debounceApplyFilters();
      });
      endDateInput.addEventListener('input', function() {
        debounceApplyFilters();
      });
    }

    // 🔹 9. Handle dropdown filter change (monthly / yearly) if it exists
    const viewFilter = document.getElementById("statViewFilter");
    if (viewFilter) {
      viewFilter.addEventListener("change", function () {
        applyStatFilters();
      });
    }
    
    // 🔹 10. Function to clear date filters
    function clearStatFilters() {
      const startDateInput = document.getElementById('statStartDate');
      const endDateInput = document.getElementById('statEndDate');
      
      if (startDateInput) {
        startDateInput.value = '';
        startDateInput.classList.remove('is-invalid');
      }
      if (endDateInput) {
        endDateInput.value = '';
        endDateInput.classList.remove('is-invalid');
      }
      
      // Remove any error messages
      const existingErrors = document.querySelectorAll('#tab1 .invalid-feedback');
      existingErrors.forEach(error => error.remove());
      
      // Reload chart with no date filters
      fetchReferralData('monthly', null, null);
    }
    
    // 🔹 11. Make functions available globally
    window.applyStatFilters = applyStatFilters;
    window.clearStatFilters = clearStatFilters;
  }
});
