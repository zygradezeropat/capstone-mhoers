from django.core.management.base import BaseCommand
from analytics.model_manager import MLModelManager
from analytics.ml_utils import train_random_forest_model_classification, random_forest_regression_train_model

class Command(BaseCommand):
    help = 'Train and save ML models for disease and time prediction'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force retraining even if models exist',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Starting ML model training...')
        
        if options['force'] or MLModelManager.train_models_if_needed():
            try:
                # Train disease classification model
                self.stdout.write('Training disease classification model...')
                disease_result = train_random_forest_model_classification()
                self.stdout.write(f'Disease model: {disease_result}')
                
                # Train time prediction model
                self.stdout.write('Training time prediction model...')
                time_result = random_forest_regression_train_model()
                self.stdout.write(f'Time model: {time_result}')
                
                # Load models into cache
                self.stdout.write('Loading models into cache...')
                MLModelManager.load_models()
                
                self.stdout.write(
                    self.style.SUCCESS('ML models trained and cached successfully!')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error training models: {e}')
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('Models already exist. Use --force to retrain.')
            )
