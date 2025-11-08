from django.core.management.base import BaseCommand
from analytics import ml_utils


class Command(BaseCommand):
    help = "Retrain GradientBoostingRegressor for time-to-cater and save artifacts"

    def handle(self, *args, **options):
        try:
            result = ml_utils.gradient_boosting_regression_train_model()
            self.stdout.write(self.style.SUCCESS(f"Training done: {result}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Training failed: {e}"))
            raise


