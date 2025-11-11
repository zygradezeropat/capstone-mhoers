from django.core.management.base import BaseCommand
from django.conf import settings
import os
import subprocess
import gzip
from datetime import datetime, timedelta
import shutil


class Command(BaseCommand):
    help = 'Create a backup of the PostgreSQL database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backup-dir',
            type=str,
            default=None,
            help='Directory to store backups (default: MHOERS/backups/)',
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            help='Compress the backup file using gzip',
        )
        parser.add_argument(
            '--retention-days',
            type=int,
            default=7,
            help='Number of days to keep backups (default: 7)',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up old backups based on retention policy',
        )

    def handle(self, *args, **options):
        db_settings = settings.DATABASES['default']
        
        # Validate database engine
        if db_settings['ENGINE'] != 'django.db.backends.postgresql':
            self.stdout.write(
                self.style.ERROR('❌ This command only supports PostgreSQL databases')
            )
            return

        # Get database connection info
        db_name = db_settings['NAME']
        db_user = db_settings.get('USER', 'postgres')
        db_host = db_settings.get('HOST', 'localhost')
        db_port = db_settings.get('PORT', '5432')
        db_password = db_settings.get('PASSWORD', '')

        # Set backup directory
        if options['backup_dir']:
            backup_dir = options['backup_dir']
        else:
            # Default to MHOERS/backups/
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        
        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'MHOERS_backup_{timestamp}.sql'
        backup_path = os.path.join(backup_dir, backup_filename)

        self.stdout.write(f'📦 Creating database backup...')
        self.stdout.write(f'   Database: {db_name}')
        self.stdout.write(f'   Backup file: {backup_path}')

        try:
            # Set PGPASSWORD environment variable for pg_dump
            env = os.environ.copy()
            if db_password:
                env['PGPASSWORD'] = db_password

            # Build pg_dump command
            pg_dump_cmd = [
                'pg_dump',
                '-h', db_host,
                '-p', str(db_port),
                '-U', db_user,
                '-d', db_name,
                '--no-password',  # Use PGPASSWORD env var instead
                '--verbose',
                '--clean',  # Include DROP statements
                '--if-exists',  # Use IF EXISTS for DROP statements
            ]

            # Execute pg_dump
            with open(backup_path, 'w', encoding='utf-8') as backup_file:
                result = subprocess.run(
                    pg_dump_cmd,
                    stdout=backup_file,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True
                )

            if result.returncode != 0:
                # Clean up failed backup file
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                self.stdout.write(
                    self.style.ERROR(f'❌ Backup failed: {result.stderr}')
                )
                return

            # Compress if requested
            if options['compress']:
                self.stdout.write('🗜️  Compressing backup...')
                compressed_path = f'{backup_path}.gz'
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(backup_path)
                backup_path = compressed_path
                self.stdout.write(f'   Compressed to: {backup_path}')

            # Get file size
            file_size = os.path.getsize(backup_path)
            size_mb = file_size / (1024 * 1024)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Backup created successfully!\n'
                    f'   File: {backup_path}\n'
                    f'   Size: {size_mb:.2f} MB'
                )
            )

            # Cleanup old backups if requested
            if options['cleanup']:
                self.cleanup_old_backups(backup_dir, options['retention_days'])

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(
                    '❌ pg_dump not found. Please ensure PostgreSQL client tools are installed.\n'
                    '   On Windows: Install PostgreSQL and add bin directory to PATH\n'
                    '   On Linux: sudo apt-get install postgresql-client'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Backup failed: {str(e)}')
            )
            # Clean up failed backup file if it exists
            if os.path.exists(backup_path):
                os.remove(backup_path)

    def cleanup_old_backups(self, backup_dir, retention_days):
        """Remove backup files older than retention_days"""
        self.stdout.write(f'🧹 Cleaning up backups older than {retention_days} days...')
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0
        total_freed = 0

        try:
            for filename in os.listdir(backup_dir):
                if not filename.startswith('MHOERS_backup_'):
                    continue
                
                file_path = os.path.join(backup_dir, filename)
                
                # Get file modification time
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_mtime < cutoff_date:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    deleted_count += 1
                    total_freed += file_size
                    self.stdout.write(f'   Deleted: {filename}')

            if deleted_count > 0:
                freed_mb = total_freed / (1024 * 1024)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Cleanup complete: {deleted_count} file(s) deleted, '
                        f'{freed_mb:.2f} MB freed'
                    )
                )
            else:
                self.stdout.write('   No old backups to clean up')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Cleanup warning: {str(e)}')
            )

