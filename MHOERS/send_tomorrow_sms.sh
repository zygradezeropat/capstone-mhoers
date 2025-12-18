#!/bin/bash

# Ubuntu script to send daily SMS reminders for TOMORROW's follow-ups
# Equivalent to send_tomorrow_sms.ps1 on Windows
# This script is designed to be run by cron

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Activate virtual environment if it exists
if [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Set API token (if needed in environment)
export IPROG_SMS_API_TOKEN="fceef382dc75566956b0dc4d64f33ade7e599d6b"

# Create logs directory if it doesn't exist
mkdir -p logs

# Log file with today's date
LOG_FILE="logs/sms_tomorrow_$(date +%Y-%m-%d).log"

# Write header to log
echo "=== $(date '+%Y-%m-%d %H:%M:%S') - Tomorrow's Follow-up SMS ===" >> "$LOG_FILE"

# Run the management command and log output
python3 manage.py send_tomorrow_checkup_sms_all >> "$LOG_FILE" 2>&1

# Optional: Print summary
echo "Tomorrow's follow-up SMS reminders sent. Check $LOG_FILE for details."








