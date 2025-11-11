import pandas as pd
import numpy as np
import os
import joblib
import re
import scipy

from referrals.models import Referral 
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder, MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, accuracy_score, f1_score
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.conf import settings

# Medical keywords for advanced time prediction
MEDICAL_KEYWORDS = ['fever', 'cough', 'pain', 'headache', 'dizziness', 'nausea',
                   'vomiting', 'diarrhea', 'rash', 'bleeding', 'swelling',
                   'chest', 'breathing', 'difficulty', 'stomach', 'abdominal',
                   'throat', 'nose', 'ear', 'eye', 'back', 'joint', 'muscle',
                   'tired', 'weak', 'chills', 'sweat', 'cold', 'hot', 'burning']

# Medical synonyms for text preprocessing
MEDICAL_SYNONYMS = {
    r'\bfever\b': 'fever', r'\bhigh temp\b': 'fever', r'\btemp\b': 'fever',
    r'\bcough\b': 'cough', r'\bheadache\b': 'headache', r'\bhead ache\b': 'headache',
    r'\bpain\b': 'pain', r'\bache\b': 'pain', r'\bdizzy\b': 'dizziness',
    r'\bdizziness\b': 'dizziness', r'\bnausea\b': 'nausea', r'\bvomit\b': 'vomiting',
    r'\bvomiting\b': 'vomiting',
}

ALLOWED_ICD_CODES = ['T14.1', 'W54.99', 'J06.9', 'J15', 'I10.1']

COMPLAINT_TRANSLATIONS = {
    'ubo': 'cough',
    'sipon': 'cold',
    'hilana': 'fever',
    'lagnat': 'fever',
    'hilanat': 'fever',
    'kalintura': 'fever',
    'sakit': 'pain',
    'labad': 'headache',
    'tiyan': 'stomach',
    'ulo': 'head',
    'toi': 'toilet',
    'poi': 'point_of_injury',
    'point of injury': 'point_of_injury',
    'bp': 'blood_pressure',
    'dogbite': 'dog_bite',
    'dog bite': 'dog_bite',
    'catbite': 'cat_bite',
    'cat bite': 'cat_bite',
    'iro': 'dog',
    'aso': 'dog',
    'iring': 'cat',
    'paak': 'bite',
    'samad': 'wound',
    'nasamad': 'wound',
    'suka': 'vomit'
}

COMPLAINT_STOPWORDS = [
    'day', 'x', 'tab', 'cert', 'maintenance', 'w', 'ug', 'pt',
    'soap', 'water', 'med', 'taken', 'check', 'week', 'month'
]

NO_COMPLAINT_TOKEN = '__no_symptom__'

SEX_NORMALIZATION = {
    'M': 'M',
    'MALE': 'M',
    'F': 'F',
    'FEMALE': 'F'
}


def normalize_sex(value):
    if value is None:
        return 'Unknown'
    normalized = str(value).strip().upper()
    if not normalized:
        return 'Unknown'
    return SEX_NORMALIZATION.get(normalized, normalized if normalized in {'M', 'F'} else 'Unknown')


def clean_and_tokenize_complaints(text, translations=None, stopwords=None):
    if pd.isna(text):
        text = ''
    translations = translations or COMPLAINT_TRANSLATIONS
    stopwords = set(stopwords or COMPLAINT_STOPWORDS)
    cleaned = str(text).lower()
    cleaned = re.sub(r'[^a-z\s]', ' ', cleaned)
    for source, target in translations.items():
        cleaned = cleaned.replace(source, target)
    return [word for word in cleaned.split() if word and word not in stopwords and len(word) > 1]


def _prepare_complaint_tokens(tokens, mlb, fallback_token):
    if not isinstance(tokens, (list, tuple)):
        tokens = []
    filtered = [token for token in tokens if token in getattr(mlb, 'classes_', [])]
    if not filtered:
        filtered = [fallback_token]
    return filtered


def build_disease_feature_frame(referrals, metadata):
    if not referrals or metadata is None:
        return pd.DataFrame()

    mlb = metadata.get('mlb')
    if mlb is None:
        return pd.DataFrame()

    translations = metadata.get('translations') or COMPLAINT_TRANSLATIONS
    stopwords = metadata.get('stopwords') or COMPLAINT_STOPWORDS
    fallback_token = metadata.get('fallback_token', NO_COMPLAINT_TOKEN)
    sex_columns = metadata.get('sex_columns', [])
    symptom_columns = metadata.get('symptom_columns')
    mlb_classes = metadata.get('mlb_classes', getattr(mlb, 'classes_', []))
    feature_columns = metadata.get('feature_columns', [])
    default_age = metadata.get('default_age', 30.0)

    rows = []
    tokens_list = []

    for referral in referrals:
        patient = getattr(referral, 'patient', None)
        age = getattr(patient, 'age', None)
        sex = normalize_sex(getattr(patient, 'sex', None))
        text = referral.symptoms or referral.chief_complaint or ''
        tokens = clean_and_tokenize_complaints(text, translations, stopwords)
        tokens = _prepare_complaint_tokens(tokens, mlb, fallback_token)

        rows.append({'AGE': age, 'SEX': sex})
        tokens_list.append(tokens)

    if not rows:
        return pd.DataFrame(columns=feature_columns)

    df = pd.DataFrame(rows)
    df['AGE'] = pd.to_numeric(df['AGE'], errors='coerce').fillna(default_age)

    sex_dummies = pd.get_dummies(df['SEX'], prefix='SEX')
    for column in sex_columns:
        if column not in sex_dummies.columns:
            sex_dummies[column] = 0
    if sex_columns:
        sex_dummies = sex_dummies[sex_columns]

    symptom_matrix = mlb.transform(tokens_list)
    if symptom_columns and len(symptom_columns) == len(mlb_classes):
        symptom_df = pd.DataFrame(symptom_matrix, columns=symptom_columns)
    else:
        symptom_df = pd.DataFrame(symptom_matrix, columns=[f"SYM_{cls}" for cls in mlb_classes])

    feature_frames = [df[['AGE']].reset_index(drop=True)]
    if not sex_dummies.empty:
        feature_frames.append(sex_dummies.reset_index(drop=True))
    feature_frames.append(symptom_df.reset_index(drop=True))

    feature_df = pd.concat(feature_frames, axis=1)
    if feature_columns:
        feature_df = feature_df.reindex(columns=feature_columns, fill_value=0)

    return feature_df.fillna(0).astype(float)


def format_icd_prediction(icd_code, metadata=None):
    if not metadata:
        return icd_code
    mapping = metadata.get('icd_to_label') or {}
    label = mapping.get(icd_code)
    if label and isinstance(label, str):
        return f"{icd_code} - {label}"
    return icd_code

def preprocess_text_advanced(text):
    """Advanced text preprocessing for complaints"""
    if pd.isna(text) or text == '':
        return ''
    text = str(text).lower().strip()
    for pattern, replacement in MEDICAL_SYNONYMS.items():
        text = re.sub(pattern, replacement, text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = ' '.join(text.split())
    return text

def assign_age_group(age):
    """Assign age to group category"""
    if pd.isna(age) or age is None:
        return 2  # Default to Adult
    try:
        age = float(age)
        if age <= 18: return 0  # Child
        elif age <= 35: return 1  # Young Adult
        elif age <= 50: return 2  # Adult
        elif age <= 65: return 3  # Middle-aged
        else: return 4  # Senior
    except:
        return 2


def get_ml_models_path():
    """Get the absolute path to the ml_models directory."""
    base_dir = getattr(settings, 'BASE_DIR', None)
    if base_dir:
        # Handle both Path objects and strings
        if isinstance(base_dir, (str, os.PathLike)):
            models_path = os.path.join(str(base_dir), 'ml_models')
            return os.path.abspath(models_path)
    # Fallback to current directory if BASE_DIR not available
    return os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml_models'))


def train_random_forest_model_classification():
    """Train the ICD-10 classifier using the Corella dataset."""
    dataset_path = os.path.join(
        settings.BASE_DIR,
        'sample_datasets',
        'New_corella_datasets_5.csv'
    )

    if not os.path.exists(dataset_path):
        return {"error": f"Dataset not found at {dataset_path}"}

    df = pd.read_csv(dataset_path, encoding='ISO-8859-1').rename(columns=str.strip)

    required_columns = {'AGE', 'SEX', 'COMPLAINTS', 'ICD10 CODE', 'DIAGNOSIS'}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        missing = ', '.join(sorted(missing_columns))
        return {"error": f"Dataset missing required columns: {missing}"}

    df = df.dropna(subset=['ICD10 CODE'])
    df = df[df['ICD10 CODE'].isin(ALLOWED_ICD_CODES)].copy()
    if df.empty:
        return {"error": "Dataset has no rows after filtering allowed ICD-10 codes."}

    df['AGE'] = pd.to_numeric(df['AGE'], errors='coerce')
    df = df.dropna(subset=['AGE'])
    if df.empty:
        return {"error": "Dataset has no valid age values after cleaning."}

    translations = dict(COMPLAINT_TRANSLATIONS)
    stopwords = list(COMPLAINT_STOPWORDS)
    df['COMPLAINTS_CLEAN'] = (
        df['COMPLAINTS']
        .fillna('')
        .astype(str)
        .apply(lambda text: clean_and_tokenize_complaints(text, translations, stopwords))
        .apply(lambda tokens: tokens if tokens else [NO_COMPLAINT_TOKEN])
    )

    mlb = MultiLabelBinarizer()
    complaint_matrix = mlb.fit_transform(df['COMPLAINTS_CLEAN'])
    mlb_classes = list(mlb.classes_)
    symptom_columns = [f"SYM_{cls}" for cls in mlb_classes]
    symptoms_df = pd.DataFrame(complaint_matrix, columns=symptom_columns)

    df['SEX_NORMALIZED'] = df['SEX'].apply(normalize_sex)
    sex_dummies = pd.get_dummies(df['SEX_NORMALIZED'], prefix='SEX')
    if 'SEX_Unknown' not in sex_dummies.columns:
        sex_dummies['SEX_Unknown'] = 0
    sex_columns = sorted(sex_dummies.columns)
    sex_dummies = sex_dummies[sex_columns]

    feature_frames = [
        df[['AGE']].reset_index(drop=True),
        sex_dummies.reset_index(drop=True),
        symptoms_df.reset_index(drop=True)
    ]
    X = pd.concat(feature_frames, axis=1).fillna(0).astype(float)
    feature_columns = list(X.columns)

    y = df['ICD10 CODE'].astype(str)
    if y.nunique() < 2:
        return {"error": "Need at least two ICD-10 classes to train the classifier."}

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    classifier = GradientBoostingClassifier(n_estimators=200, random_state=42)
    classifier.fit(X_train, y_train)

    y_pred = classifier.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average='macro')

    models_dir = get_ml_models_path()
    os.makedirs(models_dir, exist_ok=True)

    model_path = os.path.join(models_dir, 'disease_rf_model.pkl')
    metadata_path = os.path.join(models_dir, 'disease_vectorizer.pkl')

    joblib.dump(classifier, model_path)

    icd_to_label = (
        df[['ICD10 CODE', 'DIAGNOSIS']]
        .dropna()
        .groupby('ICD10 CODE')['DIAGNOSIS']
        .agg(lambda series: series.mode().iat[0] if not series.mode().empty else series.iloc[0])
        .to_dict()
    )

    metadata = {
        "mlb": mlb,
        "mlb_classes": mlb_classes,
        "symptom_columns": symptom_columns,
        "sex_columns": sex_columns,
        "feature_columns": feature_columns,
        "translations": translations,
        "stopwords": stopwords,
        "fallback_token": NO_COMPLAINT_TOKEN,
        "icd_to_label": icd_to_label,
        "allowed_icd": ALLOWED_ICD_CODES,
        "default_age": float(df['AGE'].median()),
        "version": 2
    }
    joblib.dump(metadata, metadata_path)

    return {
        "status": "Training completed",
        "num_diseases": int(len(df)),
        "accuracy": round(float(accuracy), 4),
        "macro_f1": round(float(macro_f1), 4),
        "model_path": model_path
    }


def predict_disease_for_referral(referral_id):
    """Predict the most likely ICD-10 code for the referral."""
    models_dir = get_ml_models_path()
    model_path = os.path.join(models_dir, 'disease_rf_model.pkl')
    metadata_path = os.path.join(models_dir, 'disease_vectorizer.pkl')

    if not os.path.exists(model_path):
        return "Error: Disease classification model not found. Please train the model first."
    if not os.path.exists(metadata_path):
        return "Error: Disease vectorizer not found. Please train the model first."

    try:
        model = joblib.load(model_path)
        metadata = joblib.load(metadata_path) or {}
    except Exception as e:
        return f"Error loading model/vectorizer: {e}"

    try:
        referral = Referral.objects.select_related('patient').get(referral_id=referral_id)
    except Referral.DoesNotExist:
        return "Referral not found"

    feature_df = build_disease_feature_frame([referral], metadata)
    if feature_df.empty:
        return "Insufficient data for prediction"

    prediction_code = model.predict(feature_df)[0]
    allowed_codes = metadata.get('allowed_icd', ALLOWED_ICD_CODES)
    if allowed_codes and prediction_code not in allowed_codes:
        return "Unspecified"

    return prediction_code

    
def time_completed(referral_id):
    """
    Calculate the time taken to complete a referral in minutes.
    Args:
        referral_id (int): ID of the referral.
    Returns:
        float: Time in minutes, or error message if referral not found or not completed.
    """
    try:
        referral = Referral.objects.get(referral_id=referral_id)
    except Referral.DoesNotExist:
        return "Referral not found"
    
    if referral.completed_at is None:
        return "Referral not yet completed"
    
    # Fixed: completed_at should be after created_at, so subtract in correct order
    referral_complete = (referral.completed_at - referral.created_at).total_seconds() / 60
    
    return referral_complete
    

def gradient_boosting_regression_train_model():
    """
    Train a GradientBoostingRegressor model to predict time-to-cater.
    Saves the model and vectorizer to disk.
    Returns:
        dict: Training metrics and status
    """
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
        except (ValueError, TypeError, AttributeError):
            continue

    if not data:
        return {"error": "No valid completed referrals found."}

    df = pd.DataFrame(data)

    # Text vectorizer and feature assembly
    time_vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    symptoms_vectors = time_vectorizer.fit_transform(df["symptoms"]).toarray()

    X_numeric = df[['weight', 'height', 'bp_systolic', 'bp_diastolic', 'pulse_rate',
                    'respiratory_rate', 'temperature', 'oxygen_saturation']].reset_index(drop=True)

    X = pd.concat([X_numeric, pd.DataFrame(symptoms_vectors)], axis=1)
    X.columns = X.columns.astype(str)
    y = df['time_to_cater']

    # Split and train GBM
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = GradientBoostingRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        min_samples_split=5,
        random_state=42
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    metrics = {
        "MAE": round(mean_absolute_error(y_test, y_pred), 2),
        "R2_Score": round(r2_score(y_test, y_pred), 3)
    }

    # Save GB model and vectorizer
    models_dir = get_ml_models_path()
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, 'time_gb_model.pkl')
    vectorizer_path = os.path.join(models_dir, 'symptom_vectorizer.pkl')

    joblib.dump(model, model_path)
    joblib.dump(time_vectorizer, vectorizer_path)

    return {"status": "Training completed (GradientBoostingRegressor)", **metrics, "model_path": model_path}


# Backward-compatible alias so existing callers still work
def random_forest_regression_train_model():
    return gradient_boosting_regression_train_model()

def gradient_boosting_regression_prediction_time(referral, model=None, vectorizer=None):
    """
    Predict time to complete a referral using GradientBoostingRegressor.
    Args:
        referral: Referral object to predict for
        model: Optional pre-loaded model (if None, loads from disk)
        vectorizer: Optional pre-loaded vectorizer (if None, loads from disk)
    Returns:
        float: Predicted time in hours, or error message string
    """
    models_dir = get_ml_models_path()
    gb_model_path = os.path.join(models_dir, 'time_gb_model.pkl')
    rf_model_path = os.path.join(models_dir, 'time_rf_model.pkl')  # fallback for legacy
    vectorizer_path = os.path.join(models_dir, 'symptom_vectorizer.pkl')

    # Load model
    if model is None:
        load_path = gb_model_path if os.path.exists(gb_model_path) else rf_model_path
        if not os.path.exists(load_path):
            return "Error: Time prediction model not found. Please train the model first."
        try:
            model = joblib.load(load_path)
        except Exception as e:
            return f"Error loading model: {e}"

    # Load vectorizer
    if vectorizer is None:
        if not os.path.exists(vectorizer_path):
            return "Error: Symptom vectorizer not found. Please train the model first."
        try:
            vectorizer = joblib.load(vectorizer_path)
        except Exception as e:
            return f"Error loading vectorizer: {e}"

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

    except (ValueError, TypeError, AttributeError) as e:
        return f"Prediction error: {e}"


# Backward-compatible alias
def random_forest_regression_prediction_time(referral, model=None, vectorizer=None):
    return gradient_boosting_regression_prediction_time(referral, model=model, vectorizer=vectorizer)


def train_time_prediction_model_advanced():
    """
    Train advanced time-to-cater prediction model using complaints, diagnosis, age, sex.
    Based on time_cater.py approach with advanced feature engineering.
    Returns training metrics and status.
    """
    # Get referrals with symptoms and diagnosis
    referrals = Referral.objects.exclude(symptoms__isnull=True).exclude(symptoms='')
    referrals = referrals.select_related('patient')
    
    # Filter referrals that have either final_diagnosis or initial_diagnosis
    referrals = referrals.filter(
        Q(final_diagnosis__isnull=False) | Q(initial_diagnosis__isnull=False)
    )
    # Note: We'll handle empty strings in the loop
    
    if not referrals.exists():
        # Try with less strict filtering - at least need symptoms
        referrals = Referral.objects.exclude(symptoms__isnull=True).exclude(symptoms='')
        referrals = referrals.select_related('patient')
        if not referrals.exists():
            return {"error": "No referrals with symptoms found."}
    
    data = []
    for r in referrals:
        try:
            # Get patient info
            patient = r.patient
            age = patient.age if patient else None
            
            # Calculate time - use actual if completed, otherwise use proxy
            if r.completed_at and r.created_at:
                time_to_cater = (r.completed_at - r.created_at).total_seconds() / 3600
            else:
                # Use proxy calculation for incomplete referrals
                complaint_text = preprocess_text_advanced(r.symptoms or '')
                symptom_count = len(complaint_text.split())
                diagnosis_text = r.final_diagnosis or r.initial_diagnosis or ''
                diagnosis_words = len(str(diagnosis_text).split())
                
                base_time = 0.5
                complaint_score = min(symptom_count / 50, 1.0) * 1.0
                diagnosis_complexity = diagnosis_words * 0.1
                age_factor = min((age or 30) / 100, 0.5)
                
                time_to_cater = base_time + complaint_score + diagnosis_complexity + age_factor
                time_to_cater = max(0.25, min(time_to_cater, 4.0))
            
            # Prepare features
            data.append({
                'symptoms': r.symptoms or '',
                'diagnosis': r.final_diagnosis or r.initial_diagnosis or '',
                'age': age or 30,
                'sex': patient.sex if patient else 'M',
                'time_to_cater': time_to_cater
            })
        except Exception as e:
            continue
    
    if not data:
        return {"error": "No valid referral data found."}
    
    df = pd.DataFrame(data)
    
    # Preprocess text
    df['COMPLAINTS_PREPROCESSED'] = df['symptoms'].fillna('').apply(preprocess_text_advanced)
    df['DIAGNOSIS_CLEAN'] = df['diagnosis'].fillna('Unknown').astype(str).str.strip()
    
    # Feature engineering
    df['AGE'] = df['age'].fillna(df['age'].median())
    df['SEX'] = df['sex'].fillna('M').map({'M': 0, 'F': 1, 'Male': 0, 'Female': 1, 'male': 0, 'female': 1}).fillna(0)
    
    # Text features
    df['COMPLAINTS_LENGTH'] = df['COMPLAINTS_PREPROCESSED'].str.len()
    df['COMPLAINTS_WORD_COUNT'] = df['COMPLAINTS_PREPROCESSED'].str.split().str.len()
    df['COMPLAINTS_AVG_WORD_LENGTH'] = df['COMPLAINTS_LENGTH'] / (df['COMPLAINTS_WORD_COUNT'] + 1)
    
    # Medical keywords
    for keyword in MEDICAL_KEYWORDS:
        df[f'HAS_{keyword.upper()}_TIME'] = df['COMPLAINTS_PREPROCESSED'].str.contains(keyword, regex=False, na=False).astype(int)
    
    # Age features
    df['AGE_GROUP'] = df['AGE'].apply(assign_age_group)
    df['AGE_NORMALIZED'] = (df['AGE'] - df['AGE'].mean()) / (df['AGE'].std() + 1e-8)
    
    # Diagnosis features
    df['DIAGNOSIS_LENGTH'] = df['DIAGNOSIS_CLEAN'].str.len()
    df['DIAGNOSIS_WORD_COUNT'] = df['DIAGNOSIS_CLEAN'].str.split().str.len()
    
    # Encode diagnosis
    diag_encoder = LabelEncoder()
    df['DIAGNOSIS_ENCODED'] = diag_encoder.fit_transform(df['DIAGNOSIS_CLEAN'])
    
    # Fill NaN
    numeric_cols = ['COMPLAINTS_LENGTH', 'COMPLAINTS_WORD_COUNT', 'COMPLAINTS_AVG_WORD_LENGTH',
                    'AGE_NORMALIZED', 'DIAGNOSIS_LENGTH', 'DIAGNOSIS_WORD_COUNT']
    for col in numeric_cols:
        df[col] = df[col].fillna(0).astype(float)
    
    df['AGE_GROUP'] = df['AGE_GROUP'].fillna(2).astype(int)
    
    # Text vectorization
    time_vectorizer = TfidfVectorizer(
        max_features=1000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.90,
        stop_words='english',
        sublinear_tf=True
    )
    
    X_time_text = time_vectorizer.fit_transform(df['COMPLAINTS_PREPROCESSED'])
    
    # Numeric features
    time_numeric_features = ['AGE', 'SEX', 'COMPLAINTS_LENGTH', 'COMPLAINTS_WORD_COUNT',
                            'COMPLAINTS_AVG_WORD_LENGTH', 'AGE_GROUP', 'AGE_NORMALIZED',
                            'DIAGNOSIS_ENCODED', 'DIAGNOSIS_LENGTH', 'DIAGNOSIS_WORD_COUNT']
    time_keyword_features = [f'HAS_{kw.upper()}_TIME' for kw in MEDICAL_KEYWORDS]
    all_time_numeric = time_numeric_features + time_keyword_features
    
    X_time_numeric = df[all_time_numeric].values
    
    # Scale numeric features
    time_scaler = StandardScaler()
    X_time_numeric_scaled = time_scaler.fit_transform(X_time_numeric)
    
    # Combine features
    X_time = scipy.sparse.hstack([X_time_numeric_scaled, X_time_text])
    y_time = df['time_to_cater'].values
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_time, y_time, test_size=0.2, random_state=42
    )
    
    # Train models
    time_models = {}
    time_scores = {}
    
    # Random Forest
    rf_time = RandomForestRegressor(
        n_estimators=300,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    rf_time.fit(X_train, y_train)
    rf_pred = rf_time.predict(X_test)
    time_models['RF'] = rf_time
    time_scores['RF'] = {
        'MAE': mean_absolute_error(y_test, rf_pred),
        'R2': r2_score(y_test, rf_pred)
    }
    
    # Gradient Boosting
    gb_time = GradientBoostingRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        min_samples_split=5,
        subsample=0.8,
        random_state=42,
        verbose=0
    )
    gb_time.fit(X_train, y_train)
    gb_pred = gb_time.predict(X_test)
    time_models['GB'] = gb_time
    time_scores['GB'] = {
        'MAE': mean_absolute_error(y_test, gb_pred),
        'R2': r2_score(y_test, gb_pred)
    }
    
    # Select best model
    best_model_name = min(time_scores.items(), key=lambda x: x[1]['MAE'])[0]
    best_model = time_models[best_model_name]
    best_scores = time_scores[best_model_name]
    
    # Save models
    models_dir = get_ml_models_path()
    os.makedirs(models_dir, exist_ok=True)
    
    joblib.dump(best_model, os.path.join(models_dir, 'time_prediction_model_advanced.pkl'))
    joblib.dump(time_vectorizer, os.path.join(models_dir, 'time_vectorizer_advanced.pkl'))
    joblib.dump(time_scaler, os.path.join(models_dir, 'time_scaler_advanced.pkl'))
    joblib.dump(diag_encoder, os.path.join(models_dir, 'diag_time_encoder_advanced.pkl'))
    
    return {
        "status": "Training completed",
        "best_model": best_model_name,
        "MAE": round(best_scores['MAE'], 2),
        "R2_Score": round(best_scores['R2'], 3),
        "train_samples": X_train.shape[0],  # Use shape[0] for sparse matrices
        "test_samples": X_test.shape[0]  # Use shape[0] for sparse matrices
    }


def predict_time_to_cater_advanced(referral_id):
    """
    Predict time to cater for a referral using advanced model.
    Args:
        referral_id (int): ID of the referral
    Returns:
        float: Predicted time in hours, or error message string
    """
    models_dir = get_ml_models_path()
    model_path = os.path.join(models_dir, 'time_prediction_model_advanced.pkl')
    vectorizer_path = os.path.join(models_dir, 'time_vectorizer_advanced.pkl')
    scaler_path = os.path.join(models_dir, 'time_scaler_advanced.pkl')
    encoder_path = os.path.join(models_dir, 'diag_time_encoder_advanced.pkl')
    
    # Check if model files exist
    if not os.path.exists(model_path):
        return "Error: Advanced time prediction model not found. Please train the model first."
    if not os.path.exists(vectorizer_path):
        return "Error: Time vectorizer not found. Please train the model first."
    if not os.path.exists(scaler_path):
        return "Error: Time scaler not found. Please train the model first."
    if not os.path.exists(encoder_path):
        return "Error: Diagnosis encoder not found. Please train the model first."
    
    try:
        # Load components
        model = joblib.load(model_path)
        vectorizer = joblib.load(vectorizer_path)
        scaler = joblib.load(scaler_path)
        diag_encoder = joblib.load(encoder_path)
    except Exception as e:
        return f"Error loading model components: {e}"
    
    try:
        # Get referral
        referral = Referral.objects.select_related('patient').get(referral_id=referral_id)
    except Referral.DoesNotExist:
        return "Referral not found"
    
    try:
        # Get patient info
        patient = referral.patient
        age = patient.age if patient else 30
        sex = patient.sex if patient else 'M'
        
        # Preprocess text
        complaints_preprocessed = preprocess_text_advanced(referral.symptoms or '')
        diagnosis_clean = str(referral.final_diagnosis or referral.initial_diagnosis or 'Unknown').strip()
        
        # Feature engineering
        complaints_length = len(complaints_preprocessed)
        complaints_word_count = len(complaints_preprocessed.split())
        complaints_avg_word_length = complaints_length / (complaints_word_count + 1)
        
        # Medical keywords
        keyword_features = []
        for keyword in MEDICAL_KEYWORDS:
            keyword_features.append(1 if keyword in complaints_preprocessed else 0)
        
        # Age features
        age_group = assign_age_group(age)
        # Age normalization - we need to estimate from training data
        # For prediction, use a reasonable approximation (mean=30, std=15)
        # Note: This should ideally be saved from training, but using approximation for now
        age_normalized = (age - 30) / 15  # Adjusted std for better normalization
        
        # Diagnosis features
        diagnosis_length = len(diagnosis_clean)
        diagnosis_word_count = len(diagnosis_clean.split())
        
        # ICD10 features (must match training!)
        # Check if referral has ICD10 code field
        has_icd10 = 0
        icd10_length = 0
        if hasattr(referral, 'icd10_code') and referral.icd10_code:
            has_icd10 = 1
            icd10_length = len(str(referral.icd10_code))
        elif hasattr(referral, 'icd10') and referral.icd10:
            has_icd10 = 1
            icd10_length = len(str(referral.icd10))
        
        # Encode diagnosis (handle unseen values)
        try:
            # Check if diagnosis exists in encoder classes
            if diagnosis_clean in list(diag_encoder.classes_):
                diagnosis_encoded = diag_encoder.transform([diagnosis_clean])[0]
            else:
                diagnosis_encoded = 0  # Default for unseen diagnosis
        except:
            diagnosis_encoded = 0
        
        # Sex encoding
        sex_encoded = 0 if str(sex).upper() in ['M', 'MALE'] else 1
        
        # Build numeric features - MUST MATCH TRAINING ORDER!
        numeric_features = [
            age, sex_encoded, complaints_length, complaints_word_count,
            complaints_avg_word_length, age_group, age_normalized,
            diagnosis_encoded, diagnosis_length, diagnosis_word_count,
            has_icd10, icd10_length  # ADD THESE TWO FEATURES!
        ] + keyword_features
        
        # Scale numeric features
        X_numeric_scaled = scaler.transform([numeric_features])
        
        # Vectorize text
        X_text = vectorizer.transform([complaints_preprocessed])
        
        # Combine features
        X_combined = scipy.sparse.hstack([X_numeric_scaled, X_text])
        
        # Predict
        prediction = model.predict(X_combined)
        predicted_time = float(prediction[0])
        
        # Regression models can predict negative values when:
        # 1. Input features are very different from training data
        # 2. Model extrapolates beyond training range
        # 3. Feature scaling/normalization issues
        # 
        # We clamp to reasonable bounds to prevent invalid predictions
        original_prediction = predicted_time
        predicted_time = max(0.25, min(predicted_time, 4.0))
        
        # Log if prediction was clamped (for debugging)
        if original_prediction != predicted_time:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Time prediction clamped for referral {referral_id}: "
                f"{original_prediction:.2f} -> {predicted_time:.2f} hours"
            )
        
        return round(predicted_time, 2)
        
    except Exception as e:
        return f"Prediction error: {e}"
    
def train_model_disease_spike():
    """
    Train the model to predict disease spikes per months
    """

    qs = (
    Referral.objects
    .exclude(final_diagnosis__isnull=True)  # only with diagnosis
    .annotate(month=TruncMonth("created_at"))
    .values("month", "final_diagnosis")
    .annotate(count=Count("id"))
    .order_by("month")  
    )

    if not qs.exists():
        return pd.DataFrame()  # Return empty DataFrame if no data

    df = pd.DataFrame.from_records(qs)
    
    if df.empty:
        return pd.DataFrame()

    # one col per disease
    pv_df = df.pivot(index='month', columns='final_diagnosis', values='count').fillna(0)
    
    if pv_df.empty:
        return pd.DataFrame()

    # reset index for sklearn
    pv_df = pv_df.reset_index()
    pv_df['month'] = pd.to_datetime(pv_df['month'])

    # extract features
    pv_df['year'] = pv_df['month'].dt.year
    pv_df['month_num'] = pv_df['month'].dt.month
            
    return pv_df

def disease_forecast(pv_df, months_ahead=12):
    predictions = {}
    
    if pv_df.empty:
        return {"error": "No data available for forecasting"}

    # Get disease columns (exclude 'month', 'year', 'month_num')
    disease_cols = [col for col in pv_df.columns 
                    if col not in ['month', 'year', 'month_num']]
    
    if not disease_cols:
        return {"error": "No disease columns found in data"}

    for disease in disease_cols:
        try:
            X = pv_df[['year', 'month_num']]
            y = pv_df[disease]

            rf = RandomForestRegressor(n_estimators=100, random_state=42)
            rf.fit(X, y)

            # generate next N months
            last_year, last_month = pv_df['year'].max(), pv_df['month_num'].max()
            future = []
            year, month_num = last_year, last_month
            for _ in range(months_ahead):
                month_num += 1
                if month_num > 12:
                    month_num = 1
                    year += 1
                future.append({'year': year, 'month_num': month_num})  # Fixed: dict instead of set

            X_future = pd.DataFrame(future, columns=["year", "month_num"])
            y_future = rf.predict(X_future)

            predictions[disease] = list(zip(X_future.values.tolist(), y_future))
        except Exception as e:
            predictions[disease] = f"Error: {str(e)}"

    return predictions


def extract_icd10_from_text(text):
    """
    Extract ICD10 code from diagnosis text if present.
    ICD10 codes typically follow pattern: Letter + 2 digits + . + 1-2 digits
    Examples: T14.1, W54.99, J06.9, J15, I10.1
    """
    if not text:
        return None
    
    # Pattern: Letter(s) + digits + optional dot + digits
    pattern = r'\b([A-Z]\d{2}(?:\.\d{1,2})?)\b'
    matches = re.findall(pattern, str(text).upper())
    
    if matches:
        return matches[0]  # Return first match
    return None


def get_top_diseases_from_dataframe(df, top_n=5):
    """
    Identify top N diseases based on ICD10 code frequency.
    Returns list of top disease codes/categories.
    Excludes Z00 (general health check) from the results.
    """
    if df['ICD10 CODE'].notna().sum() > 0:
        # Use ICD10 codes
        # Filter out Z00 before getting top diseases
        df_filtered = df[df['ICD10 CODE'] != 'Z00'].copy()
        if df_filtered.empty:
            # If filtering Z00 leaves no data, use original df
            df_filtered = df.copy()
        top_diseases = df_filtered['ICD10 CODE'].value_counts().head(top_n)
        return top_diseases.index.tolist()
    else:
        # Fallback: use diagnosis categories
        df['DIAGNOSIS_CATEGORY'] = df['DIAGNOSIS'].apply(
            lambda x: str(x)[:50].strip() if x else 'Unknown'
        )
        top_diseases = df['DIAGNOSIS_CATEGORY'].value_counts().head(top_n)
        return top_diseases.index.tolist()


def load_disease_peak_csv_data(csv_2023_path=None, csv_2024_path=None):
    """
    Load data from CSV files for 2023 and 2024.
    Returns combined DataFrame with standardized column names.
    """
    base_dir = str(settings.BASE_DIR)
    
    # Default paths
    if csv_2023_path is None:
        possible_paths_2023 = [
            os.path.join(base_dir, 'sample_datasets', 'New_Corella_datasets_2023.csv'),
            os.path.join(os.path.dirname(base_dir), 'MHOERS', 'sample_datasets', 'New_Corella_datasets_2023.csv'),
        ]
        for path in possible_paths_2023:
            if os.path.exists(path):
                csv_2023_path = path
                break
        if csv_2023_path is None:
            csv_2023_path = possible_paths_2023[0]
    
    if csv_2024_path is None:
        possible_paths_2024 = [
            os.path.join(base_dir, 'sample_datasets', 'New_corella_datasets_5.csv'),
            os.path.join(os.path.dirname(base_dir), 'MHOERS', 'sample_datasets', 'New_corella_datasets_5.csv'),
        ]
        for path in possible_paths_2024:
            if os.path.exists(path):
                csv_2024_path = path
                break
        if csv_2024_path is None:
            csv_2024_path = possible_paths_2024[0]
    
    # Load CSV files
    if not os.path.exists(csv_2023_path):
        raise FileNotFoundError(f"CSV file not found: {csv_2023_path}")
    if not os.path.exists(csv_2024_path):
        raise FileNotFoundError(f"CSV file not found: {csv_2024_path}")
    
    df_2023 = pd.read_csv(csv_2023_path, encoding='latin1')
    df_2024 = pd.read_csv(csv_2024_path, encoding='latin1')
    
    # Combine datasets
    df = pd.concat([df_2023, df_2024], ignore_index=True)
    
    # Standardize column names
    df.columns = df.columns.str.strip()
    required_cols = ['AGE', 'SEX', 'COMPLAINTS', 'DIAGNOSIS', 'ICD10 CODE']
    
    # Check if columns exist (case-insensitive)
    for col in required_cols:
        if col not in df.columns:
            matching_cols = [c for c in df.columns if c.upper() == col.upper()]
            if matching_cols:
                df.rename(columns={matching_cols[0]: col}, inplace=True)
    
    # Handle SITIO/BARANGAY column (preserve if exists)
    if 'SITIO/BARANGAY' not in df.columns:
        # Try to find similar column names
        possible_barangay_cols = [c for c in df.columns if 'barangay' in c.lower() or 'sitio' in c.lower() or 'location' in c.lower()]
        if possible_barangay_cols:
            df.rename(columns={possible_barangay_cols[0]: 'SITIO/BARANGAY'}, inplace=True)
        else:
            df['SITIO/BARANGAY'] = 'Unknown'
    
    # Handle DATE column if exists
    if 'DATE' in df.columns:
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
    elif 'CREATED_AT' in df.columns:
        df['DATE'] = pd.to_datetime(df['CREATED_AT'], errors='coerce')
    
    # Clean ICD10 CODE column
    if 'ICD10 CODE' in df.columns:
        mask_empty = df['ICD10 CODE'].isna() | (df['ICD10 CODE'].astype(str).str.strip() == '')
        if 'DIAGNOSIS' in df.columns:
            df.loc[mask_empty, 'ICD10 CODE'] = df.loc[mask_empty, 'DIAGNOSIS'].apply(
                lambda x: extract_icd10_from_text(str(x)) if pd.notna(x) else None
            )
    
    return df


def queryset_to_disease_peak_dataframe(referrals):
    """
    Convert Django QuerySet to pandas DataFrame for disease peak analysis.
    Maps Django model fields to CSV column equivalents.
    """
    data = []
    
    for referral in referrals.select_related('patient', 'facility'):
        patient = referral.patient
        if not patient:
            continue
            
        diagnosis = referral.final_diagnosis or referral.initial_diagnosis or ''
        
        # Get ICD10 code
        if hasattr(referral, 'ICD_code') and referral.ICD_code:
            icd10_code = str(referral.ICD_code).strip()
        elif hasattr(referral, 'icd10_code') and referral.icd10_code:
            icd10_code = str(referral.icd10_code).strip()
        else:
            icd10_code = extract_icd10_from_text(diagnosis)
        
        diagnosis_label = icd10_code if icd10_code else str(diagnosis)[:50].strip() or 'Unknown'
        
        # Get barangay/facility name
        barangay = 'Unknown'
        if referral.facility:
            barangay = referral.facility.name
        elif hasattr(patient, 'facility') and patient.facility:
            barangay = patient.facility.name
        
        data.append({
            'AGE': patient.age,
            'SEX': patient.sex,
            'COMPLAINTS': referral.chief_complaint or referral.symptoms or '',
            'DIAGNOSIS': diagnosis,
            'ICD10 CODE': icd10_code if icd10_code else diagnosis_label,
            'CREATED_AT': referral.created_at,
            'SITIO/BARANGAY': barangay,
            'DATE': referral.created_at,
        })
    
    return pd.DataFrame(data)


def train_disease_peak_prediction_model(csv_2023_path=None, csv_2024_path=None, use_db=False, top_n=5):
    """
    Train disease peak prediction model and save it for reuse.
    
    Args:
        csv_2023_path: Path to 2023 CSV file (if None, uses default)
        csv_2024_path: Path to 2024 CSV file (if None, uses default)
        use_db: If True, load from Django database instead of CSV
        top_n: Number of top diseases to analyze (default: 5)
    
    Returns:
        dict: Training metrics and status
    """
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.svm import LinearSVC
    from scipy.sparse import hstack
    
    # Step 1: Load data
    if use_db:
        referrals_2023_2024 = Referral.objects.filter(
            created_at__year__in=[2023, 2024]
        ).exclude(
            Q(patient__isnull=True) | 
            Q(initial_diagnosis__isnull=True) | 
            Q(initial_diagnosis='')
        )
        
        if not referrals_2023_2024.exists():
            return {"error": "No referral data found for 2023-2024"}
        
        df = queryset_to_disease_peak_dataframe(referrals_2023_2024)
    else:
        try:
            df = load_disease_peak_csv_data(csv_2023_path, csv_2024_path)
        except FileNotFoundError as e:
            return {"error": str(e)}
    
    if df.empty:
        return {"error": "No data loaded"}
    
    # Step 2: Identify top diseases
    allowed_diseases = get_top_diseases_from_dataframe(df, top_n)
    df = df[df['ICD10 CODE'].isin(allowed_diseases)]
    
    if df.empty:
        return {"error": "No data remaining after filtering"}
    
    # Step 3: Prepare features
    target = 'ICD10 CODE'
    df = df.dropna(subset=['AGE', 'SEX', 'COMPLAINTS', target])
    
    if df.empty:
        return {"error": "No data remaining after removing missing values"}
    
    # Feature engineering
    df['COMPLAINTS'] = df['COMPLAINTS'].fillna('').astype(str).str.strip()
    df['COMPLAINTS_CLEAN'] = df['COMPLAINTS'].str.lower()
    df['COMPLAINTS_LENGTH'] = df['COMPLAINTS'].str.len()
    df['COMPLAINTS_WORD_COUNT'] = df['COMPLAINTS'].str.split().str.len()
    df['COMPLAINTS_AVG_WORD_LENGTH'] = df['COMPLAINTS_LENGTH'] / (df['COMPLAINTS_WORD_COUNT'] + 1)
    
    df['AGE'] = pd.to_numeric(df['AGE'], errors='coerce')
    df['AGE'] = df['AGE'].fillna(df['AGE'].median())
    df['AGE_GROUP'] = pd.cut(df['AGE'], bins=[0, 18, 35, 50, 65, 100], 
                             labels=[0, 1, 2, 3, 4], include_lowest=True).astype(int)
    df['AGE_NORMALIZED'] = (df['AGE'] - df['AGE'].mean()) / (df['AGE'].std() + 1e-8)
    
    df['SEX'] = df['SEX'].astype(str).str.strip().str.upper()
    df['SEX_ENCODED'] = df['SEX'].map({'M': 0, 'MALE': 0, 'F': 1, 'FEMALE': 1}).fillna(0)
    
    # Fill NaN
    df['COMPLAINTS_LENGTH'] = df['COMPLAINTS_LENGTH'].fillna(0)
    df['COMPLAINTS_WORD_COUNT'] = df['COMPLAINTS_WORD_COUNT'].fillna(0)
    df['COMPLAINTS_AVG_WORD_LENGTH'] = df['COMPLAINTS_AVG_WORD_LENGTH'].fillna(0)
    
    # Encode target
    target_encoder = LabelEncoder()
    df[target] = target_encoder.fit_transform(df[target].astype(str))
    
    # Prepare features
    numeric_features = ['AGE', 'AGE_GROUP', 'AGE_NORMALIZED', 'SEX_ENCODED', 
                       'COMPLAINTS_LENGTH', 'COMPLAINTS_WORD_COUNT', 'COMPLAINTS_AVG_WORD_LENGTH']
    text_features = ['COMPLAINTS_CLEAN']
    
    # Train/test split
    y = df[target]
    X_train, X_test, y_train, y_test = train_test_split(
        df, y, test_size=0.2, random_state=42
    )
    
    # Create preprocessing
    tfidf = TfidfVectorizer(
        max_features=500,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        lowercase=True,
        stop_words='english'
    )
    scaler = StandardScaler()
    
    # Prepare features
    X_train_numeric = X_train[numeric_features].values
    X_test_numeric = X_test[numeric_features].values
    X_train_text = tfidf.fit_transform(X_train[text_features[0]])
    X_test_text = tfidf.transform(X_test[text_features[0]])
    
    X_train_numeric_scaled = scaler.fit_transform(X_train_numeric)
    X_test_numeric_scaled = scaler.transform(X_test_numeric)
    
    X_train_combined = hstack([X_train_numeric_scaled, X_train_text])
    X_test_combined = hstack([X_test_numeric_scaled, X_test_text])
    
    # Train models
    models = {
        "Random Forest": RandomForestClassifier(
            n_estimators=300, 
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42, 
            n_jobs=-1
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            learning_rate=0.05, 
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        ),
        "Linear SVM": LinearSVC(
            C=0.5, 
            max_iter=10000, 
            random_state=42
        )
    }
    
    results = []
    best_model = None
    best_model_name = None
    best_score = 0
    
    for name, model in models.items():
        model.fit(X_train_combined, y_train)
        y_pred = model.predict(X_test_combined)
        acc = accuracy_score(y_test, y_pred)
        macro_f1 = f1_score(y_test, y_pred, average='macro')
        weighted_f1 = f1_score(y_test, y_pred, average='weighted')
        
        results.append({
            "Model": name,
            "Accuracy": acc,
            "Macro F1": macro_f1,
            "Weighted F1": weighted_f1
        })
        
        if acc > best_score:
            best_score = acc
            best_model = model
            best_model_name = name
    
    # Save model and preprocessing components
    models_dir = get_ml_models_path()
    os.makedirs(models_dir, exist_ok=True)
    
    joblib.dump(best_model, os.path.join(models_dir, 'disease_peak_model.pkl'))
    joblib.dump(tfidf, os.path.join(models_dir, 'disease_peak_tfidf.pkl'))
    joblib.dump(scaler, os.path.join(models_dir, 'disease_peak_scaler.pkl'))
    joblib.dump(target_encoder, os.path.join(models_dir, 'disease_peak_encoder.pkl'))
    
    # Save metadata
    metadata = {
        'numeric_features': numeric_features,
        'text_features': text_features,
        'allowed_diseases': allowed_diseases,
        'top_n': top_n,
        'best_model_name': best_model_name,
        'results': results
    }
    joblib.dump(metadata, os.path.join(models_dir, 'disease_peak_metadata.pkl'))
    
    return {
        "status": "Training completed",
        "best_model": best_model_name,
        "accuracy": round(best_score, 4),
        "top_diseases": allowed_diseases,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "models_saved_to": models_dir
    }


def predict_disease_peak_for_month(month_name=None, samples_per_month=100, use_db=False, csv_2023_path=None, csv_2024_path=None):
    """
    Predict disease peak for a specific month using saved model.
    
    Args:
        month_name: Month name (e.g., "January", "February") or None for all months
        samples_per_month: Number of samples to simulate per month
        use_db: Use Django database for simulation data
        csv_2023_path: Path to 2023 CSV file
        csv_2024_path: Path to 2024 CSV file
    
    Returns:
        dict: Prediction results with month and predicted disease
    """
    import joblib
    from scipy.sparse import hstack
    import random
    
    # Load saved model
    models_dir = get_ml_models_path()
    model_path = os.path.join(models_dir, 'disease_peak_model.pkl')
    tfidf_path = os.path.join(models_dir, 'disease_peak_tfidf.pkl')
    scaler_path = os.path.join(models_dir, 'disease_peak_scaler.pkl')
    encoder_path = os.path.join(models_dir, 'disease_peak_encoder.pkl')
    metadata_path = os.path.join(models_dir, 'disease_peak_metadata.pkl')
    
    if not all(os.path.exists(p) for p in [model_path, tfidf_path, scaler_path, encoder_path, metadata_path]):
        return {"error": "Disease peak model not found. Please train the model first."}
    
    try:
        model = joblib.load(model_path)
        tfidf = joblib.load(tfidf_path)
        scaler = joblib.load(scaler_path)
        target_encoder = joblib.load(encoder_path)
        metadata = joblib.load(metadata_path)
    except Exception as e:
        return {"error": f"Error loading model: {e}"}
    
    numeric_features = metadata['numeric_features']
    text_features = metadata['text_features']
    
    # Load historical data for simulation
    if use_db:
        referrals_2023_2024 = Referral.objects.filter(
            created_at__year__in=[2023, 2024]
        ).exclude(
            Q(patient__isnull=True) | 
            Q(initial_diagnosis__isnull=True) | 
            Q(initial_diagnosis='')
        )
        
        if not referrals_2023_2024.exists():
            return {"error": "No referral data found for 2023-2024"}
        
        original_df = queryset_to_disease_peak_dataframe(referrals_2023_2024)
    else:
        try:
            original_df = load_disease_peak_csv_data(csv_2023_path, csv_2024_path)
        except FileNotFoundError as e:
            return {"error": str(e)}
    
    # Simulate data for the requested month(s)
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    
    target_months = [month_name] if month_name and month_name in months else months
    
    sample_columns = ['AGE', 'SEX', 'COMPLAINTS']
    available_columns = [col for col in sample_columns if col in original_df.columns]
    sampling_df = original_df[available_columns].dropna(subset=available_columns)
    
    if len(sampling_df) == 0:
        return {"error": "No valid data for sampling"}
    
    # Calculate average patients per month from historical data
    monthly_averages = {}
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    
    if use_db:
        from django.db.models import Count
        from django.db.models.functions import ExtractMonth
        
        # Get monthly counts from historical referrals
        monthly_counts = Referral.objects.filter(
            created_at__year__in=[2023, 2024]
        ).exclude(
            Q(patient__isnull=True) | 
            Q(initial_diagnosis__isnull=True) | 
            Q(initial_diagnosis='')
        ).extra(
            select={'month': "EXTRACT(MONTH FROM created_at)"}
        ).values('month').annotate(count=Count('id'))
        
        # Calculate average per month (across 2 years)
        for month_num in range(1, 13):
            month_data = [mc['count'] for mc in monthly_counts if mc['month'] == month_num]
            if month_data:
                # Average across 2 years
                monthly_averages[month_names[month_num - 1]] = int(sum(month_data) / len(month_data))
            else:
                # Fallback to default if no data for this month
                monthly_averages[month_names[month_num - 1]] = samples_per_month
    else:
        # For CSV data, try to calculate from dataframe if date column exists
        date_cols = [col for col in original_df.columns if 'date' in col.lower() or 'created' in col.lower()]
        if date_cols:
            try:
                date_col = date_cols[0]
                original_df['month'] = pd.to_datetime(original_df[date_col], errors='coerce').dt.month
                for month_num in range(1, 13):
                    month_data = original_df[original_df['month'] == month_num]
                    if len(month_data) > 0:
                        monthly_averages[month_names[month_num - 1]] = int(len(month_data) / 2)  # Average over 2 years
                    else:
                        monthly_averages[month_names[month_num - 1]] = samples_per_month
            except:
                # If date parsing fails, use default for all months
                for month in month_names:
                    monthly_averages[month] = samples_per_month
        else:
            # No date column, use default
            for month in month_names:
                monthly_averages[month] = samples_per_month
    
    # Import hashlib for month-specific random seeds
    import hashlib
    
    results = {}
    
    for month in target_months:
        # Use historical average for this month, or fallback to default
        month_samples = monthly_averages.get(month, samples_per_month)
        
        # Generate month-specific random seed for variation
        month_seed = int(hashlib.md5(month.encode()).hexdigest()[:8], 16) % (2**31)
        
        # Generate simulated data for this month with month-specific sample size
        sampled_data = sampling_df.sample(
            n=min(month_samples, len(sampling_df)), 
            replace=True if month_samples > len(sampling_df) else False,
            random_state=month_seed  # Different seed per month
        )
        
        sim_df = sampled_data.head(month_samples).copy()
        
        # Ensure all required columns exist
        for col in sample_columns:
            if col not in sim_df.columns:
                if col == 'AGE':
                    sim_df[col] = random.randint(1, 90)
                elif col == 'SEX':
                    sim_df[col] = random.choice(["Male", "Female"])
                else:
                    sim_df[col] = ''
        
        # Apply feature engineering
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
        
        # Count disease occurrences
        disease_counts = sim_df["Predicted_Disease_Label"].value_counts()
        
        # Get all disease predictions (not just peak)
        all_diseases = {}
        for disease_code, count in disease_counts.items():
            all_diseases[disease_code] = int(count)
        
        # Still include peak for backward compatibility
        peak_disease = disease_counts.index[0] if len(disease_counts) > 0 else "Unknown"
        peak_count = int(disease_counts.iloc[0]) if len(disease_counts) > 0 else 0
        
        results[month] = {
            'disease': peak_disease,  # Peak disease for backward compatibility
            'count': peak_count,  # Peak count for backward compatibility
            'total_samples': month_samples,  # Use historical average
            'all_diseases': all_diseases  # All diseases with their counts
        }
    
    return results


def train_barangay_disease_peak_model(csv_2023_path=None, csv_2024_path=None, use_db=False, allowed_icd=None):
    """
    Train barangay-based disease peak prediction model (similar to Google Colab code).
    Trains a RandomForestRegressor per disease per barangay using YEAR and MONTH features.
    
    Args:
        csv_2023_path: Path to 2023 CSV file (if None, uses default)
        csv_2024_path: Path to 2024 CSV file (if None, uses default)
        use_db: If True, load from Django database instead of CSV
        allowed_icd: List of allowed ICD10 codes (if None, uses default)
    
    Returns:
        dict: Training status and saved model paths
    """
    # Default allowed ICD codes
    if allowed_icd is None:
        allowed_icd = ALLOWED_ICD_CODES
    
    # Step 1: Load data
    if use_db:
        referrals_2023_2024 = Referral.objects.filter(
            created_at__year__in=[2023, 2024]
        ).exclude(
            Q(patient__isnull=True) | 
            Q(initial_diagnosis__isnull=True) | 
            Q(initial_diagnosis='')
        ).select_related('patient', 'facility')
        
        if not referrals_2023_2024.exists():
            return {"error": "No referral data found for 2023-2024"}
        
        df = queryset_to_disease_peak_dataframe(referrals_2023_2024)
    else:
        try:
            df = load_disease_peak_csv_data(csv_2023_path, csv_2024_path)
        except FileNotFoundError as e:
            return {"error": str(e)}
    
    if df.empty:
        return {"error": "No data loaded"}
    
    # Step 2: Clean and prepare key columns
    if 'DATE' not in df.columns:
        if 'CREATED_AT' in df.columns:
            df['DATE'] = pd.to_datetime(df['CREATED_AT'], errors='coerce')
        else:
            return {"error": "No date column found in data"}
    
    df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
    df['MONTH'] = df['DATE'].dt.month
    df['YEAR'] = df['DATE'].dt.year
    
    # Drop rows with missing barangay or ICD10 code
    df = df.dropna(subset=['SITIO/BARANGAY', 'ICD10 CODE'])
    
    # Filter by allowed ICD codes
    df = df[df['ICD10 CODE'].isin(allowed_icd)].copy()
    
    if df.empty:
        return {"error": "No data remaining after filtering"}
    
    # Step 3: Aggregate disease counts by Barangay, Disease, Year, and Month
    barangay_trends = (
        df.groupby(['SITIO/BARANGAY', 'ICD10 CODE', 'YEAR', 'MONTH'])
          .size()
          .reset_index(name='CASE_COUNT')
    )
    
    if barangay_trends.empty:
        return {"error": "No aggregated data available"}
    
    # Step 4: Train regression model per disease per barangay
    models_dict = {}
    training_stats = {
        'total_barangays': 0,
        'total_diseases': 0,
        'models_trained': 0,
        'skipped_insufficient_data': 0
    }
    
    for barangay in barangay_trends['SITIO/BARANGAY'].unique():
        training_stats['total_barangays'] += 1
        models_dict[barangay] = {}
        
        for disease in barangay_trends['ICD10 CODE'].unique():
            training_stats['total_diseases'] += 1
            
            subset = barangay_trends[
                (barangay_trends['SITIO/BARANGAY'] == barangay) &
                (barangay_trends['ICD10 CODE'] == disease)
            ]
            
            if len(subset) < 3:
                training_stats['skipped_insufficient_data'] += 1
                continue  # Skip if not enough data points
            
            X = subset[['YEAR', 'MONTH']]
            y = subset['CASE_COUNT']
            
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)
            
            models_dict[barangay][disease] = model
            training_stats['models_trained'] += 1
    
    # Save models
    models_dir = get_ml_models_path()
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, 'barangay_disease_peak_models.pkl')
    metadata_path = os.path.join(models_dir, 'barangay_disease_peak_metadata.pkl')
    
    joblib.dump(models_dict, model_path)
    
    metadata = {
        'allowed_icd': allowed_icd,
        'barangays': list(barangay_trends['SITIO/BARANGAY'].unique()),
        'diseases': list(barangay_trends['ICD10 CODE'].unique()),
        'training_stats': training_stats
    }
    joblib.dump(metadata, metadata_path)
    
    return {
        "status": "Training completed",
        "models_saved_to": model_path,
        "metadata_saved_to": metadata_path,
        "training_stats": training_stats
    }


def predict_barangay_disease_peak_2025(target_barangays=None, csv_2023_path=None, csv_2024_path=None, use_db=False):
    """
    Predict monthly disease peaks for each barangay in 2025 (similar to Google Colab code).
    
    Args:
        target_barangays: List of barangay names to filter (if None, predicts for all)
        csv_2023_path: Path to 2023 CSV file (if None, uses default)
        csv_2024_path: Path to 2024 CSV file (if None, uses default)
        use_db: If True, load from Django database instead of CSV
    
    Returns:
        dict: Predictions with structure {barangay: {month: {disease: count, ...}}}
    """
    # Load saved models
    models_dir = get_ml_models_path()
    model_path = os.path.join(models_dir, 'barangay_disease_peak_models.pkl')
    metadata_path = os.path.join(models_dir, 'barangay_disease_peak_metadata.pkl')
    
    if not os.path.exists(model_path) or not os.path.exists(metadata_path):
        return {"error": "Barangay disease peak models not found. Please train the model first using train_barangay_disease_peak_model()"}
    
    try:
        models_dict = joblib.load(model_path)
        metadata = joblib.load(metadata_path)
    except Exception as e:
        return {"error": f"Error loading models: {e}"}
    
    # Get all barangays from models and filter out "poblacion" (case-insensitive)
    all_barangays = [b for b in models_dict.keys() if 'poblacion' not in b.lower()]
    
    # Filter target barangays if specified
    if target_barangays:
        # Case-insensitive matching
        target_barangays_upper = [b.upper() for b in target_barangays]
        filtered_barangays = [b for b in all_barangays if b.upper() in target_barangays_upper]
        if not filtered_barangays:
            return {"error": f"No matching barangays found. Available: {all_barangays}"}
        all_barangays = filtered_barangays
    
    # Step 5: Generate predictions for 2025
    predictions = []
    
    for barangay in all_barangays:
        if barangay not in models_dict:
            continue
        
        for disease in models_dict[barangay].keys():
            model = models_dict[barangay][disease]
            
            # Predict for 2025 months (1-12)
            future_months = pd.DataFrame({'YEAR': [2025]*12, 'MONTH': range(1, 13)})
            y_pred = model.predict(future_months)
            
            for m, p in zip(range(1, 13), y_pred):
                predictions.append({
                    'Barangay': barangay,
                    'Disease': disease,
                    'Year': 2025,
                    'Month': m,
                    'Predicted_Cases': max(0, int(round(p)))
                })
    
    if not predictions:
        return {"error": "No predictions generated"}
    
    # Convert predictions to DataFrame
    pred_df = pd.DataFrame(predictions)
    
    # Find the top disease per barangay each month
    peak_disease = (
        pred_df.sort_values(['Barangay', 'Month', 'Predicted_Cases'], ascending=[True, True, False])
        .groupby(['Barangay', 'Month'])
        .first()
        .reset_index()
    )
    
    # Organize results by barangay and month
    results = {}
    for barangay in all_barangays:
        results[barangay] = {}
        
        # Get all predictions for this barangay
        barangay_preds = pred_df[pred_df['Barangay'] == barangay]
        
        for month in range(1, 13):
            month_data = barangay_preds[barangay_preds['Month'] == month]
            
            # Get peak disease
            peak = peak_disease[
                (peak_disease['Barangay'] == barangay) & 
                (peak_disease['Month'] == month)
            ]
            
            # Get all diseases for this month
            all_diseases = {}
            for _, row in month_data.iterrows():
                # Convert to Python native types for JSON serialization
                all_diseases[str(row['Disease'])] = int(row['Predicted_Cases'])
            
            if not peak.empty:
                results[barangay][month] = {
                    'peak_disease': str(peak.iloc[0]['Disease']),
                    'peak_cases': int(peak.iloc[0]['Predicted_Cases']),
                    'all_diseases': all_diseases
                }
            else:
                results[barangay][month] = {
                    'peak_disease': None,
                    'peak_cases': 0,
                    'all_diseases': all_diseases
                }
    
    return results


def train_time_prediction_model_advanced_from_csv(csv_path=None):
    """
    Train advanced time prediction model from CSV file and save as .pkl files.
    Uses the same logic as time_cater.py but saves models for Django reuse.
    
    Args:
        csv_path: Path to CSV file. If None, uses default path.
    
    Returns:
        dict: Training metrics and status
    """
    # Default CSV path
    if csv_path is None:
        # Try multiple possible paths
        base_dir = str(settings.BASE_DIR)
        
        possible_paths = [
            # Direct path from BASE_DIR (if BASE_DIR is MHOERS folder)
            os.path.join(base_dir, 'sample_datasets', 'New_corella_datasets_5.csv'),
            # If BASE_DIR is one level up
            os.path.join(os.path.dirname(base_dir), 'MHOERS', 'sample_datasets', 'New_corella_datasets_5.csv'),
            # Absolute path
            os.path.abspath(os.path.join(base_dir, 'sample_datasets', 'New_corella_datasets_5.csv')),
        ]
        
        csv_path = None
        for path in possible_paths:
            if os.path.exists(path):
                csv_path = os.path.abspath(path)  # Use absolute path
                break
        
        if csv_path is None:
            # Show all tried paths for debugging
            return {
                "error": f"CSV file not found. Tried paths: {possible_paths}",
                "base_dir": base_dir
            }
    
    if not os.path.exists(csv_path):
        return {"error": f"CSV file not found: {csv_path}"}
    
    df_time = pd.read_csv(csv_path, encoding='latin1')
    
    # Clean data (same as time_cater.py)
    df_time = df_time[df_time['COMPLAINTS'].notna()].copy()
    df_time = df_time[df_time['DIAGNOSIS'].notna()].copy()
    df_time = df_time[(df_time['AGE'] >= 0) & (df_time['AGE'] <= 120)].copy()
    
    
    # Preprocess text
    df_time['COMPLAINTS_PREPROCESSED'] = df_time['COMPLAINTS'].fillna('').apply(preprocess_text_advanced)
    df_time['DIAGNOSIS_CLEAN'] = df_time['DIAGNOSIS'].fillna('Unknown').astype(str).str.strip()
    
    # Feature engineering (same as time_cater.py)
    df_time['AGE'] = df_time['AGE'].fillna(df_time['AGE'].median())
    # Convert SEX to numeric (M=0, F=1)
    df_time['SEX'] = df_time['SEX'].fillna('M').map({'M': 0, 'F': 1, 'Male': 0, 'Female': 1, 'male': 0, 'female': 1}).fillna(0)
    
    # Text features
    df_time['COMPLAINTS_LENGTH'] = df_time['COMPLAINTS_PREPROCESSED'].str.len()
    df_time['COMPLAINTS_WORD_COUNT'] = df_time['COMPLAINTS_PREPROCESSED'].str.split().str.len()
    df_time['COMPLAINTS_AVG_WORD_LENGTH'] = df_time['COMPLAINTS_LENGTH'] / (df_time['COMPLAINTS_WORD_COUNT'] + 1)
    
    # Medical keywords
    for keyword in MEDICAL_KEYWORDS:
        df_time[f'HAS_{keyword.upper()}_TIME'] = df_time['COMPLAINTS_PREPROCESSED'].str.contains(keyword, regex=False, na=False).astype(int)
    
    # Age features
    df_time['AGE_GROUP'] = df_time['AGE'].apply(assign_age_group)
    df_time['AGE_NORMALIZED'] = (df_time['AGE'] - df_time['AGE'].mean()) / (df_time['AGE'].std() + 1e-8)
    
    # Diagnosis features
    df_time['DIAGNOSIS_LENGTH'] = df_time['DIAGNOSIS_CLEAN'].str.len()
    df_time['DIAGNOSIS_WORD_COUNT'] = df_time['DIAGNOSIS_CLEAN'].str.split().str.len()
    
    # Encode diagnosis
    diag_time_encoder = LabelEncoder()
    df_time['DIAGNOSIS_ENCODED'] = diag_time_encoder.fit_transform(df_time['DIAGNOSIS_CLEAN'])
    
    # ICD10 (if available)
    if 'ICD10 CODE' in df_time.columns:
        df_time['HAS_ICD10'] = df_time['ICD10 CODE'].notna().astype(int)
        df_time['ICD10_LENGTH'] = df_time['ICD10 CODE'].astype(str).str.len()
    else:
        df_time['HAS_ICD10'] = 0
        df_time['ICD10_LENGTH'] = 0
    
    # Fill NaN
    numeric_cols = ['COMPLAINTS_LENGTH', 'COMPLAINTS_WORD_COUNT', 'COMPLAINTS_AVG_WORD_LENGTH',
                    'AGE_NORMALIZED', 'DIAGNOSIS_LENGTH', 'DIAGNOSIS_WORD_COUNT', 'ICD10_LENGTH']
    for col in numeric_cols:
        df_time[col] = df_time[col].fillna(0).astype(float)
    
    df_time['AGE_GROUP'] = df_time['AGE_GROUP'].fillna(2).astype(int)
    
    # Create proxy time target (same as time_cater.py)
    def calculate_proxy_time(row):
        base_time = 0.5
        complaint_score = min(row['COMPLAINTS_WORD_COUNT'] / 50, 1.0) * 1.0
        diagnosis_complexity = len(str(row['DIAGNOSIS_CLEAN']).split()) * 0.1
        age_factor = min(row['AGE'] / 100, 0.5)
        total = base_time + complaint_score + diagnosis_complexity + age_factor
        return max(0.25, min(total, 4.0))
    
    df_time['TIME_TO_CATER'] = df_time.apply(calculate_proxy_time, axis=1)
    
    # Text vectorization
    time_vectorizer = TfidfVectorizer(
        max_features=1000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.90,
        stop_words='english',
        sublinear_tf=True
    )
    
    X_time_text = time_vectorizer.fit_transform(df_time['COMPLAINTS_PREPROCESSED'])
    
    # Numeric features
    time_numeric_features = ['AGE', 'SEX', 'COMPLAINTS_LENGTH', 'COMPLAINTS_WORD_COUNT',
                            'COMPLAINTS_AVG_WORD_LENGTH', 'AGE_GROUP', 'AGE_NORMALIZED',
                            'DIAGNOSIS_ENCODED', 'DIAGNOSIS_LENGTH', 'DIAGNOSIS_WORD_COUNT',
                            'HAS_ICD10', 'ICD10_LENGTH']
    time_keyword_features = [f'HAS_{kw.upper()}_TIME' for kw in MEDICAL_KEYWORDS]
    all_time_numeric = time_numeric_features + time_keyword_features
    
    X_time_numeric = df_time[all_time_numeric].values
    
    # Scale numeric features
    time_scaler = StandardScaler()
    X_time_numeric_scaled = time_scaler.fit_transform(X_time_numeric)
    
    # Combine features
    X_time = scipy.sparse.hstack([X_time_numeric_scaled, X_time_text])
    y_time = df_time['TIME_TO_CATER'].values
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_time, y_time, test_size=0.2, random_state=42
    )
    
    
    
    # Train models
    time_models = {}
    time_scores = {}
    
    # Random Forest
    rf_time = RandomForestRegressor(
        n_estimators=300,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    rf_time.fit(X_train, y_train)
    rf_pred = rf_time.predict(X_test)
    time_models['RF'] = rf_time
    time_scores['RF'] = {
        'MAE': mean_absolute_error(y_test, rf_pred),
        'R2': r2_score(y_test, rf_pred)
    }
    
    gb_time = GradientBoostingRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        min_samples_split=5,
        subsample=0.8,
        random_state=42,
        verbose=0
    )
    gb_time.fit(X_train, y_train)
    gb_pred = gb_time.predict(X_test)
    time_models['GB'] = gb_time
    time_scores['GB'] = {
        'MAE': mean_absolute_error(y_test, gb_pred),
        'R2': r2_score(y_test, gb_pred)
    }
    
    # Select best model
    best_model_name = min(time_scores.items(), key=lambda x: x[1]['MAE'])[0]
    best_model = time_models[best_model_name]
    best_scores = time_scores[best_model_name]
    
    
    # Save models to Django ml_models directory
    models_dir = get_ml_models_path()
    os.makedirs(models_dir, exist_ok=True)

    joblib.dump(best_model, os.path.join(models_dir, 'time_prediction_model_advanced.pkl'))
    joblib.dump(time_vectorizer, os.path.join(models_dir, 'time_vectorizer_advanced.pkl'))
    joblib.dump(time_scaler, os.path.join(models_dir, 'time_scaler_advanced.pkl'))
    joblib.dump(diag_time_encoder, os.path.join(models_dir, 'diag_time_encoder_advanced.pkl'))
    print("Training Completed")
    
    return {
        "status": "Training completed from CSV"
    }

