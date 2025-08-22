
document.getElementById('printDiagnosesBtn').addEventListener('click', function() {
    // Get selected year and month
    const year = document.getElementById('diagnosisYearFilter').value;
    const month = document.getElementById('diagnosisMonthFilter').value;

    // Get the chart canvases
    const topDiagnosedCanvas = document.getElementById('topDiagnosedChart');
    const trendsCanvas = document.getElementById('topTrendsDiagnosed');

    // Convert canvases to images
    const topDiagnosedImg = topDiagnosedCanvas.toDataURL('image/png');
    const trendsImg = trendsCanvas.toDataURL('image/png');

    // Create a new window
    const printWindow = window.open('', '', 'width=1000,height=700');
    printWindow.document.write(`
      <html>
      <head>
        <title>Common Diagnoses Report</title>
        <link rel="stylesheet" href="${window.location.origin}/static/css/admin_dashboard.css">
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; }
          h2 { margin-top: 0; }
          .row { display: flex; gap: 30px; }
          .col-md-6 { flex: 1; }
          img { max-width: 100%; height: auto; border: 1px solid #ccc; background: #fff; }
        </style>
      </head>
      <body>
        <div style="text-align: center;">
          <h2>Common Diagnoses Report</h2>
          <p><strong>Year:</strong> ${year || 'All'} &nbsp; <strong>Month:</strong> ${month ? document.querySelector('#diagnosisMonthFilter option:checked').text : 'All'}</p>
          <div class="row" style="justify-content: center;">
            <div class="col-md-6">
              <h5>Top Diagnosed Cases</h5>
              <img src="${topDiagnosedImg}" alt="Top Diagnosed Cases Chart" />
            </div>
            <div class="col-md-6">
              <h5>Diagnosis Trends</h5>
              <img src="${trendsImg}" alt="Diagnosis Trends Chart" />
            </div>
          </div>
        </div>
        <script>
          window.onload = function() { window.print(); }
        <\/script>
      </body>
      </html>
    `);

    // Optionally, close the window after printing
    printWindow.onafterprint = function() { printWindow.close(); };
});

// Referral Statistics Print
if (document.getElementById('printReferralStatsBtn')) {
  document.getElementById('printReferralStatsBtn').addEventListener('click', function() {
    const view = document.getElementById('reportViewFilter').value;
    const chartCanvas = document.getElementById('monthlyReportChart');
    const chartImg = chartCanvas.toDataURL('image/png');
    const printWindow = window.open('', '', 'width=900,height=700');
    printWindow.document.write(`
      <html>
      <head>
        <title>Referral Statistics Report</title>
        <link rel="stylesheet" href="${window.location.origin}/static/css/admin_dashboard.css">
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; }
          h2 { margin-top: 0; }
          .centered { text-align: center; }
          img { max-width: 100%; height: auto; border: 1px solid #ccc; background: #fff; }
        </style>
      </head>
      <body>
        <div class="centered">
          <h2>Referral Statistics Report</h2>
          <p><strong>View:</strong> ${view.charAt(0).toUpperCase() + view.slice(1)} </p>
          <img src="${chartImg}" alt="Referral Statistics Chart" />
        </div>
        <script>window.onload = function() { window.print(); }<\/script>
      </body>
      </html>
    `);
    printWindow.onafterprint = function() { printWindow.close(); };
  });
}

// Barangay Performance Print
if (document.getElementById('printBarangayBtn')) {
  document.getElementById('printBarangayBtn').addEventListener('click', function() {
    const stacked = document.getElementById('stackedBarangayChart').toDataURL('image/png');
    const radar = document.getElementById('radarBarangayChart').toDataURL('image/png');
    const grouped = document.getElementById('groupedBarangayChart').toDataURL('image/png');
    const printWindow = window.open('', '', 'width=1100,height=900');
    printWindow.document.write(`
      <html>
      <head>
        <title>Barangay Performance Report</title>
        <link rel="stylesheet" href="${window.location.origin}/static/css/admin_dashboard.css">
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; }
          h2 { margin-top: 0; }
          .row { display: flex; gap: 30px; justify-content: center; }
          .col-md-6, .col-md-12 { flex: 1; }
          img { max-width: 100%; height: auto; border: 1px solid #ccc; background: #fff; }
        </style>
      </head>
      <body>
        <div style="text-align: center;">
          <h2>Barangay Performance Report</h2>
          <div class="row">
            <div class="col-md-6">
              <h5>Referral Status Overview</h5>
              <img src="${stacked}" alt="Referral Status Overview" />
            </div>
            <div class="col-md-6">
              <h5>Comparative Analysis</h5>
              <img src="${radar}" alt="Comparative Analysis" />
            </div>
          </div>
          <div class="row" style="margin-top: 40px;">
            <div class="col-md-12">
              <h5>Completion Rate Analysis</h5>
              <img src="${grouped}" alt="Completion Rate Analysis" />
            </div>
          </div>
        </div>
        <script>window.onload = function() { window.print(); }<\/script>
      </body>
      </html>
    `);
    printWindow.onafterprint = function() { printWindow.close(); };
  });
}

// System Usage Print
if (document.getElementById('printSystemUsageBtn')) {
  document.getElementById('printSystemUsageBtn').addEventListener('click', function() {
    const chartCanvas = document.getElementById('systemUsageLogsChart');
    const chartImg = chartCanvas.toDataURL('image/png');
    const printWindow = window.open('', '', 'width=900,height=700');
    printWindow.document.write(`
      <html>
      <head>
        <title>System Usage Report</title>
        <link rel="stylesheet" href="${window.location.origin}/static/css/admin_dashboard.css">
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; }
          h2 { margin-top: 0; }
          .centered { text-align: center; }
          img { max-width: 100%; height: auto; border: 1px solid #ccc; background: #fff; }
        </style>
      </head>
      <body>
        <div class="centered">
          <h2>System Usage Report</h2>
          <img src="${chartImg}" alt="System Usage Chart" />
        </div>
        <script>window.onload = function() { window.print(); }<\/script>
      </body>
      </html>
    `);
    printWindow.onafterprint = function() { printWindow.close(); };
  });
}