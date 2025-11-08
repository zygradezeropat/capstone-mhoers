import os
import re
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

# Optional models
XGB_AVAILABLE = LGBM_AVAILABLE = CATBOOST_AVAILABLE = False
try:
    from xgboost import XGBRegressor
    XGB_AVAILABLE = True
except Exception:
    pass
try:
    from lightgbm import LGBMRegressor
    LGBM_AVAILABLE = True
except Exception:
    pass
try:
    from catboost import CatBoostRegressor
    CATBOOST_AVAILABLE = True
except Exception:
    pass

import joblib

# ========= Config =========
CSV_CANDIDATES = [
    os.path.join('MHOERS', 'sample_datasets', 'New_corella_datasets_5.csv'),
    os.path.join('sample_datasets', 'New_corella_datasets_5.csv'),
    'New_corella_datasets_5.csv'
]
MEDICAL_KEYWORDS = [
    'fever','cough','pain','headache','dizziness','nausea','vomiting','diarrhea','rash','bleeding','swelling',
    'chest','breathing','difficulty','stomach','abdominal','throat','nose','ear','eye','back','joint','muscle',
    'tired','weak','chills','sweat','cold','hot','burning'
]
MEDICAL_SYNONYMS = {
    r'\bfever\b': 'fever', r'\bhigh temp\b': 'fever', r'\btemp\b': 'fever',
    r'\bcough\b': 'cough', r'\bhead ache\b': 'headache', r'\bheadache\b': 'headache',
    r'\bpain\b': 'pain', r'\bache\b': 'pain', r'\bdizzy\b': 'dizziness', r'\bdizziness\b': 'dizziness',
    r'\bvomit\b': 'vomiting', r'\bvomiting\b': 'vomiting', r'\bnausea\b': 'nausea',
}

# ========= Helpers =========
def preprocess_text_advanced(text: str) -> str:
    if pd.isna(text) or text == '':
        return ''
    text = str(text).lower().strip()
    for pattern, replacement in MEDICAL_SYNONYMS.items():
        text = re.sub(pattern, replacement, text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return ' '.join(text.split())

def assign_age_group(age):
    if pd.isna(age) or age is None:
        return 2
    try:
        age = float(age)
        if age <= 18: return 0
        elif age <= 35: return 1
        elif age <= 50: return 2
        elif age <= 65: return 3
        else: return 4
    except Exception:
        return 2

def parse_hms(s):
    if pd.isna(s): return None
    s = str(s).strip()
    try:
        # HH:MM:SS or HH:MM
        parts = s.split(':')
        h = int(float(parts[0])); m = int(float(parts[1])); sec = int(float(parts[2])) if len(parts) > 2 else 0
        return h*3600 + m*60 + sec
    except Exception:
        return None

def compute_duration_hours(admission, discharge):
    a = parse_hms(admission); d = parse_hms(discharge)
    if a is None or d is None: return np.nan
    diff = d - a
    if diff < 0: diff += 24*3600  # midnight crossover
    hours = diff / 3600.0
    # filter unrealistic durations (<5 min or >4 hrs)
    if hours < 0.0833 or hours > 4.0:
        return np.nan
    return hours

def find_csv_path():
    for p in CSV_CANDIDATES:
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"CSV not found. Tried: {CSV_CANDIDATES}")

# ========= Load =========
csv_path = find_csv_path()
print(f"📂 Loading: {csv_path}")
df = pd.read_csv(csv_path, encoding='latin1')

required_cols = ['ADMISSION_TIME','DISCHARGE','COMPLAINTS','DIAGNOSIS','AGE','SEX','ICD10 CODE']
missing = [c for c in required_cols if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

# ========= Target from real times =========
df['TIME_TO_CATER'] = df.apply(lambda r: compute_duration_hours(r['ADMISSION_TIME'], r['DISCHARGE']), axis=1)

# ========= Clean/filter =========
df = df[df['TIME_TO_CATER'].notna()].copy()
df = df[(pd.to_numeric(df['AGE'], errors='coerce') >= 0) & (pd.to_numeric(df['AGE'], errors='coerce') <= 120)].copy()

# ========= Feature engineering - Only ICD10 CODE, ADMISSION_TIME, DISCHARGE, AGE =========

# AGE - normalize
df['AGE'] = pd.to_numeric(df['AGE'], errors='coerce').fillna(df['AGE'].median())

# ADMISSION_TIME - extract hour and minutes as features
df['ADMISSION_HOUR'] = pd.to_datetime(df['ADMISSION_TIME'], format='%H:%M:%S', errors='coerce').dt.hour.fillna(0).astype(int)
df['ADMISSION_MINUTE'] = pd.to_datetime(df['ADMISSION_TIME'], format='%H:%M:%S', errors='coerce').dt.minute.fillna(0).astype(int)
# Convert to minutes since midnight for continuous feature
df['ADMISSION_TIME_MINUTES'] = df['ADMISSION_HOUR'] * 60 + df['ADMISSION_MINUTE']

# DISCHARGE - extract hour and minutes as features
df['DISCHARGE_HOUR'] = pd.to_datetime(df['DISCHARGE'], format='%H:%M:%S', errors='coerce').dt.hour.fillna(0).astype(int)
df['DISCHARGE_MINUTE'] = pd.to_datetime(df['DISCHARGE'], format='%H:%M:%S', errors='coerce').dt.minute.fillna(0).astype(int)
# Convert to minutes since midnight for continuous feature
df['DISCHARGE_TIME_MINUTES'] = df['DISCHARGE_HOUR'] * 60 + df['DISCHARGE_MINUTE']

# ICD10 CODE - encode as categorical (use LabelEncoder)
df['ICD10_CODE_CLEAN'] = df['ICD10 CODE'].fillna('UNKNOWN').astype(str).str.strip()
icd10_encoder = LabelEncoder()
df['ICD10_ENCODED'] = icd10_encoder.fit_transform(df['ICD10_CODE_CLEAN'])

# Build feature matrix - only the 4 requested features
# AGE + ADMISSION_TIME + DISCHARGE + ICD10_CODE
numeric_features = ['AGE', 'ADMISSION_TIME_MINUTES', 'DISCHARGE_TIME_MINUTES', 'ICD10_ENCODED']
X_numeric = df[numeric_features].values

scaler = StandardScaler()
X_numeric_scaled = scaler.fit_transform(X_numeric)

# No text features, just numeric
X = X_numeric_scaled
y = df['TIME_TO_CATER'].values

# Update variable names for compatibility (no vectorizer needed)
vectorizer = None
diag_vectorizer = None
diag_encoder = icd10_encoder  # Use ICD10 encoder as the encoder for saving

print(f"✅ Data ready. Samples: {X.shape[0]}, Features: {X.shape[1]}")
print(f"   Target (hours) min={y.min():.2f}, max={y.max():.2f}, mean={y.mean():.2f}")

# ========= Split =========
# Prefer a time-based split to reduce leakage and stabilize R²
if 'DATE' in df.columns:
    df['_DATE_PARSED'] = pd.to_datetime(df['DATE'], errors='coerce')
    if df['_DATE_PARSED'].notna().sum() >= int(0.5 * len(df)):
        order = np.argsort(df['_DATE_PARSED'].fillna(pd.Timestamp.min).values)
        cutoff = int(0.8 * len(order))
        train_idx = order[:cutoff]
        test_idx = order[cutoff:]
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
    else:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
else:
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

# ========= Train models =========
models = {}
results = {}

def eval_and_store(name, model, Xtr, ytr, Xte, yte):
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    mae = mean_absolute_error(yte, pred)
    # RMSE for older sklearn versions without 'squared' parameter
    rmse = np.sqrt(mean_squared_error(yte, pred))
    r2 = r2_score(yte, pred)
    models[name] = model
    results[name] = {'MAE': mae, 'RMSE': rmse, 'R2': r2, 'pred': pred}
    print(f"{name}: MAE={mae:.3f}h ({mae*60:.1f}m), RMSE={rmse:.3f}h ({rmse*60:.1f}m), R²={r2:.3f} ({r2*100:.1f}%)")

print("\n🔧 Training models...")
eval_and_store("Random Forest", RandomForestRegressor(
    n_estimators=300, max_depth=20, min_samples_split=5, min_samples_leaf=2, random_state=42, n_jobs=-1
), X_train, y_train, X_test, y_test)

eval_and_store("Gradient Boosting", GradientBoostingRegressor(
    n_estimators=200, max_depth=5, learning_rate=0.1, min_samples_split=5, subsample=0.8, random_state=42
), X_train, y_train, X_test, y_test)

if XGB_AVAILABLE:
    eval_and_store("XGBoost", XGBRegressor(
        n_estimators=300, max_depth=6, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
        min_child_weight=3, gamma=0.1, reg_alpha=0.1, reg_lambda=1.0, random_state=42, n_jobs=-1, verbosity=0
    ), X_train, y_train, X_test, y_test)

if LGBM_AVAILABLE:
    eval_and_store("LightGBM", LGBMRegressor(
        n_estimators=300, max_depth=6, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
        min_child_samples=20, reg_alpha=0.1, reg_lambda=1.0, random_state=42, n_jobs=-1, verbosity=-1 
    ), X_train, y_train, X_test, y_test)

if CATBOOST_AVAILABLE:
    eval_and_store("CatBoost", CatBoostRegressor(
        iterations=300, depth=6, learning_rate=0.05, loss_function='RMSE', random_seed=42, verbose=False
    ), X_train, y_train, X_test, y_test)

# ========= Compare =========
res_df = pd.DataFrame(results).T[['MAE','RMSE','R2']].sort_values('MAE')
print("\n📊 Model comparison:")
print(res_df)

# Also show R² as percentage per model
print("\n📊 R² as percentage per model:")
for model_name, row in res_df.iterrows():
    print(f" - {model_name}: {row['R2']*100:.1f}%")

best_model_name = res_df.index[0]
best_model = models[best_model_name]
best_pred = results[best_model_name]['pred']
print(f"\n🏆 Best: {best_model_name} | MAE={res_df.loc[best_model_name,'MAE']:.3f}h ({res_df.loc[best_model_name,'MAE']*60:.1f}m), R²={res_df.loc[best_model_name,'R2']:.3f} ({res_df.loc[best_model_name,'R2']*100:.1f}%)")

# Feature importance (text output only)
if hasattr(best_model, 'feature_importances_'):
    importances = best_model.feature_importances_
    feature_names = numeric_features
    idx = np.argsort(importances)[::-1]
    feats = [feature_names[i] for i in idx]
    scores = importances[idx]
    print(f"\n📊 Feature Importance ({best_model_name}):")
    for feat, score in zip(feats, scores):
        print(f"   {feat}: {score:.4f}")

# ========= Save components =========
os.makedirs('ml_outputs', exist_ok=True)
model_path = os.path.join('ml_outputs', f'time_prediction_model_{best_model_name.lower().replace(" ","_")}.pkl')
scaler_path = os.path.join('ml_outputs', 'time_scaler.pkl')
enc_path = os.path.join('ml_outputs', 'icd10_encoder.pkl')

joblib.dump(best_model, model_path)
joblib.dump(scaler, scaler_path)
joblib.dump(diag_encoder, enc_path)

print("\n💾 Saved:")
print(f" - Model: {model_path}")
print(f" - Scaler: {scaler_path}")
print(f" - ICD10 encoder: {enc_path}")
print(f"\n📊 Features used: {numeric_features}")

# Optional: auto-download in Colab
try:
    from google.colab import files
    files.download(model_path)
    files.download(scaler_path)
    files.download(enc_path)
except Exception:
    pass

print("\n✅ Done.")