# PowerShell script to perform daily database backups
# This script is designed to be run by Windows Task Scheduler
# Recommended schedule: Daily at 2:00 AM

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = $scriptDir  # MHOERS folder
$venvPath = Join-Path (Split-Path -Parent $projectDir) "venv"

# Activate virtual environment if it exists
if (Test-Path "$venvPath\Scripts\Activate.ps1") {
    & "$venvPath\Scripts\Activate.ps1"
}

# Change to project directory
Set-Location $projectDir

# Create logs directory if it doesn't exist
$logDir = Join-Path $projectDir "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Log file with date
$logFile = Join-Path $logDir "backup_daily_$(Get-Date -Format 'yyyy-MM-dd').log"

# Function to write log
function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $logFile -Value $logMessage
}

Write-Log "=== Starting Daily Database Backup ==="

# Run the backup command with compression and cleanup
# --compress: Compress backup to save space
# --cleanup: Remove backups older than retention period
# --retention-days 7: Keep backups for 7 days (1 week)
try {
    $output = python manage.py backup_database --compress --cleanup --retention-days 7 2>&1
    
    # Write output to log
    $output | ForEach-Object {
        Write-Log $_
    }
    
    # Check if backup was successful
    if ($LASTEXITCODE -eq 0) {
        Write-Log "=== Backup completed successfully ==="
        exit 0
    } else {
        Write-Log "=== Backup failed with exit code $LASTEXITCODE ==="
        exit 1
    }
} catch {
    Write-Log "=== Error during backup: $_ ==="
    exit 1
}

