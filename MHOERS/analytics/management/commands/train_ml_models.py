from django.core.management.base import BaseCommand
from analytics.model_manager import MLModelManager
from analytics.ml_utils import (
    train_random_forest_model_classification,
    train_time_prediction_model_advanced_from_csv,
    train_disease_peak_prediction_model
)

class Command(BaseCommand):
    help = 'Train and save ML models for disease, time, and disease peak prediction'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force retraining even if models exist',
        )
        parser.add_argument(
            '--csv-path',
            type=str,
            default=None,
            help='Path to CSV file for time model (default: sample_datasets/New_corella_datasets_5.csv)',
        )
        parser.add_argument(
            '--disease-peak-top-n',
            type=int,
            default=5,
            help='Number of top diseases for peak prediction (default: 5)',
        )
        parser.add_argument(
            '--use-db',
            action='store_true',
            help='Use Django database for disease peak model instead of CSV',
        )
    
    def handle(self, *args, **options):
        
        if options['force'] or MLModelManager.train_models_if_needed():
            try:
                # Train disease classification model
                self.stdout.write('📊 Training disease classification model...')
                disease_result = train_random_forest_model_classification()
                
                if isinstance(disease_result, dict) and disease_result.get('error'):
                    self.stdout.write(
                        self.style.ERROR(f'❌ Disease model training failed: {disease_result["error"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Disease model trained successfully!')
                    )
                   
                
                self.stdout.write('')
                
                # Train time prediction model from CSV
                self.stdout.write('⏱Training time prediction model from CSV...')
                csv_path = options.get('csv_path', None)
                time_result = train_time_prediction_model_advanced_from_csv(csv_path=csv_path)
                
                if isinstance(time_result, dict) and time_result.get('error'):
                    self.stdout.write(
                        self.style.ERROR(f'❌ Time model training failed: {time_result["error"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Time model trained successfully!')
                    )
                    if isinstance(time_result, dict):
                        self.stdout.write(f'   Status: {time_result.get("status", "N/A")}')
                
                self.stdout.write('')
                
                # Train disease peak prediction model
                self.stdout.write('📈 Training disease peak prediction model...')
                top_n = options.get('disease_peak_top_n', 5)
                use_db = options.get('use_db', False)
                peak_result = train_disease_peak_prediction_model(
                    csv_2023_path=None,
                    csv_2024_path=None,
                    use_db=use_db,
                    top_n=top_n
                )
                
                if isinstance(peak_result, dict) and peak_result.get('error'):
                    self.stdout.write(
                        self.style.ERROR(f'❌ Disease peak model training failed: {peak_result["error"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Disease peak model trained successfully!')
                    )
                    if isinstance(peak_result, dict):
                        self.stdout.write(f'   Best Model: {peak_result.get("best_model", "N/A")}')
                        self.stdout.write(f'   Accuracy: {peak_result.get("accuracy", "N/A")}')
                        self.stdout.write(f'   Top Diseases: {peak_result.get("top_diseases", [])}')
                
                self.stdout.write('')
                
                # Load models into cache
                MLModelManager.load_models()
                
                self.stdout.write(
                    self.style.SUCCESS('✅ All models trained and cached successfully!')
                )
                
            except Exception as e:
                self.stdout.write('')
                self.stdout.write(
                    self.style.ERROR(f'❌ Error training models: {e}')
                )
                import traceback
                self.stdout.write(self.style.ERROR(traceback.format_exc()))
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ Models already exist. Use --force to retrain.')
            )
