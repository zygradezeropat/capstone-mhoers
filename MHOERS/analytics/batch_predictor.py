import pandas as pd
import numpy as np
from django.core.cache import cache
from .model_manager import MLModelManager
from .ml_utils import build_disease_feature_frame, format_icd_prediction

def normalize_disease_prediction(prediction):
    """Normalize disease predictions, converting 'N' to 'Unspecified'"""
    if not prediction:
        return "No prediction"
    pred_str = str(prediction).strip()
    if pred_str.upper() == 'N' or pred_str == 'n':
        return "Unspecified"
    return pred_str

class BatchPredictor:
    """Handles batch predictions for multiple referrals"""
    
    @classmethod
    def predict_diseases_batch(cls, referrals):
        """Predict diseases for multiple referrals at once with confidence threshold"""
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
            prediction_probas = disease_model.predict_proba(feature_df)
            allowed_codes = metadata.get('allowed_icd', [])
            
            # Confidence threshold: if model is less than 30% confident, return "Unspecified"
            CONFIDENCE_THRESHOLD = 0.3  # 30% minimum confidence required

            formatted = []
            for i, code in enumerate(predictions):
                # Convert to string and normalize "N" predictions to "Unspecified"
                code_str = normalize_disease_prediction(code)
                max_confidence = max(prediction_probas[i])
                
                # If already normalized to "Unspecified", skip other checks
                if code_str == "Unspecified":
                    formatted.append(code_str)
                # Special handling for T14.1 - require BOTH high confidence AND wound keywords
                elif code_str == 'T14.1':
                    complaint_text = (referrals[i].chief_complaint or referrals[i].symptoms or '').lower()
                    wound_keywords = ['wound', 'cut', 'laceration', 'injury', 'trauma', 'bleeding', 
                                     'sugat', 'tusok', 'galos', 'hiwa', 'open wound', 'puncture']
                    has_wound_keyword = any(keyword in complaint_text for keyword in wound_keywords)
                    
                    # If confidence is below 50% OR no wound keywords, return "Unspecified"
                    # This ensures T14.1 is only returned when we're confident AND it's actually wound-related
                    if max_confidence < 0.5 or not has_wound_keyword:
                        formatted.append("Unspecified")
                    else:
                        formatted.append(code_str)
                # Check confidence for this prediction
                elif max_confidence < CONFIDENCE_THRESHOLD:
                    formatted.append("Unspecified")
                elif allowed_codes and code_str not in allowed_codes:
                    formatted.append("Unspecified")
                else:
                    formatted.append(code_str)

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
                    # Handle missing values with defaults
                    numeric_data.append({
                        'weight': float(r.weight) if r.weight else 70.0,  # Default 70 kg
                        'height': float(r.height) if r.height else 170.0,  # Default 170 cm
                        'bp_systolic': r.bp_systolic if r.bp_systolic else 120,
                        'bp_diastolic': r.bp_diastolic if r.bp_diastolic else 80,
                        'pulse_rate': r.pulse_rate if r.pulse_rate else 72,
                        'respiratory_rate': r.respiratory_rate if r.respiratory_rate else 18,
                        'temperature': float(r.temperature) if r.temperature else 37.0,
                        'oxygen_saturation': r.oxygen_saturation if r.oxygen_saturation else 98
                    })
                    text_data.append(r.symptoms or r.chief_complaint or '')
                    valid_referrals.append(r)
                except (ValueError, TypeError, AttributeError) as e:
                    # Log error but continue with other referrals
                    print(f"Error processing referral {r.referral_id} for time prediction: {e}")
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
        
        # If cached, normalize any "N" values before returning
        if cached_predictions:
            normalized_cache = {}
            for ref_id, (disease, time_pred) in cached_predictions.items():
                normalized_disease = normalize_disease_prediction(disease)
                normalized_cache[ref_id] = (normalized_disease, time_pred)
            return normalized_cache
        
        disease_predictions = cls.predict_diseases_batch(referrals)
        time_predictions = cls.predict_times_batch(referrals)
        
        # Combine predictions and normalize any "N" values
        combined_predictions = {}
        for r in referrals:
            disease = disease_predictions.get(r.referral_id, "No prediction")
            # Additional normalization check in case "N" slipped through
            disease = normalize_disease_prediction(disease)
            time_pred = time_predictions.get(r.referral_id, "N/A")
            combined_predictions[r.referral_id] = (disease, time_pred)
        
        # Cache for 5 minutes
        cache.set(cache_key, combined_predictions, 300)
        
        return combined_predictions
