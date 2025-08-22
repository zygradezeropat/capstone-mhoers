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

  // Line Chart: Monthly Patient Visits (Male vs Female)
  const lineCtx = document.getElementById("lineChart");
  if (lineCtx) {
    fetch("/referrals/api/referral-counts-by-user/")
      .then((response) => response.json())
      .then((result) => {
        const lineData = {
          labels: result.labels,
          datasets: [
            {
              label: "Total Referrals",
              data: result.data,
              borderColor: "#5c3dff",
              backgroundColor: "rgba(92, 61, 255, 0.1)",
              tension: 0.4,
              fill: true,
            },
          ],
        };
        const lineConfig = {
          type: "line",
          data: lineData,
          options: {
            responsive: true,
            plugins: {
              title: {
                display: true,
                text: "Total Referrals per User",
              },
              legend: { display: false },
            },
            scales: {
              x: {
                title: {
                  display: true,
                  text: "User (username)",
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
          },
        };
        new Chart(lineCtx, lineConfig);
      })
      .catch((error) => {
        console.error("Error fetching referral counts by user:", error);
      });
  }

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
          label: "Carcor",
          data: [150, 200, 180, 220, 150, 200, 180, 220, 150, 200, 180, 220],
          backgroundColor: "#ffb457",
          borderRadius: 10,
          barThickness: 20,
        },
        {
          label: "Mesaoy",
          data: [160, 210, 190, 230, 160, 210, 190, 230, 160, 210, 190, 230],
          backgroundColor: "#ff57d1",
          borderRadius: 10,
          barThickness: 20,
        },
        {
          label: "New Corella",
          data: [170, 220, 200, 240, 170, 220, 200, 240, 170, 220, 200, 240],
          backgroundColor: "#5c3dff",
          borderRadius: 10,
          barThickness: 20,
        },
        {
          label: "Sta. Cruz",
          data: [180, 230, 210, 250, 180, 230, 210, 250, 180, 230, 210, 250],
          backgroundColor: "#ff918e",
          borderRadius: 10,
          barThickness: 20,
        },
      ],
    };

    const yearlyData = {
      labels: ["2021", "2022", "2023", "2024"],
      datasets: [
        {
          label: "Carcor",
          data: [2100, 2400, 1980, 2300],
          backgroundColor: "#ffb457",
          borderRadius: 10,
          barThickness: 20,
        },
        {
          label: "Mesaoy",
          data: [2050, 2200, 2150, 2250],
          backgroundColor: "#ff57d1",
          borderRadius: 10,
          barThickness: 20,
        },
        {
          label: "New Corella",
          data: [2250, 2500, 2400, 2650],
          backgroundColor: "#5c3dff",
          borderRadius: 10,
          barThickness: 20,
        },
        {
          label: "Sta. Cruz",
          data: [1950, 2100, 2200, 2000],
          backgroundColor: "#ff918e",
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
