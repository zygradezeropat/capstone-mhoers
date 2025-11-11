# PowerShell script to automatically set up Windows Task Scheduler for daily SMS reminders
# Run this script once to configure the scheduled task

# Get the script directory and project paths
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = $scriptDir  # MHOERS folder
$smsScriptPath = Join-Path $projectDir "send_daily_sms.ps1"

# Task Scheduler task name
$taskName = "MHOERS Daily SMS Reminders"

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator to create Task Scheduler tasks." -ForegroundColor Red
    Write-Host "Please right-click PowerShell and select 'Run as Administrator', then run this script again." -ForegroundColor Yellow
    exit 1
}

# Check if SMS script exists
if (-not (Test-Path $smsScriptPath)) {
    Write-Host "ERROR: SMS script not found at: $smsScriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "Setting up Task Scheduler for daily SMS reminders..." -ForegroundColor Green
Write-Host "Project Directory: $projectDir" -ForegroundColor Cyan
Write-Host "SMS Script: $smsScriptPath" -ForegroundColor Cyan

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "Task '$taskName' already exists." -ForegroundColor Yellow
    $response = Read-Host "Do you want to update it? (Y/N)"
    if ($response -ne 'Y' -and $response -ne 'y') {
        Write-Host "Skipping task creation." -ForegroundColor Yellow
        exit 0
    }
    # Remove existing task
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Removed existing task." -ForegroundColor Green
}

# Create the action (run PowerShell script)
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"$smsScriptPath`"" `
    -WorkingDirectory $projectDir

# Create the trigger (daily at 7:00 AM)
$trigger = New-ScheduledTaskTrigger -Daily -At "7:00AM"

# Create task settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -MultipleInstances IgnoreNew

# Create task principal (run whether user is logged on or not)
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Highest

# Register the scheduled task
try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Automated daily SMS reminders for patients with follow-up appointments scheduled today. Sends at 7:00 AM daily." `
        -Force | Out-Null
    
    Write-Host "`nSUCCESS: Task Scheduler task created successfully!" -ForegroundColor Green
    Write-Host "Task Name: $taskName" -ForegroundColor Cyan
    Write-Host "Schedule: Daily at 7:00 AM" -ForegroundColor Cyan
    Write-Host "Script: $smsScriptPath" -ForegroundColor Cyan
    Write-Host "`nTo test the task, run:" -ForegroundColor Yellow
    Write-Host "  Start-ScheduledTask -TaskName `"$taskName`"" -ForegroundColor White
    Write-Host "`nTo view task details:" -ForegroundColor Yellow
    Write-Host "  Get-ScheduledTask -TaskName `"$taskName`" | Get-ScheduledTaskInfo" -ForegroundColor White
    Write-Host "`nTo delete the task (if needed):" -ForegroundColor Yellow
    Write-Host "  Unregister-ScheduledTask -TaskName `"$taskName`" -Confirm:`$false" -ForegroundColor White
    
} catch {
    Write-Host "ERROR: Failed to create scheduled task: $_" -ForegroundColor Red
    exit 1
}

# Test if we can see the task
$createdTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($createdTask) {
    Write-Host "`nTask verification: Task found in Task Scheduler!" -ForegroundColor Green
} else {
    Write-Host "`nWARNING: Task created but could not be verified." -ForegroundColor Yellow
}



