# Database Backup Setup Guide

This guide explains how to set up automated daily database backups for the MHOERS-RMS system.

## Overview

The backup system consists of:
1. **Django Management Command**: `backup_database.py` - Performs PostgreSQL database backups
2. **PowerShell Script**: `backup_database_daily.ps1` - Scheduled script for daily backups
3. **Automatic Cleanup**: Removes backups older than specified retention period

## Prerequisites

1. **PostgreSQL Client Tools**: `pg_dump` must be installed and accessible in PATH
   - Windows: Install PostgreSQL (includes pg_dump in `bin` folder)
   - Linux: `sudo apt-get install postgresql-client` or `sudo yum install postgresql`

2. **Python gzip module**: Included in standard library (no installation needed)

## Manual Backup

You can run backups manually using the Django management command:

```bash
# Basic backup
python manage.py backup_database

# Compressed backup
python manage.py backup_database --compress

# Backup with automatic cleanup (removes backups older than 7 days)
python manage.py backup_database --compress --cleanup --retention-days 7

# Custom backup directory
python manage.py backup_database --backup-dir /path/to/backups
```

### Command Options

- `--backup-dir`: Custom directory for backups (default: `MHOERS/backups/`)
- `--compress`: Compress backup using gzip (saves disk space)
- `--retention-days N`: Number of days to keep backups (default: 7)
- `--cleanup`: Remove old backups based on retention policy

## Automated Daily Backups (Windows Task Scheduler)

### Step 1: Verify PowerShell Script

The script `backup_database_daily.ps1` is located in the `MHOERS` directory.

### Step 2: Create Scheduled Task

1. Open **Task Scheduler** (search "Task Scheduler" in Windows)
2. Click **Create Basic Task** (or **Create Task** for advanced options)
3. Configure the task:
   - **Name**: `MHOERS Daily Database Backup`
   - **Description**: `Automated daily backup of MHOERS PostgreSQL database`
   - **Trigger**: Daily at 2:00 AM (or your preferred time)
   - **Action**: Start a program
   - **Program/script**: `powershell.exe`
   - **Arguments**: 
     ```
     -ExecutionPolicy Bypass -File "C:\Users\63912\OneDrive\Documents\MHOERS-RMS\MHOERS\backup_database_daily.ps1"
     ```
     (Adjust the path to match your actual project location)
   - **Start in**: `C:\Users\63912\OneDrive\Documents\MHOERS-RMS\MHOERS`
     (Adjust to your project directory)

4. **Security Options**:
   - Select "Run whether user is logged on or not"
   - Check "Run with highest privileges" (if needed for database access)
   - Configure the account that has database access permissions

5. **Conditions** (optional):
   - Uncheck "Start the task only if the computer is on AC power" (for servers)

6. **Settings**:
   - Check "Allow task to be run on demand"
   - Check "Run task as soon as possible after a scheduled start is missed"
   - Configure retry options if desired

### Step 3: Test the Task

1. Right-click the task in Task Scheduler
2. Select **Run**
3. Check the log file: `MHOERS/logs/backup_daily_YYYY-MM-DD.log`
4. Verify backup file exists: `MHOERS/backups/MHOERS_backup_YYYYMMDD_HHMMSS.sql.gz`

## Backup File Location

By default, backups are stored in:
```
MHOERS/backups/
```

Backup files are named:
- Uncompressed: `MHOERS_backup_YYYYMMDD_HHMMSS.sql`
- Compressed: `MHOERS_backup_YYYYMMDD_HHMMSS.sql.gz`

## Backup Retention

The default retention policy keeps backups for **7 days (1 week)**. Older backups are automatically deleted when using the `--cleanup` flag.

To change retention period:
```bash
# Keep backups for 30 days
python manage.py backup_database --cleanup --retention-days 30

# Keep backups for 60 days
python manage.py backup_database --cleanup --retention-days 60
```

## Restoring from Backup

### Restore from uncompressed backup:
```bash
psql -h localhost -U postgres -d MHOERS < MHOERS/backups/MHOERS_backup_YYYYMMDD_HHMMSS.sql
```

### Restore from compressed backup:
```bash
gunzip -c MHOERS/backups/MHOERS_backup_YYYYMMDD_HHMMSS.sql.gz | psql -h localhost -U postgres -d MHOERS
```

Or on Windows with PowerShell:
```powershell
Get-Content MHOERS/backups/MHOERS_backup_YYYYMMDD_HHMMSS.sql.gz | gunzip | psql -h localhost -U postgres -d MHOERS
```

## Troubleshooting

### Error: "pg_dump not found"
- **Solution**: Install PostgreSQL client tools and ensure `pg_dump` is in your system PATH
- Windows: Add PostgreSQL `bin` directory to PATH environment variable
- Linux: Install `postgresql-client` package

### Error: "password authentication failed"
- **Solution**: Ensure the database password in `settings.py` is correct
- The command uses `PGPASSWORD` environment variable for authentication

### Error: "Permission denied"
- **Solution**: Ensure the backup directory is writable
- Check file permissions on the `MHOERS/backups/` directory

### Backup file is too large
- **Solution**: Use `--compress` flag to enable gzip compression
- Compressed backups are typically 70-90% smaller

## Monitoring

### Check Backup Logs
Logs are stored in: `MHOERS/logs/backup_daily_YYYY-MM-DD.log`

### Verify Recent Backups
```bash
# List recent backups
ls -lt MHOERS/backups/ | head -10

# On Windows PowerShell
Get-ChildItem MHOERS/backups/ | Sort-Object LastWriteTime -Descending | Select-Object -First 10
```

### Check Backup Size
```bash
# Linux/Mac
du -sh MHOERS/backups/*

# Windows PowerShell
Get-ChildItem MHOERS/backups/ | Select-Object Name, @{Name="Size(MB)";Expression={[math]::Round($_.Length/1MB,2)}}
```

## Best Practices

1. **Test Restores**: Periodically test restoring from backups to ensure they work
2. **Offsite Storage**: Consider copying backups to cloud storage or remote server
3. **Monitor Disk Space**: Ensure backup directory has sufficient space
4. **Retention Policy**: Adjust retention days based on your needs and available storage
5. **Backup Before Updates**: Always create a backup before major system updates
6. **Encryption**: For sensitive data, consider encrypting backup files

## Integration with Cloud Storage (Optional)

You can extend the PowerShell script to upload backups to cloud storage:

```powershell
# Example: Upload to cloud storage after backup
# Add to backup_database_daily.ps1 after successful backup

# Example for AWS S3 (requires AWS CLI)
# aws s3 cp $backupPath s3://your-bucket/backups/

# Example for Azure Blob Storage (requires Azure CLI)
# az storage blob upload --file $backupPath --container-name backups --name (Split-Path $backupPath -Leaf)
```

## Support

For issues or questions:
1. Check the log files in `MHOERS/logs/`
2. Verify PostgreSQL connection settings in `MHOERS/settings.py`
3. Test the backup command manually first before scheduling

