document.addEventListener("DOMContentLoaded", function () {
  // Horizontal Bar Chart: Total Patients per BHC Facility
  const barCanvas = document.getElementById("barChart");
  if (barCanvas) {
    const barCtx = barCanvas.getContext("2d");
    new Chart(barCtx, {
      type: "bar",
      data: {
        labels: ["Carcor", "Mesaoy", "New Corella", "Sta. Cruz"],
        datasets: [
          {
            label: "Total Patients",
            data: [64, 50, 33, 22],
            backgroundColor: ["#5c3dff", "#ff918e", "#ff57d1", "#ffb457"],
            borderRadius: 10,
            barThickness: 20,
          },
        ],
      },
      options: {
        indexAxis: "y",
        scales: {
          x: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Number of Referred Patients from BHC",
            },
            ticks: {
              callback: (value) => `${value}`,
            },
          },
          y: {
            beginAtZero: true,
          },
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => `${context.parsed.x} patients`,
            },
          },
        },
      },
    });
  }

  // Line Chart: Referrals per Account/Facility with Monthly/Yearly Filter
const lineCtx = document.getElementById("referralsPerUserChart");
if (lineCtx) {
  let referralsChart;

  function loadAndRenderReferralsChart(viewType) {
    const baseUrl = viewType === 'yearly' 
      ? '/referral/api/yearly-referral-counts-by-user/' 
      : '/referral/api/monthly-referral-counts-by-user/';
      
    const params = new URLSearchParams();
    if (viewType === 'monthly') {
      const yearNow = new Date().getFullYear();
      params.set('year', yearNow);
    }
    
    fetch(`${baseUrl}?${params.toString()}`)
      .then(response => response.json())
      .then(result => {
        if (referralsChart) {
          referralsChart.destroy();
        }

        const chartConfig = {
          type: "line",   // 🔹 Changed from "bar" to "line"
          data: {
            labels: result.labels,
            datasets: result.datasets.map(ds => ({
              ...ds,
              fill: false,          // no area under line
              tension: 0.3,         // smooth curves
              borderWidth: 2,       // thicker lines
              pointRadius: 4,       // circle points
              pointHoverRadius: 6   // bigger when hovered
            }))
          },
          options: {
            responsive: true,
            plugins: {
              title: { 
                display: true, 
                text: `Referrals per Account/Facility (${viewType === 'yearly' ? 'Yearly' : 'Monthly'} View)` 
              },
              legend: { 
                display: true, 
                position: "bottom",
                labels: {
                  usePointStyle: true,
                  padding: 20
                }
              },
            },
            scales: {
              x: {
                title: {
                  display: true,
                  text: viewType === 'yearly' ? "Year" : "Month",
                },
              },
              y: {
                beginAtZero: true,
                title: {
                  display: true,
                  text: "Number of Referrals",
                },
              },
            },
            interaction: {
              intersect: false,
              mode: 'index'
            }
          },
        };

        referralsChart = new Chart(lineCtx, chartConfig);

        // Update legend summary with totals per account
        const legendEl = document.getElementById('referralsPerUserLegend');
        if (legendEl && result.datasets) {
          const totals = result.datasets.map(ds => {
            const total = ds.data.reduce((sum, val) => sum + val, 0);
            return `${ds.label}: ${total}`;
          });
          legendEl.innerHTML = totals.join(' · ') || 'No referral data available.';
        }
      })
      .catch(error => {
        console.error("Error fetching referral counts by user:", error);
      });
  }

  // Load initial chart with monthly view
  loadAndRenderReferralsChart('monthly');

  // Handle view filter change
  const viewFilter = document.getElementById('reportViewFilter');
  if (viewFilter) {
    viewFilter.addEventListener('change', function() {
      loadAndRenderReferralsChart(this.value);
    });
  }
}

  // Monthly and Yearly Report per Barangay (Stacked Bar with Filter)
  const reportCtx = document.getElementById("monthlyReportChart");
  if (reportCtx) {
    const ctx = reportCtx.getContext("2d");
    let reportChart;

    function fetchAndRender(view) {
      const params = new URLSearchParams();
      const endpoint = `/analytics/api/monthly-diagnosis-trends/?${params.toString()}`;
      fetch(endpoint)
        .then((r) => r.json())
        .then((data) => {
          const months = data.months;
          const datasets = Object.keys(data.data).map((disease, idx) => {
            const baseColors = ["#5c3dff", "#ff918e", "#ff57d1", "#ffb457", "#28a745", "#17a2b8", "#6f42c1", "#20c997", "#ffc107", "#dc3545"];
            const color = baseColors[idx % baseColors.length];
            return {
              label: disease,
              data: data.data[disease],
              backgroundColor: color,
              borderColor: color,
              borderWidth: 1,
            };
          });

          const cfg = {
            type: "bar",
            data: { labels: months, datasets },
            options: {
              responsive: true,
              scales: {
                x: { stacked: true, title: { display: true, text: "Month" } },
                y: { stacked: true, beginAtZero: true, title: { display: true, text: "Diagnoses" } },
              },
              plugins: {
                legend: { display: true, position: "bottom" },
                title: { display: true, text: "Monthly Diagnosis Trends by Disease" },
                tooltip: {
                  callbacks: {
                    footer: (items) => {
                      // Sum stack at this index for quick total
                      const idx = items[0].dataIndex;
                      const total = items[0].chart.data.datasets.reduce((sum, ds) => sum + (ds.data[idx] || 0), 0);
                      return `Total: ${total}`;
                    }
                  }
                }
              },
            },
          };

          if (reportChart) {
            reportChart.destroy();
          }
          reportChart = new Chart(ctx, cfg);
        })
        .catch((e) => console.error("Failed to load diagnosis trends", e));
    }

    fetchAndRender("monthly");
    const filter = document.getElementById("reportViewFilter");
    if (filter) {
      filter.addEventListener("change", function () {
        fetchAndRender(this.value);
      });
    }

    // Add per-user legend counts panel
    const container = reportCtx.parentElement;
    const legendDiv = document.createElement('div');
    legendDiv.id = 'perUserLegend';
    legendDiv.style.marginTop = '12px';
    container.appendChild(legendDiv);

    function loadPerUserLegend() {
      fetch('/analytics/api/disease-counts-per-user/')
        .then(r => r.json())
        .then(json => {
          const { users, diseases, matrix } = json;
          // Build a compact legend summary per user for all diseases
          let html = '';
          users.forEach((user, r) => {
            const total = matrix[r].reduce((a, b) => a + b, 0);
            const top = matrix[r]
              .map((v, i) => ({ disease: diseases[i], v }))
              .filter(x => x.v > 0)
              .sort((a, b) => b.v - a.v)
              .slice(0, 3)
              .map(x => `${x.disease}: ${x.v}`)
              .join(', ');
            html += `<div><strong>${user}</strong>: ${total} total${top ? ` — ${top}` : ''}</div>`;
          });
          legendDiv.innerHTML = html || '<div>No data</div>';
        })
        .catch(e => console.error('Failed to load per-user legend', e));
    }

    loadPerUserLegend();
  }

  // Render diagnoses per user stacked bar chart
  const perUserCanvas = document.getElementById('diagnosesPerUserChart');
  if (perUserCanvas) {
    const ctx2 = perUserCanvas.getContext('2d');
    fetch('/analytics/api/disease-counts-per-user/')
      .then(r => r.json())
      .then(json => {
        const { users, diseases, matrix } = json;
        const baseColors = ["#5c3dff", "#ff918e", "#ff57d1", "#ffb457", "#28a745", "#17a2b8", "#6f42c1", "#20c997", "#ffc107", "#dc3545"];
        const datasets = diseases.map((disease, i) => ({
          label: disease,
          data: matrix.map(row => row[i]),
          backgroundColor: baseColors[i % baseColors.length],
          borderColor: baseColors[i % baseColors.length],
          borderWidth: 1,
        }));
        new Chart(ctx2, {
          type: 'bar',
          data: { labels: users, datasets },
          options: {
            responsive: true,
            scales: {
              x: { stacked: true, title: { display: true, text: 'User' } },
              y: { stacked: true, beginAtZero: true, title: { display: true, text: 'Diagnoses' } },
            },
            plugins: {
              legend: { display: true, position: 'bottom' },
              title: { display: true, text: 'Diagnoses by User (stacked by disease)' },
            },
          },
        });
      })
      .catch(e => console.error('Failed to render diagnoses per user', e));
  }


 //PIE CHART FOR TOP DIAGNOSIS
 



});
