"""
Django Management Command: Disease Peak Analytics for 2025
Predicts monthly disease trend spikes based on 2023-2024 historical data.
Uses saved models trained by train_ml_models command.
"""
import pandas as pd
import random
import os
from django.core.management.base import BaseCommand
from django.db.models import Q

from referrals.models import Referral
from analytics.ml_utils import (
    get_ml_models_path,
    load_disease_peak_csv_data,
    queryset_to_disease_peak_dataframe
)


class Command(BaseCommand):
    help = 'Predict 2025 monthly disease trends based on 2023-2024 historical referral data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--samples-per-month',
            type=int,
            default=100,
            help='Number of simulated samples per month for 2025 prediction (default: 100)',
        )
        parser.add_argument(
            '--use-db',
            action='store_true',
            help='Use Django database instead of CSV files for simulation data',
        )
        parser.add_argument(
            '--csv-2023',
            type=str,
            default=None,
            help='Path to 2023 CSV file for simulation (default: sample_datasets/New_Corella_datasets_2023.csv)',
        )
        parser.add_argument(
            '--csv-2024',
            type=str,
            default=None,
            help='Path to 2024 CSV file for simulation (default: sample_datasets/New_corella_datasets_5.csv)',
        )

    def handle(self, *args, **options):
        import joblib
        from scipy.sparse import hstack
        
        self.stdout.write(self.style.SUCCESS(
            '\n======================================================\n'
            '📘 Disease Peak Analytics — Predicting 2025 Monthly Disease Trends\n'
            '======================================================\n'
        ))
        
        samples_per_month = options['samples_per_month']
        use_db = options['use_db']
        csv_2023 = options['csv_2023']
        csv_2024 = options['csv_2024']
        
        # Step 1: Load saved model and preprocessing components
        self.stdout.write('📦 Loading saved disease peak prediction model...')
        models_dir = get_ml_models_path()
        model_path = os.path.join(models_dir, 'disease_peak_model.pkl')
        tfidf_path = os.path.join(models_dir, 'disease_peak_tfidf.pkl')
        scaler_path = os.path.join(models_dir, 'disease_peak_scaler.pkl')
        encoder_path = os.path.join(models_dir, 'disease_peak_encoder.pkl')
        metadata_path = os.path.join(models_dir, 'disease_peak_metadata.pkl')
        
        if not all(os.path.exists(p) for p in [model_path, tfidf_path, scaler_path, encoder_path, metadata_path]):
            self.stdout.write(self.style.ERROR(
                '❌ Disease peak model not found. Please run: python manage.py train_ml_models'
            ))
            return
        
        try:
            model = joblib.load(model_path)
            tfidf = joblib.load(tfidf_path)
            scaler = joblib.load(scaler_path)
            target_encoder = joblib.load(encoder_path)
            metadata = joblib.load(metadata_path)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error loading model: {e}'))
            return
        
        numeric_features = metadata['numeric_features']
        text_features = metadata['text_features']
        allowed_diseases = metadata.get('allowed_diseases', [])
        best_model_name = metadata.get('best_model_name', 'Unknown')
        
        self.stdout.write(f'✅ Model loaded: {best_model_name}')
        self.stdout.write(f'   Top diseases: {allowed_diseases}')
        
        # Step 2: Load historical data for simulation
        self.stdout.write('\n📊 Loading historical data for simulation...')
        if use_db:
            referrals_2023_2024 = Referral.objects.filter(
                created_at__year__in=[2023, 2024]
            ).exclude(
                Q(patient__isnull=True) | 
                Q(initial_diagnosis__isnull=True) | 
                Q(initial_diagnosis='')
            )
            
            if not referrals_2023_2024.exists():
                self.stdout.write(self.style.ERROR(
                    '❌ No referral data found for 2023-2024. Please ensure data exists.'
                ))
                return
            
            original_df = queryset_to_disease_peak_dataframe(referrals_2023_2024)
            self.stdout.write(f'✅ Loaded {len(original_df)} referral records from database')
        else:
            try:
                original_df = load_disease_peak_csv_data(csv_2023, csv_2024)
                self.stdout.write(f'✅ Loaded {len(original_df)} total records from CSV files')
            except FileNotFoundError as e:
                self.stdout.write(self.style.ERROR(f'❌ {e}'))
                return
        
        # Step 3: Simulate 2025 monthly data
        self.stdout.write('\n🗓️ Simulating 2025 monthly disease predictions...')
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        
        self.stdout.write('   📊 Extracting patterns from historical data...')
        
        # Prepare data for sampling
        sample_columns = ['AGE', 'SEX', 'COMPLAINTS']
        available_columns = [col for col in sample_columns if col in original_df.columns]
        
        if len(available_columns) < len(sample_columns):
            self.stdout.write(self.style.WARNING(
                f'   ⚠️  Some columns missing: {set(sample_columns) - set(available_columns)}'
            ))
        
        sampling_df = original_df[available_columns].dropna(subset=available_columns)
        
        if len(sampling_df) == 0:
            self.stdout.write(self.style.ERROR('   ❌ No valid data for sampling'))
            return
        
        self.stdout.write(f'   ✅ Using {len(sampling_df)} records for pattern extraction')
        
        # Generate simulated data
        total_samples_needed = len(months) * samples_per_month
        sampled_data = sampling_df.sample(
            n=min(total_samples_needed, len(sampling_df)), 
            replace=True if total_samples_needed > len(sampling_df) else False,
            random_state=42
        )
        
        # Assign months to sampled data
        month_assignments = []
        for month in months:
            month_assignments.extend([month] * samples_per_month)
        
        sim_df = sampled_data.head(total_samples_needed).copy()
        sim_df['Month'] = month_assignments[:len(sim_df)]
        
        # Ensure all required columns exist
        for col in sample_columns:
            if col not in sim_df.columns:
                if col == 'AGE':
                    sim_df[col] = random.randint(1, 90)
                elif col == 'SEX':
                    sim_df[col] = random.choice(["Male", "Female"])
                else:
                    sim_df[col] = ''
        
        # Apply same feature engineering as training data
        self.stdout.write('   🔨 Engineering features for simulated data...')
        sim_df['COMPLAINTS'] = sim_df['COMPLAINTS'].fillna('').astype(str).str.strip()
        sim_df['COMPLAINTS_CLEAN'] = sim_df['COMPLAINTS'].str.lower()
        sim_df['COMPLAINTS_LENGTH'] = sim_df['COMPLAINTS'].str.len()
        sim_df['COMPLAINTS_WORD_COUNT'] = sim_df['COMPLAINTS'].str.split().str.len()
        sim_df['COMPLAINTS_AVG_WORD_LENGTH'] = sim_df['COMPLAINTS_LENGTH'] / (sim_df['COMPLAINTS_WORD_COUNT'] + 1)
        
        sim_df['AGE'] = pd.to_numeric(sim_df['AGE'], errors='coerce')
        sim_df['AGE'] = sim_df['AGE'].fillna(original_df['AGE'].median() if 'AGE' in original_df.columns else 30)
        sim_df['AGE_GROUP'] = pd.cut(sim_df['AGE'], bins=[0, 18, 35, 50, 65, 100], 
                                     labels=[0, 1, 2, 3, 4], include_lowest=True).astype(int)
        age_mean = original_df['AGE'].mean() if 'AGE' in original_df.columns else 30
        age_std = original_df['AGE'].std() if 'AGE' in original_df.columns else 15
        sim_df['AGE_NORMALIZED'] = (sim_df['AGE'] - age_mean) / (age_std + 1e-8)
        
        sim_df['SEX'] = sim_df['SEX'].astype(str).str.strip().str.upper()
        sim_df['SEX_ENCODED'] = sim_df['SEX'].map({'M': 0, 'MALE': 0, 'F': 1, 'FEMALE': 1}).fillna(0)
        
        # Fill NaN
        sim_df['COMPLAINTS_LENGTH'] = sim_df['COMPLAINTS_LENGTH'].fillna(0)
        sim_df['COMPLAINTS_WORD_COUNT'] = sim_df['COMPLAINTS_WORD_COUNT'].fillna(0)
        sim_df['COMPLAINTS_AVG_WORD_LENGTH'] = sim_df['COMPLAINTS_AVG_WORD_LENGTH'].fillna(0)
        
        # Prepare features for prediction
        sim_numeric = sim_df[numeric_features].values
        sim_numeric_scaled = scaler.transform(sim_numeric)
        sim_text = tfidf.transform(sim_df[text_features[0]])
        
        # Combine features
        sim_combined = hstack([sim_numeric_scaled, sim_text])
        
        # Predict diseases
        sim_df["Predicted_Disease_Encoded"] = model.predict(sim_combined)
        
        # Map back to disease labels
        reverse_encoder = {i: label for i, label in enumerate(target_encoder.classes_)}
        sim_df["Predicted_Disease_Label"] = sim_df["Predicted_Disease_Encoded"].map(reverse_encoder)
        
        # Step 4: Identify disease peaks per month
        peak_diseases = (
            sim_df.groupby(["Month", "Predicted_Disease_Label"])
            .size()
            .reset_index(name="Count")
            .sort_values(["Month", "Count"], ascending=[True, False])
        )
        
        # Extract top 1 disease per month
        peak_disease_per_month = peak_diseases.groupby("Month").first().reset_index()
        
        self.stdout.write(self.style.SUCCESS('\n📅 Predicted Disease Peaks for 2025:'))
        self.stdout.write(peak_disease_per_month.to_string(index=False))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Analysis complete!'))

