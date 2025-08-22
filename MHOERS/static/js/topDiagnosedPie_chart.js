document.addEventListener("DOMContentLoaded", function () {
  const ctx = document.getElementById("topDiagnosedChart").getContext("2d");

  // Populate year filter (last 5 years)
  const yearSelect = document.getElementById("diagnosisYearFilter");
  if (yearSelect) {
    const currentYear = new Date().getFullYear();
    for (let y = currentYear; y >= currentYear - 4; y--) {
      const opt = document.createElement("option");
      opt.value = y;
      opt.textContent = y;
      yearSelect.appendChild(opt);
    }
    yearSelect.value = currentYear;
  }
  const monthSelect = document.getElementById("diagnosisMonthFilter");

  let diagnosisChart = null;
  let trendsChart = null;

  function getSelectedYear() {
    return yearSelect ? yearSelect.value : new Date().getFullYear();
  }
  function getSelectedMonth() {
    return monthSelect ? monthSelect.value : "";
  }

  function loadDiagnosisChart() {
    const year = getSelectedYear();
    const month = getSelectedMonth();
    let url = `/patients/api/disease-diagnosis-counts/?year=${year}`;
    if (month) url += `&month=${month}`;
    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        const labels = data.labels;
        const counts = data.counts;
        const backgroundColors = [
          "#4e73df",
          "#1cc88a",
          "#36b9cc",
          "#f6c23e",
          "#e74a3b",
          "#858796",
        ];
        const barColors = labels.map((_, i) => backgroundColors[i % backgroundColors.length]);
        if (diagnosisChart) diagnosisChart.destroy();
        diagnosisChart = new Chart(ctx, {
          type: "bar",
          data: {
            labels: labels,
            datasets: [
              {
                label: "Number of Diagnoses",
                data: counts,
                backgroundColor: barColors,
                borderColor: barColors,
                borderWidth: 1,
              },
            ],
          },
          options: {
            responsive: true,
            plugins: {
              legend: { display: false },
              title: { display: true, text: "Most Common Diagnoses" },
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
              x: { title: { display: true, text: "Disease" } },
              y: { beginAtZero: true, title: { display: true, text: "Number of Cases" } },
            },
          },
        });
      });
  }

  function loadTrendsChart() {
    const ttd = document.getElementById("topTrendsDiagnosed").getContext("2d");
    const year = getSelectedYear();
    const month = getSelectedMonth();
    let url = `/analytics/api/monthly-diagnosis-trends/?year=${year}`;
    if (month) url += `&month=${month}`;
    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        const months = data.months;
        const diseases = data.diseases;
        const trends = data.data;
        const lineColors = [
          "#4e73df",
          "#1cc88a",
          "#36b9cc",
          "#f6c23e",
          "#e74a3b",
          "#858796",
          "#8e44ad",
          "#16a085",
          "#d35400",
          "#2c3e50"
        ];
        const datasets = diseases.map((disease, i) => ({
          label: disease,
          data: trends[disease],
          fill: false,
          borderColor: lineColors[i % lineColors.length],
          backgroundColor: lineColors[i % lineColors.length],
          tension: 0.4,
        }));
        if (trendsChart) trendsChart.destroy();
        trendsChart = new Chart(ttd, {
          type: "line",
          data: {
            labels: months,
            datasets: datasets,
          },
          options: {
            responsive: true,
            animation: { duration: 1500, easing: "easeInOutQuart" },
            plugins: {
              title: { display: true, text: "Diagnosis Trends Over Time (Monthly)", font: { size: 18 } },
              tooltip: { mode: "index", intersect: false },
              legend: { position: "top" },
            },
            interaction: { mode: "nearest", axis: "x", intersect: false },
            scales: {
              x: { title: { display: true, text: "Month" } },
              y: { beginAtZero: true, title: { display: true, text: "Number of Cases" } },
            },
          },
        });
      });
  }

  if (yearSelect && monthSelect) {
    yearSelect.addEventListener("change", function () {
      loadDiagnosisChart();
      loadTrendsChart();
    });
    monthSelect.addEventListener("change", function () {
      loadDiagnosisChart();
      loadTrendsChart();
    });
  }

  // Initial load
  loadDiagnosisChart();
  loadTrendsChart();
});
