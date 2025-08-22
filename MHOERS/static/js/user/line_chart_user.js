document.addEventListener("DOMContentLoaded", function () {
  
  // Monthly and Yearly Report per Barangay (Stacked Bar with Filter)
  const reportCtx = document.getElementById("monthlyReportChart");
  if (reportCtx) {
    const ctx = reportCtx.getContext("2d");

    const monthlyData = {
      labels: [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sept",
        "Oct",
        "Nov",
        "Dec",
      ],
      datasets: [
        {
          label: "Barangay 1",
          data: [150, 200, 180, 220, 150, 200, 180, 220, 150, 200, 180, 220],
          backgroundColor: "#ffb457",
          borderRadius: 10,
          barThickness: 20,
        },
      ],
    };

    const yearlyData = {
      labels: ["2021", "2022", "2023", "2024"],
      datasets: [
        {
          label: "Barangay 1",
          data: [2100, 2400, 1980, 2300],
          backgroundColor: "#ffb457",
          borderRadius: 10,
          barThickness: 20,
        },
      ],
    };

    const reportChart = new Chart(ctx, {
      type: "bar",
      data: monthlyData,
      options: {
        indexAxis: "x",
        responsive: true,
        scales: {
          x: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Month/Year",
            },
          },
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Number of Referred Patients",
            },
          },
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: (context) => `${context.parsed.y} patients`,
            },
          },
        },
      },
    });

    document
      .getElementById("reportViewFilter")
      .addEventListener("change", function () {
        const selected = this.value;
        reportChart.data = selected === "monthly" ? monthlyData : yearlyData;
        reportChart.update();
      });
  }

  //PIE CHART FOR TOP DIAGNOSIS
});
