# PowerShell script to send daily SMS reminders at 7 AM
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

# Run the management command
python manage.py send_today_checkup_sms_all

# Optional: Log output to a file
$logFile = Join-Path $projectDir "logs\sms_daily_$(Get-Date -Format 'yyyy-MM-dd').log"
$logDir = Split-Path -Parent $logFile
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}
"=== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ===" | Out-File -Append -FilePath $logFile
python manage.py send_today_checkup_sms_all 2>&1 | Out-File -Append -FilePath $logFile

