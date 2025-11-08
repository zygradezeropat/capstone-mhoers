import joblib
import os
from django.core.cache import cache
from django.conf import settings
from .ml_utils import (
    train_random_forest_model_classification,
    train_time_prediction_model_advanced_from_csv,
    train_disease_peak_prediction_model,
    get_ml_models_path
)

class MLModelManager:
    """Manages loading and caching of ML models"""
    
    CACHE_KEYS = {
        'disease_model': 'ml_disease_model',
        'disease_vectorizer': 'ml_disease_vectorizer', 
        'time_model': 'ml_time_model',
        'time_vectorizer': 'ml_time_vectorizer'
    }
    
    @classmethod
    def load_models(cls):
        """Load all models and cache them"""
        try:
            models_dir = get_ml_models_path()

            disease_model = joblib.load(os.path.join(models_dir, 'disease_rf_model.pkl'))
            disease_vectorizer = joblib.load(os.path.join(models_dir, 'disease_vectorizer.pkl'))

            time_model = None
            for candidate in ['time_prediction_model_advanced.pkl', 'time_gb_model.pkl', 'time_rf_model.pkl']:
                candidate_path = os.path.join(models_dir, candidate)
                if os.path.exists(candidate_path):
                    time_model = joblib.load(candidate_path)
                    break

            time_vectorizer = None
            for candidate in ['time_vectorizer_advanced.pkl', 'symptom_vectorizer.pkl']:
                candidate_path = os.path.join(models_dir, candidate)
                if os.path.exists(candidate_path):
                    time_vectorizer = joblib.load(candidate_path)
                    break

            cache.set(cls.CACHE_KEYS['disease_model'], disease_model, 3600)
            cache.set(cls.CACHE_KEYS['disease_vectorizer'], disease_vectorizer, 3600)
            if time_model is not None:
                cache.set(cls.CACHE_KEYS['time_model'], time_model, 3600)
            if time_vectorizer is not None:
                cache.set(cls.CACHE_KEYS['time_vectorizer'], time_vectorizer, 3600)

            return True
        except Exception as e:
            print(f"Error loading models: {e}")
            return False
    
    @classmethod
    def get_models(cls):
        """Get cached models or load them if not cached"""
        models = {}
        
        for key, cache_key in cls.CACHE_KEYS.items():
            model = cache.get(cache_key)
            if model is None:
                # Models not in cache, load them
                cls.load_models()
                model = cache.get(cache_key)
            models[key] = model
            
        return models
    
    @classmethod
    def train_models_if_needed(cls):
        """Train models only if they don't exist"""
        models_dir = get_ml_models_path()
        disease_files = [
            os.path.join(models_dir, 'disease_rf_model.pkl'),
            os.path.join(models_dir, 'disease_vectorizer.pkl')
        ]
        time_model_candidates = [
            os.path.join(models_dir, name)
            for name in ['time_prediction_model_advanced.pkl', 'time_gb_model.pkl', 'time_rf_model.pkl']
        ]
        time_vectorizer_candidates = [
            os.path.join(models_dir, name)
            for name in ['time_vectorizer_advanced.pkl', 'symptom_vectorizer.pkl']
        ]
        disease_peak_files = [
            os.path.join(models_dir, 'disease_peak_model.pkl'),
            os.path.join(models_dir, 'disease_peak_tfidf.pkl'),
            os.path.join(models_dir, 'disease_peak_scaler.pkl'),
            os.path.join(models_dir, 'disease_peak_encoder.pkl'),
            os.path.join(models_dir, 'disease_peak_metadata.pkl')
        ]

        missing = [path for path in disease_files if not os.path.exists(path)]
        if not any(os.path.exists(path) for path in time_model_candidates):
            missing.append('time_model')
        if not any(os.path.exists(path) for path in time_vectorizer_candidates):
            missing.append('time_vectorizer')
        if not all(os.path.exists(path) for path in disease_peak_files):
            missing.append('disease_peak_model')

        if missing:
            print("Training missing models...")
            disease_result = train_random_forest_model_classification()
            if isinstance(disease_result, dict) and disease_result.get('error'):
                print(f"Error training disease model: {disease_result['error']}")
            # Use CSV-based time training (creates advanced model files)
            time_result = train_time_prediction_model_advanced_from_csv(csv_path=None)
            if isinstance(time_result, dict) and time_result.get('error'):
                print(f"Error training time model: {time_result['error']}")
            # Train disease peak model
            peak_result = train_disease_peak_prediction_model(
                csv_2023_path=None,
                csv_2024_path=None,
                use_db=False,
                top_n=5
            )
            if isinstance(peak_result, dict) and peak_result.get('error'):
                print(f"Error training disease peak model: {peak_result['error']}")
            return True
        return False
