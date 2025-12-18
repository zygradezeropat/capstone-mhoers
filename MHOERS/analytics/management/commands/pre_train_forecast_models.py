"""
Django Management Command: Pre-train Disease Forecast Models
Pre-trains and saves disease forecast models to PKL files for fast loading.
This solves the loading delay problem by training models before users access the page.
"""
import os
from django.core.management.base import BaseCommand
from analytics.ml_utils import (
    train_disease_forecast_best_model,
    train_barangay_disease_peak_model,
    get_ml_models_path
)


class Command(BaseCommand):
    help = 'Pre-train disease forecast models and save to PKL files for fast loading'

    def add_arguments(self, parser):
        parser.add_argument(
            '--use-db',
            action='store_true',
            help='Use Django database instead of CSV files (default: use CSV)',
        )
        parser.add_argument(
            '--main-model-only',
            action='store_true',
            help='Train only the main disease forecast model (skip barangay model)',
        )
        parser.add_argument(
            '--barangay-model-only',
            action='store_true',
            help='Train only the barangay disease peak model (skip main model)',
        )
        parser.add_argument(
            '--csv-2023',
            type=str,
            default=None,
            help='Path to 2023 CSV file (default: auto-detect)',
        )
        parser.add_argument(
            '--csv-2024',
            type=str,
            default=None,
            help='Path to 2024 CSV file (default: auto-detect)',
        )

    def handle(self, *args, **options):
        use_db = options['use_db']
        main_only = options['main_model_only']
        barangay_only = options['barangay_model_only']
        csv_2023 = options['csv_2023']
        csv_2024 = options['csv_2024']
        
        models_dir = get_ml_models_path()
        self.stdout.write(self.style.SUCCESS(f'\n📦 Models will be saved to: {models_dir}\n'))
        
        # Check if models already exist
        main_model_path = os.path.join(models_dir, 'disease_forecast_best_model.pkl')
        barangay_model_path = os.path.join(models_dir, 'barangay_disease_peak_models.pkl')
        
        main_exists = os.path.exists(main_model_path)
        barangay_exists = os.path.exists(barangay_model_path)
        
        if main_exists:
            self.stdout.write(self.style.WARNING('⚠️  Main model already exists. Will retrain...'))
        if barangay_exists:
            self.stdout.write(self.style.WARNING('⚠️  Barangay model already exists. Will retrain...'))
        
        # Train main disease forecast model
        if not barangay_only:
            self.stdout.write(self.style.SUCCESS('\n🧠 Training Main Disease Forecast Model...'))
            self.stdout.write('   This may take 2-5 minutes...\n')
            
            try:
                result = train_disease_forecast_best_model(
                    csv_2023_path=csv_2023,
                    csv_2024_path=csv_2024,
                    use_db=use_db
                )
                
                if "error" in result:
                    self.stdout.write(self.style.ERROR(f'❌ Error: {result["error"]}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'✅ Main model trained successfully!'))
                    self.stdout.write(f'   Best model: {result["best_model"]}')
                    self.stdout.write(f'   Train RMSE: {result["train_rmse"]}')
                    self.stdout.write(f'   Saved to: {result["models_saved_to"]}\n')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error training main model: {e}'))
        
        # Train barangay disease peak model
        if not main_only:
            self.stdout.write(self.style.SUCCESS('\n🧠 Training Barangay Disease Peak Model...'))
            self.stdout.write('   This may take 2-5 minutes...\n')
            
            try:
                result = train_barangay_disease_peak_model(
                    csv_2023_path=csv_2023,
                    csv_2024_path=csv_2024,
                    use_db=use_db
                )
                
                if "error" in result:
                    self.stdout.write(self.style.ERROR(f'❌ Error: {result["error"]}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'✅ Barangay model trained successfully!'))
                    stats = result.get('training_stats', {})
                    self.stdout.write(f'   Barangays: {stats.get("total_barangays", 0)}')
                    self.stdout.write(f'   Models trained: {stats.get("models_trained", 0)}')
                    self.stdout.write(f'   Saved to: {result["models_saved_to"]}\n')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error training barangay model: {e}'))
        
        # Verify models were created
        self.stdout.write(self.style.SUCCESS('\n📋 Verifying saved models...\n'))
        
        if not barangay_only:
            if os.path.exists(main_model_path):
                self.stdout.write(self.style.SUCCESS('✅ Main model file exists'))
            else:
                self.stdout.write(self.style.ERROR('❌ Main model file NOT found'))
        
        if not main_only:
            if os.path.exists(barangay_model_path):
                self.stdout.write(self.style.SUCCESS('✅ Barangay model file exists'))
            else:
                self.stdout.write(self.style.ERROR('❌ Barangay model file NOT found'))
        
        self.stdout.write(self.style.SUCCESS('\n✨ Pre-training complete! Models are ready for fast loading.\n'))
        
        # Pre-generate predictions to warm up cache
        self.stdout.write(self.style.SUCCESS('\n🔮 Pre-generating predictions to warm up cache...\n'))
        try:
            from analytics.ml_utils import predict_disease_forecast_2025_monthly, predict_barangay_disease_peak_2025
            
            # Pre-generate main predictions
            if not barangay_only and main_exists:
                self.stdout.write('   Generating main disease predictions...')
                main_result = predict_disease_forecast_2025_monthly()
                if "error" not in main_result:
                    self.stdout.write(self.style.SUCCESS('   ✅ Main predictions cached'))
                else:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  {main_result.get("error", "Unknown error")}'))
            
            # Pre-generate barangay predictions
            if not main_only and barangay_exists:
                self.stdout.write('   Generating barangay predictions...')
                barangay_result = predict_barangay_disease_peak_2025(use_db=use_db)
                if "error" not in barangay_result:
                    self.stdout.write(self.style.SUCCESS('   ✅ Barangay predictions cached'))
                else:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  {barangay_result.get("error", "Unknown error")}'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   ⚠️  Could not pre-generate predictions: {e}'))
            self.stdout.write('   You can run "python manage.py pre_generate_predictions" separately')
        
        self.stdout.write(self.style.SUCCESS('\n💡 Tip: Page loads will now be <1 second instead of 2-6 minutes!\n'))

