// Report Generation Functions
document.addEventListener('DOMContentLoaded', function() {
    // Initialize report checkboxes
    const reportCheckboxes = document.querySelectorAll('input[name="printSelection"]');
    const printReportButton = document.getElementById('printReportButton');
    const completeReportCheckbox = document.getElementById('reportTab4');
    const otherCheckboxes = Array.from(reportCheckboxes).filter(cb => cb.id !== 'reportTab4');

    // Handle complete report checkbox
    completeReportCheckbox.addEventListener('change', function() {
        if (this.checked) {
            // Uncheck and disable other checkboxes
            otherCheckboxes.forEach(cb => {
                cb.checked = false;
                cb.disabled = true;
            });
        } else {
            // Enable other checkboxes
            otherCheckboxes.forEach(cb => {
                cb.disabled = false;
            });
        }
    });

    // Enable/disable print button based on checkbox selection
    reportCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const anyChecked = Array.from(reportCheckboxes).some(cb => cb.checked);
            printReportButton.disabled = !anyChecked;
        });
    });

    // Handle report generation
    printReportButton.addEventListener('click', function() {
        const selectedReports = Array.from(reportCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.id);

        if (selectedReports.length === 0) {
            alert('Please select at least one report to generate.');
            return;
        }

        generateReports(selectedReports);
    });

    // Report view filter change handler
    const reportViewFilter = document.getElementById('reportViewFilter');
    if (reportViewFilter) {
        reportViewFilter.addEventListener('change', function() {
            updateChartView(this.value);
        });
    }
});

// Function to generate selected reports
function generateReports(selectedReports) {
    // Show loading state
    const printButton = document.getElementById('printReportButton');
    const originalText = printButton.innerHTML;
    printButton.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Generating Reports...';
    printButton.disabled = true;

    // Create a new window for printing
    const printWindow = window.open('', '_blank');
    
    // Get the current date and time
    const now = new Date();
    const dateStr = now.toLocaleDateString();
    const timeStr = now.toLocaleTimeString();

    // Prepare the print content
    let printContent = `
        <html>
        <head>
            <title>MHO-ERS Reports</title>
            <style>
                @page { 
                    size: A4 landscape; 
                    margin: 20mm 15mm;
                }
                * {
                    font-family: Arial, sans-serif !important;
                }
                body { 
                    font-family: Arial, sans-serif; 
                    font-size: 12pt;
                    margin: 0;
                    padding: 20px;
                    color: #000;
                    line-height: 1.5;
                }
                .header { 
                    text-align: center; 
                    margin-bottom: 30px;
                    border-bottom: 2px solid #333;
                    padding-bottom: 15px;
                }
                .header h1 {
                    font-size: 18pt;
                    font-weight: bold;
                    margin: 0 0 10px 0;
                    color: #000;
                }
                .header p {
                    font-size: 12pt;
                    margin: 5px 0;
                    color: #666;
                }
                .report-section { 
                    margin-bottom: 40px; 
                    page-break-after: always;
                }
                .report-section h2 {
                    font-size: 14pt;
                    font-weight: bold;
                    margin: 20px 0 15px 0;
                    color: #000;
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 8px;
                }
                .report-section h3 {
                    font-size: 12pt;
                    font-weight: bold;
                    margin: 15px 0 10px 0;
                    color: #000;
                }
                .chart-container { 
                    margin: 20px 0; 
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 12pt;
                    margin: 15px 0;
                }
                th, td {
                    border: 1px solid #000;
                    padding: 8px 10px;
                    text-align: left;
                    font-size: 12pt;
                }
                th {
                    background-color: #f5f5f5;
                    font-weight: bold;
                    text-align: center;
                }
                .footer { 
                    text-align: center; 
                    margin-top: 30px; 
                    padding-top: 15px;
                    border-top: 1px solid #ccc;
                    font-size: 11pt; 
                    color: #666; 
                }
                @media print {
                    .no-print { display: none; }
                    .page-break { page-break-before: always; }
                    body { 
                        margin: 0;
                        padding: 15px;
                    }
                    @page {
                        size: A4 landscape;
                        margin: 20mm 15mm;
                    }
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>MHO-ERS Analytics Report</h1>
                <p>Generated on: ${dateStr} at ${timeStr}</p>
            </div>
    `;

    // Add selected reports content
    selectedReports.forEach(reportId => {
        const reportTitle = document.querySelector(`label[for="${reportId}"]`).textContent;
        printContent += `
            <div class="report-section">
                <h2>${reportTitle}</h2>
                <div class="chart-container">
                    ${getReportContent(reportId)}
                </div>
            </div>
        `;
    });

    printContent += `
            <div class="footer">
                <p>© ${new Date().getFullYear()} MHOERS. All rights reserved.</p>
            </div>
        </body>
        </html>
    `;

    // Write content to the new window
    printWindow.document.write(printContent);
    printWindow.document.close();

    // Wait for images and charts to load
    setTimeout(() => {
        // Print the window
        printWindow.print();
        // Close the window after printing
        printWindow.onafterprint = function() {
            printWindow.close();
        };
    }, 2000); // Increased timeout to ensure charts are rendered

    // Reset button state
    printButton.innerHTML = originalText;
    printButton.disabled = false;
}

// Function to get report content based on report type
function getReportContent(reportId) {
    let content = '';
    
    switch(reportId) {
        case 'reportTab1':
            // Common Diagnoses Report
            const topDiagnosedChart = document.getElementById('topDiagnosedChart');
            const topTrendsChart = document.getElementById('topTrendsDiagnosed');
            if (topDiagnosedChart && topTrendsChart) {
                content = `
                    <div class="chart-container">
                        <h3>Top Diagnosed Cases</h3>
                        <img src="${topDiagnosedChart.toDataURL('image/png')}" style="width: 100%; max-width: 600px;">
                    </div>
                    <div class="chart-container">
                        <h3>Diagnosis Trends</h3>
                        <img src="${topTrendsChart.toDataURL('image/png')}" style="width: 100%; max-width: 600px;">
                    </div>
                `;
            }
            break;
            
        case 'reportTab2':
            // Barangay Performance Report
            const stackedChart = document.getElementById('stackedBarangayChart');
            const radarChart = document.getElementById('radarBarangayChart');
            const groupedChart = document.getElementById('groupedBarangayChart');
            if (stackedChart && radarChart && groupedChart) {
                content = `
                    <div class="chart-container">
                        <h3>Referral Status Overview</h3>
                        <img src="${stackedChart.toDataURL('image/png')}" style="width: 100%; max-width: 600px;">
                    </div>
                    <div class="chart-container">
                        <h3>Comparative Analysis</h3>
                        <img src="${radarChart.toDataURL('image/png')}" style="width: 100%; max-width: 600px;">
                    </div>
                    <div class="chart-container">
                        <h3>Completion Rate Analysis</h3>
                        <img src="${groupedChart.toDataURL('image/png')}" style="width: 100%; max-width: 600px;">
                    </div>
                `;
            }
            break;
            
        case 'reportTab3':
            // Referral Statistics Report
            const monthlyChart = document.getElementById('monthlyReportChart');
            const reportViewFilter = document.getElementById('reportViewFilter');
            const viewType = reportViewFilter ? reportViewFilter.value : 'monthly';
            
            if (monthlyChart) {
                try {
                    // Get the Chart.js instance
                    const chartInstance = Chart.getChart(monthlyChart);
                    if (chartInstance) {
                        // Force chart update
                        chartInstance.update();
                        
                        // Capture chart immediately after update
                        content = `
                            <div class="chart-container">
                                <h3>${viewType === 'monthly' ? 'Monthly' : 'Yearly'} Referral Analytics</h3>
                                <img src="${monthlyChart.toDataURL('image/png')}" style="width: 100%; max-width: 600px;">
                            </div>
                        `;
                    }
                } catch (error) {
                    console.error('Error capturing chart:', error);
                }
            }
            break;

        case 'reportTab4':
            // Complete Analytics Report - Include all charts
            const allCharts = {
                monthlyChart: document.getElementById('monthlyReportChart'),
                topDiagnosedChart: document.getElementById('topDiagnosedChart'),
                topTrendsChart: document.getElementById('topTrendsDiagnosed'),
                stackedChart: document.getElementById('stackedBarangayChart'),
                radarChart: document.getElementById('radarBarangayChart'),
                groupedChart: document.getElementById('groupedBarangayChart')
            };

            content = Object.entries(allCharts)
                .filter(([_, chart]) => chart)
                .map(([name, chart]) => {
                    try {
                        const chartInstance = Chart.getChart(chart);
                        if (chartInstance) {
                            chartInstance.update();
                        }
                        return `
                            <div class="chart-container">
                                <h3>${name.replace('Chart', ' Analysis')}</h3>
                                <img src="${chart.toDataURL('image/png')}" style="width: 100%; max-width: 600px;">
                            </div>
                        `;
                    } catch (error) {
                        console.error(`Error capturing ${name}:`, error);
                        return '';
                    }
                }).join('');
            break;
    }
    
    return content;
}

// Function to update chart view based on selected time period
function updateChartView(viewType) {
    // Get the chart instance
    const chart = Chart.getChart('monthlyReportChart');
    if (!chart) return;

    // Update chart data based on view type
    if (viewType === 'monthly') {
        // Update for monthly view
        updateMonthlyData();
    } else if (viewType === 'yearly') {
        // Update for yearly view
        updateYearlyData();
    }
}

// Function to update monthly data
function updateMonthlyData() {
    const currentYear = new Date().getFullYear();
    const url = `/analytics/api/referral-statistics/?view_type=monthly&year=${currentYear}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const chart = Chart.getChart('monthlyReportChart');
            if (chart) {
                chart.data.labels = data.labels;
                chart.data.datasets = data.datasets;
                chart.update();
            }
        })
        .catch(error => {
            console.error('Error updating monthly data:', error);
        });
}

// Function to update yearly data
function updateYearlyData() {
    const currentYear = new Date().getFullYear();
    const url = `/analytics/api/referral-statistics/?view_type=yearly&year=${currentYear}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const chart = Chart.getChart('monthlyReportChart');
            if (chart) {
                chart.data.labels = data.labels;
                chart.data.datasets = data.datasets;
                chart.update();
            }
        })
        .catch(error => {
            console.error('Error updating yearly data:', error);
        });
}

// Function to handle tab switching
function handleTabSwitch(tabId) {
    // Add any necessary chart resizing or data updates when switching tabs
    const charts = ['monthlyReportChart', 'topDiagnosedChart', 'topTrendsDiagnosed', 
                   'stackedBarangayChart', 'radarBarangayChart', 'groupedBarangayChart'];
    
    charts.forEach(chartId => {
        const chart = Chart.getChart(chartId);
        if (chart) {
            chart.resize();
        }
    });
}

// Add event listeners for tab switching
document.querySelectorAll('a[data-bs-toggle="tab"]').forEach(tab => {
    tab.addEventListener('shown.bs.tab', function(e) {
        handleTabSwitch(e.target.id);
    });
}); 