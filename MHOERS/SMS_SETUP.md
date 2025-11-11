# SMS Follow-up Setup Guide

This guide explains how to set up automated daily SMS reminders for patients with follow-up appointments.

## Overview

The SMS system consists of:
1. **Django Management Command**: `send_today_checkup_sms_all` - Sends SMS to all patients with follow-ups scheduled today
2. **PowerShell Script**: `send_daily_sms.ps1` - Scheduled script for daily SMS sending
3. **Setup Script**: `setup_sms_scheduler.ps1` - Automatically configures Windows Task Scheduler

## Automatic Setup (Recommended)

### Step 1: Run the Setup Script

1. **Open PowerShell as Administrator**:
   - Press `Win + X` and select "Windows PowerShell (Admin)" or "Terminal (Admin)"
   - Or search for "PowerShell" in Start Menu, right-click, and select "Run as Administrator"

2. **Navigate to the MHOERS directory**:
   ```powershell
   cd "C:\Users\63912\OneDrive\Documents\MHOERS-RMS\MHOERS"
   ```

3. **Run the setup script**:
   ```powershell
   .\setup_sms_scheduler.ps1
   ```

The script will:
- Check if you're running as Administrator
- Verify the SMS script exists
- Create the Task Scheduler task named "MHOERS Daily SMS Reminders"
- Configure it to run daily at 7:00 AM
- Set it to run whether the user is logged on or not

### Step 2: Verify the Task

After running the setup script, verify the task was created:

```powershell
Get-ScheduledTask -TaskName "MHOERS Daily SMS Reminders"
```

## Manual Setup (Alternative)

If automatic setup doesn't work, you can manually create the task:

1. Open **Task Scheduler** (search "Task Scheduler" in Windows)
2. Click **Create Basic Task** (or **Create Task** for advanced options)
3. Configure the task:
   - **Name**: `MHOERS Daily SMS Reminders`
   - **Description**: `Automated daily SMS reminders for patients with follow-up appointments scheduled today. Sends at 7:00 AM daily.`
   - **Trigger**: Daily at 7:00 AM (or your preferred time)
   - **Action**: Start a program
   - **Program/script**: `powershell.exe`
   - **Arguments**: 
     ```
     -ExecutionPolicy Bypass -File "C:\Users\63912\OneDrive\Documents\MHOERS-RMS\MHOERS\send_daily_sms.ps1"
     ```
     (Adjust the path to match your actual project location)
   - **Start in**: `C:\Users\63912\OneDrive\Documents\MHOERS-RMS\MHOERS`
     (Adjust to your project directory)

4. **Security Options**:
   - Select "Run whether user is logged on or not"
   - Check "Run with highest privileges" (if needed)
   - Configure the account that has necessary permissions

5. **Conditions** (optional):
   - Uncheck "Start the task only if the computer is on AC power" (for servers)

6. **Settings**:
   - Check "Allow task to be run on demand"
   - Check "Run task as soon as possible after a scheduled start is missed"

## Testing

### Test the Scheduled Task

Run the task manually to test it:

```powershell
Start-ScheduledTask -TaskName "MHOERS Daily SMS Reminders"
```

### Check Task Status

View task information:

```powershell
Get-ScheduledTask -TaskName "MHOERS Daily SMS Reminders" | Get-ScheduledTaskInfo
```

### View Logs

Check the SMS logs:

```powershell
Get-Content "logs\sms_daily_$(Get-Date -Format 'yyyy-MM-dd').log"
```

Or navigate to: `MHOERS/logs/sms_daily_YYYY-MM-DD.log`

## Manual Execution

You can also run the SMS script manually without waiting for the scheduled time:

### Option 1: Run PowerShell Script

```powershell
.\send_daily_sms.ps1
```

### Option 2: Run Django Management Command

```bash
python manage.py send_today_checkup_sms_all
```

### Option 3: Send SMS to Specific Patient

Use the API endpoint:
```
GET /patients/api/send-today-checkup-sms/<patient_id>/
```

## Command Options

The management command supports several options:

```bash
# Send to all patients with follow-ups today
python manage.py send_today_checkup_sms_all

# Send only for a specific facility
python manage.py send_today_checkup_sms_all --facility-id 1

# Use custom sender ID
python manage.py send_today_checkup_sms_all --sender-id "MHO-NewCorella"

# Dry run (list targets without sending)
python manage.py send_today_checkup_sms_all --dry-run
```

## SMS Message Format

The SMS message sent to patients:

- **If advice is available**: `Hi [First Name] [Last Name], reminder: [advice text].`
- **Default message**: `Hi [First Name] [Last Name], this is a reminder of your medical check-up scheduled today.`

## Troubleshooting

### Error: "This script must be run as Administrator"

**Solution**: Right-click PowerShell and select "Run as Administrator", then run the setup script again.

### Error: "SMS script not found"

**Solution**: Ensure `send_daily_sms.ps1` exists in the MHOERS directory.

### Error: "IPROG SMS API token not set"

**Solution**: The API token is set in the PowerShell script. Verify it's correct in `send_daily_sms.ps1`:
```powershell
$env:IPROG_SMS_API_TOKEN = "fceef382dc75566956b0dc4d64f33ade7e599d6b"
```

### SMS Not Sending

1. **Check logs**: Review `logs/sms_daily_YYYY-MM-DD.log` for error messages
2. **Test manually**: Run `python manage.py send_today_checkup_sms_all --dry-run` to see which patients would receive SMS
3. **Verify follow-up dates**: Ensure patients have `followup_date` set to today in `Medical_History`
4. **Check phone numbers**: Verify patients have valid phone numbers in `p_number` field

### Task Not Running

1. **Check Task Scheduler**: Open Task Scheduler and verify the task exists and is enabled
2. **Check last run**: View task history in Task Scheduler
3. **Test manually**: Run `Start-ScheduledTask -TaskName "MHOERS Daily SMS Reminders"`
4. **Check permissions**: Ensure the task is configured to run with appropriate permissions

## Updating the Task

If you need to update the scheduled task (e.g., change the time):

1. **Delete the existing task**:
   ```powershell
   Unregister-ScheduledTask -TaskName "MHOERS Daily SMS Reminders" -Confirm:$false
   ```

2. **Run the setup script again**:
   ```powershell
   .\setup_sms_scheduler.ps1
   ```

Or manually edit the task in Task Scheduler.

## Removing the Task

To completely remove the scheduled task:

```powershell
Unregister-ScheduledTask -TaskName "MHOERS Daily SMS Reminders" -Confirm:$false
```

## Monitoring

### Check Recent SMS Activity

View the latest log file:
```powershell
Get-Content "logs\sms_daily_$(Get-Date -Format 'yyyy-MM-dd').log" -Tail 50
```

### Check Task Execution History

1. Open Task Scheduler
2. Find "MHOERS Daily SMS Reminders"
3. Click "History" tab to see execution logs

## Best Practices

1. **Test First**: Always test with `--dry-run` before scheduling
2. **Monitor Logs**: Regularly check SMS logs for errors
3. **Verify Phone Numbers**: Ensure patient phone numbers are valid and in correct format
4. **Time Selection**: Choose a time (e.g., 7 AM) when patients are likely to be awake
5. **Backup Plan**: Keep manual execution option available for urgent reminders

## Support

For issues or questions:
1. Check the log files in `MHOERS/logs/`
2. Verify IPROG SMS API token in `send_daily_sms.ps1`
3. Test the management command manually first before scheduling
4. Review Task Scheduler history for execution errors



