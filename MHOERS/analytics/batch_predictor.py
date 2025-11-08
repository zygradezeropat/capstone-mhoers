import pandas as pd
import numpy as np
from django.core.cache import cache
from .model_manager import MLModelManager
from .ml_utils import build_disease_feature_frame, format_icd_prediction

class BatchPredictor:
    """Handles batch predictions for multiple referrals"""
    
    @classmethod
    def predict_diseases_batch(cls, referrals):
        """Predict diseases for multiple referrals at once"""
        try:
            models = MLModelManager.get_models()
            disease_model = models.get('disease_model')
            metadata = models.get('disease_vectorizer')
            if disease_model is None or metadata is None:
                return {}

            feature_df = build_disease_feature_frame(referrals, metadata)
            if feature_df.empty:
                return {}

            predictions = disease_model.predict(feature_df)
            allowed_codes = metadata.get('allowed_icd', [])

            formatted = []
            for code in predictions:
                if allowed_codes and code not in allowed_codes:
                    formatted.append("Unspecified")
                else:
                    formatted.append(code)

            return dict(zip([r.referral_id for r in referrals], formatted))
            
        except Exception as e:
            print(f"Error in batch disease prediction: {e}")
            return {}
    
    @classmethod
    def predict_times_batch(cls, referrals):
        """Predict completion times for multiple referrals at once"""
        try:
            models = MLModelManager.get_models()
            time_model = models.get('time_model')
            time_vectorizer = models.get('time_vectorizer')

            if time_model is None or time_vectorizer is None:
                return {}
            
            # Prepare data for all referrals
            numeric_data = []
            text_data = []
            valid_referrals = []
            
            for r in referrals:
                try:
                    numeric_data.append({
                        'weight': float(r.weight),
                        'height': float(r.height),
                        'bp_systolic': r.bp_systolic,
                        'bp_diastolic': r.bp_diastolic,
                        'pulse_rate': r.pulse_rate,
                        'respiratory_rate': r.respiratory_rate,
                        'temperature': float(r.temperature),
                        'oxygen_saturation': r.oxygen_saturation
                    })
                    text_data.append(r.symptoms or '')
                    valid_referrals.append(r)
                except:
                    continue
            
            if not valid_referrals:
                return {}
            
            # Create DataFrame
            X_numeric = pd.DataFrame(numeric_data)
            X_text = time_vectorizer.transform(text_data).toarray()
            X_combined = pd.concat([X_numeric.reset_index(drop=True), pd.DataFrame(X_text)], axis=1)
            X_combined.columns = X_combined.columns.astype(str)
            
            # Predict all times at once (model outputs hours)
            time_predictions = time_model.predict(X_combined)
            
            # Create results dictionary
            results = {}
            for i, r in enumerate(valid_referrals):
                hours = float(time_predictions[i])
                minutes = round(hours * 60, 0)
                results[r.referral_id] = minutes
            
            return results
            
        except Exception as e:
            print(f"Error in batch time prediction: {e}")
            return {}
    
    @classmethod
    def predict_all_batch(cls, referrals):
        """Predict both disease and time for all referrals"""
        cache_key = f"predictions_batch_{len(referrals)}"
        cached_predictions = cache.get(cache_key)
        
        if cached_predictions:
            return cached_predictions
        
        disease_predictions = cls.predict_diseases_batch(referrals)
        time_predictions = cls.predict_times_batch(referrals)
        
        # Combine predictions
        combined_predictions = {}
        for r in referrals:
            disease = disease_predictions.get(r.referral_id, "No prediction")
            time_pred = time_predictions.get(r.referral_id, "N/A")
            combined_predictions[r.referral_id] = (disease, time_pred)
        
        # Cache for 5 minutes
        cache.set(cache_key, combined_predictions, 300)
        
        return combined_predictions
