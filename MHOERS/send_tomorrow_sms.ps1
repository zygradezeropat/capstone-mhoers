# PowerShell script to send daily SMS reminders for TOMORROW's follow-ups at 7 AM
# This script is designed to be run by Windows Task Scheduler

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = $scriptDir  # MHOERS folder
$venvPath = Join-Path (Split-Path -Parent $projectDir) "venv"

# Activate virtual environment if it exists
if (Test-Path "$venvPath\Scripts\Activate.ps1") {
    & "$venvPath\Scripts\Activate.ps1"
}

# Set API token
$env:IPROG_SMS_API_TOKEN = "fceef382dc75566956b0dc4d64f33ade7e599d6b"

# Change to project directory
Set-Location $projectDir

# Create logs directory if it doesn't exist
$logDir = Join-Path $projectDir "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Log file with today's date
$logFile = Join-Path $logDir "sms_tomorrow_$(Get-Date -Format 'yyyy-MM-dd').log"

# Write header to log
"=== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Tomorrow's Follow-up SMS ===" | Out-File -Append -FilePath $logFile

# Run the management command and log output
python manage.py send_tomorrow_checkup_sms_all 2>&1 | Out-File -Append -FilePath $logFile

# Optional: Print summary to console
Write-Host "Tomorrow's follow-up SMS reminders sent. Check $logFile for details."








