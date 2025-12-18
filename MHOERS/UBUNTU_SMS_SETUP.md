# Ubuntu SMS Setup Guide - Tomorrow's Follow-ups

## Step 1: Make Script Executable

```bash
chmod +x send_tomorrow_sms.sh
```

## Step 2: Test the Script Manually

```bash
cd /path/to/MHOERS/MHOERS
./send_tomorrow_sms.sh
```

## Step 3: Set Up Cron Job

### Option A: Edit Crontab Directly

```bash
crontab -e
```

Add this line (runs daily at 7:00 AM):
```bash
0 7 * * * cd /path/to/MHOERS/MHOERS && /path/to/MHOERS/send_tomorrow_sms.sh >> /path/to/MHOERS/logs/sms_tomorrow_cron.log 2>&1
```

**Important:** Replace `/path/to/MHOERS` with your actual project path.

### Option B: Add to Crontab via Command

```bash
(crontab -l 2>/dev/null; echo "0 7 * * * cd /path/to/MHOERS/MHOERS && /path/to/MHOERS/send_tomorrow_sms.sh >> /path/to/MHOERS/logs/sms_tomorrow_cron.log 2>&1") | crontab -
```

## Step 4: Verify Cron Job

```bash
# List your cron jobs
crontab -l

# Check cron service status
sudo systemctl status cron
```

## Step 5: Test the Cron Job

```bash
# Run the script manually to test
./send_tomorrow_sms.sh

# Or test with dry-run (if implemented)
python3 manage.py send_tomorrow_checkup_sms_all
```

## Troubleshooting

### Check Logs
```bash
tail -f logs/sms_tomorrow_$(date +%Y-%m-%d).log
```

### Check Cron Logs
```bash
grep CRON /var/log/syslog | tail -20
```

### Verify Python Path
```bash
which python3
# Use full path in cron if needed: /usr/bin/python3
```

### Test Script Paths
```bash
# Make sure all paths are absolute in cron
# Example with full paths:
0 7 * * * /usr/bin/bash /home/user/MHOERS/MHOERS/send_tomorrow_sms.sh >> /home/user/MHOERS/MHOERS/logs/sms_tomorrow_cron.log 2>&1
```

## Notes

- The script runs daily at 7:00 AM
- It checks for follow-ups scheduled for TOMORROW
- Duplicate prevention is handled by the `SMSReminderLog` model
- Logs are saved in the `logs/` directory with date stamps








