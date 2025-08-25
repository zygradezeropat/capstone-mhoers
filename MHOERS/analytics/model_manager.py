import joblib
import os
from django.core.cache import cache
from django.conf import settings
from .ml_utils import train_random_forest_model_classification, random_forest_regression_train_model

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
            # Load disease prediction models
            disease_model = joblib.load('ml_models/disease_rf_model.pkl')
            disease_vectorizer = joblib.load('ml_models/disease_vectorizer.pkl')
            
            # Load time prediction models
            time_model = joblib.load('ml_models/time_rf_model.pkl')
            time_vectorizer = joblib.load('ml_models/symptom_vectorizer.pkl')
            
            # Cache models for 1 hour
            cache.set(cls.CACHE_KEYS['disease_model'], disease_model, 3600)
            cache.set(cls.CACHE_KEYS['disease_vectorizer'], disease_vectorizer, 3600)
            cache.set(cls.CACHE_KEYS['time_model'], time_model, 3600)
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
        model_files = [
            'ml_models/disease_rf_model.pkl',
            'ml_models/disease_vectorizer.pkl',
            'ml_models/time_rf_model.pkl', 
            'ml_models/symptom_vectorizer.pkl'
        ]
        
        missing_models = [f for f in model_files if not os.path.exists(f)]
        
        if missing_models:
            print("Training missing models...")
            train_random_forest_model_classification()
            random_forest_regression_train_model()
            return True
        return False
