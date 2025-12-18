"""
Django Management Command: Pre-generate Disease Forecast Predictions
Pre-generates and caches 2025 monthly predictions for instant page loads.
This should be run after pre-training models to warm up the cache.
"""
from django.core.management.base import BaseCommand
from analytics.ml_utils import (
    predict_disease_forecast_2025_monthly,
    predict_barangay_disease_peak_2025,
    get_ml_models_path
)
import os


class Command(BaseCommand):
    help = 'Pre-generate and cache disease forecast predictions for fast page loads'

    def add_arguments(self, parser):
        parser.add_argument(
            '--use-db',
            action='store_true',
            help='Use Django database instead of CSV files (default: use CSV)',
        )
        parser.add_argument(
            '--main-only',
            action='store_true',
            help='Generate only main disease predictions (skip barangay)',
        )
        parser.add_argument(
            '--barangay-only',
            action='store_true',
            help='Generate only barangay predictions (skip main)',
        )

    def handle(self, *args, **options):
        use_db = options['use_db']
        main_only = options['main_only']
        barangay_only = options['barangay_only']
        
        models_dir = get_ml_models_path()
        self.stdout.write(self.style.SUCCESS(f'\n📦 Models directory: {models_dir}\n'))
        
        # Check if models exist
        main_model_path = os.path.join(models_dir, 'disease_forecast_best_model.pkl')
        barangay_model_path = os.path.join(models_dir, 'barangay_disease_peak_models.pkl')
        
        main_exists = os.path.exists(main_model_path)
        barangay_exists = os.path.exists(barangay_model_path)
        
        if not main_exists and not barangay_exists:
            self.stdout.write(self.style.ERROR('❌ No models found! Please run pre_train_forecast_models first.'))
            return
        
        # Pre-generate main disease predictions
        if not barangay_only:
            if not main_exists:
                self.stdout.write(self.style.WARNING('⚠️  Main model not found. Skipping main predictions...'))
            else:
                self.stdout.write(self.style.SUCCESS('\n🔮 Generating Main Disease Forecast Predictions...'))
                self.stdout.write('   This may take 10-30 seconds (first time only)...\n')
                
                try:
                    result = predict_disease_forecast_2025_monthly()
                    
                    if "error" in result:
                        self.stdout.write(self.style.ERROR(f'❌ Error: {result["error"]}'))
                    else:
                        self.stdout.write(self.style.SUCCESS('✅ Main predictions generated and cached!'))
                        self.stdout.write(f'   Diseases: {len(result)}')
                        total_months = sum(len(months) for months in result.values())
                        self.stdout.write(f'   Total predictions: {total_months}')
                        self.stdout.write('   Cache duration: 24 hours\n')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Error generating predictions: {e}'))
        
        # Pre-generate barangay predictions
        if not main_only:
            if not barangay_exists:
                self.stdout.write(self.style.WARNING('⚠️  Barangay model not found. Skipping barangay predictions...'))
            else:
                self.stdout.write(self.style.SUCCESS('\n🔮 Generating Barangay Disease Predictions...'))
                self.stdout.write('   This may take 10-30 seconds (first time only)...\n')
                
                try:
                    result = predict_barangay_disease_peak_2025(use_db=use_db)
                    
                    if "error" in result:
                        self.stdout.write(self.style.ERROR(f'❌ Error: {result["error"]}'))
                    else:
                        self.stdout.write(self.style.SUCCESS('✅ Barangay predictions generated and cached!'))
                        self.stdout.write(f'   Barangays: {len(result)}')
                        self.stdout.write('   Predictions are now cached for fast loading\n')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Error generating barangay predictions: {e}'))
        
        self.stdout.write(self.style.SUCCESS('\n✨ Pre-generation complete!'))
        self.stdout.write('💡 Tip: Page loads will now be instant (<1 second)!\n')
        self.stdout.write('📝 Note: Predictions are cached for 24 hours. Re-run this command to refresh.\n')


