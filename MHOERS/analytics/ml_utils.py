import pandas as pd
import numpy as np
import os
import joblib

from sklearn.linear_model import LinearRegression
from referrals.models import Referral 
from analytics.models import Disease
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score



def train_random_forest_model_classification():
    """
    Train a Random Forest classifier using the Disease model's symptoms.
    Saves the model and vectorizer to disk.
    """
    # Load diseases
    diseases = Disease.objects.all()
    if not diseases.exists():
        return {"error": "No disease records found."}

    # Prepare training data
    X_train = [d.symptoms for d in diseases]
    y_train = [d.name for d in diseases]

    # Vectorize symptoms
    vectorizer = CountVectorizer()
    X_vectors = vectorizer.fit_transform(X_train)

    # Train Random Forest model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_vectors, y_train)

    # Save model and vectorizer
    joblib.dump(model, 'ml_models/disease_rf_model.pkl')
    joblib.dump(vectorizer, 'ml_models/disease_vectorizer.pkl')

    return {"status": "Training completed", "num_diseases": len(y_train)}


def predict_disease_for_referral(referral_id):
    """
    Predict the most likely disease for a given referral using saved model.
    Args:
        referral_id (int): ID of the referral to classify.
    Returns:
        str: Predicted disease name or error message.
    """
    try:
        # Load saved model & vectorizer
        model = joblib.load('ml_models/disease_rf_model.pkl')
        vectorizer = joblib.load('ml_models/disease_vectorizer.pkl')
    except Exception as e:
        return f"Error loading model/vectorizer: {e}"

    try:
        # Fetch referral data
        referral = Referral.objects.get(referral_id=referral_id)
    except Referral.DoesNotExist:
        return "Referral not found"

    # Vectorize the symptoms
    input_symptoms = [referral.symptoms or ""]
    input_vector = vectorizer.transform(input_symptoms)

    # Predict disease
    prediction = model.predict(input_vector)
    return prediction[0]

    
def time_completed(referral_id):
    referral = Referral.objects.get(referral_id=referral_id)
    referral_complete = (referral.created_at - referral.completed_at).total_seconds() / 60
    
    return referral_complete
    

def random_forest_regression_train_model():
    """
    Train a Random Forest Regression model to predict how long it will take to complete a referral.
    Uses various features from the referral data to make predictions.
    Returns:
        model: Trained Random Forest Regression model
    """
    "Trained Data here"
    
    referrals = Referral.objects.filter(status='completed').exclude(completed_at=None)
    
    data = []
    
    for r in referrals:
        try:
            time_to_cater = (r.completed_at - r.created_at).total_seconds() / 3600
            
            data.append({
                'weight': float(r.weight),
                'height': float(r.height),
                'bp_systolic': r.bp_systolic,
                'bp_diastolic': r.bp_diastolic,
                'pulse_rate': r.pulse_rate,
                'respiratory_rate': r.respiratory_rate,
                'temperature': float(r.temperature),
                'oxygen_saturation': r.oxygen_saturation,
                'symptoms': r.symptoms or '',
                'time_to_cater': time_to_cater
            })
        except:
            continue  # Skip records with bad data
        
    if not data:
        return {"error": "No valid completed referrals found."}
    
    df = pd.DataFrame(data)
    
    # preprocess the data
    time_vectorizer = TfidfVectorizer(max_features=50)
    symptoms_vectors = time_vectorizer.fit_transform(df["symptoms"]).toarray()
    
    X_numeric = df[['weight', 'height', 'bp_systolic', 'bp_diastolic', 'pulse_rate',
                    'respiratory_rate', 'temperature', 'oxygen_saturation']].reset_index(drop=True)
    
    X = pd.concat([X_numeric, pd.DataFrame(symptoms_vectors)], axis=1)
    X.columns = X.columns.astype(str)
    y = df['time_to_cater']
    
    #split the data and train 
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    
    #evaluate the model
    y_pred = model.predict(X_test)
    metrics = {
        "MAE": round(mean_absolute_error(y_test, y_pred), 2),
        "R2_Score": round(r2_score(y_test, y_pred), 2)
    }

    # save the model
    os.makedirs('ml_models', exist_ok=True)
    joblib.dump(model, 'ml_models/time_rf_model.pkl')
    joblib.dump(time_vectorizer, 'ml_models/symptom_vectorizer.pkl')
    
    
    return {"status": "Training completed", **metrics}

def random_forest_regression_prediction_time(referral, model=None, vectorizer=None):
    import joblib
    import pandas as pd

    if model is None:
        model = joblib.load('ml_models/time_rf_model.pkl')
    if vectorizer is None:
        vectorizer = joblib.load('ml_models/symptom_vectorizer.pkl')

    try:
        numeric_features = {
            'weight': float(referral.weight),
            'height': float(referral.height),
            'bp_systolic': referral.bp_systolic,
            'bp_diastolic': referral.bp_diastolic,
            'pulse_rate': referral.pulse_rate,
            'respiratory_rate': referral.respiratory_rate,
            'temperature': float(referral.temperature),
            'oxygen_saturation': referral.oxygen_saturation,
        }

        symptoms_text = referral.symptoms or ''
        symptoms_vector = vectorizer.transform([symptoms_text]).toarray()

        X_numeric = pd.DataFrame([numeric_features])
        X_combined = pd.concat([X_numeric, pd.DataFrame(symptoms_vector)], axis=1)
        X_combined.columns = X_combined.columns.astype(str)

        prediction = model.predict(X_combined)
        return round(float(prediction[0]), 2)

    except Exception as e:
        return f"Prediction error: {e}"