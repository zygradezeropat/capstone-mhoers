# =============================
 #
 # TIME-TO-CATER PREDICTION MODEL (Improved)
 #
 # =============================

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from xgboost import XGBRegressor
from datetime import datetime


# Step 2: Load dataset
DATA_PATH = os.path.join("MHOERS", "sample_datasets", "New_corella_datasets_5.csv")
df = pd.read_csv(DATA_PATH)
print("✅ Dataset loaded. Shape:", df.shape)


# Step 3: Convert time columns safely
def to_time_flexible(x):
    """Convert time strings in HH:MM or HH:MM:SS format"""
    if pd.isna(x):
        return np.nan
    s = str(x).strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    # Fallback: try pandas
    try:
        dt = pd.to_datetime(s, format=None, errors="coerce")
        return pd.NaT if pd.isna(dt) else dt.to_pydatetime()
    except Exception:
        return np.nan


df['ADMISSION_TIME'] = df['ADMISSION_TIME'].apply(to_time_flexible)
df['DISCHARGE'] = df['DISCHARGE'].apply(to_time_flexible)


# Step 4: Compute time_cater in hours
def diff_hours(a, b):
    if pd.isna(a) or pd.isna(b):
        return np.nan
    delta = b - a
    # If negative, assume discharge is next day
    if getattr(delta, 'total_seconds', None) is None:
        return np.nan
    seconds = delta.total_seconds()
    if seconds < 0:
        seconds += 24 * 3600
    return seconds / 3600.0


df['time_cater'] = [diff_hours(a, b) for a, b in zip(df['ADMISSION_TIME'], df['DISCHARGE'])]

# Drop invalid or negative times
before = df.shape[0]
df = df.dropna(subset=['time_cater'])
df = df[df['time_cater'] >= 0]
after = df.shape[0]
print(f"🧹 Removed {before - after} invalid rows. Remaining rows: {after}")
if df.empty:
    raise ValueError("⚠️ All rows invalid. Check ADMISSION_TIME and DISCHARGE formats in your CSV.")


# Step 5: Feature Engineering (Extract hour)
df['HOUR_ADMITTED'] = df['ADMISSION_TIME'].apply(lambda x: x.hour if pd.notnull(x) else np.nan)


# Step 6: Select relevant features
features = ['AGE', 'SEX', 'ICD10 CODE', 'DIAGNOSIS', 'HOUR_ADMITTED']
target = 'time_cater'
data = df[features + [target]].copy()


# Step 7: Handle missing values
data = data.fillna('Unknown')


# Step 8: Encode categorical variables (skip numeric)
label_encoders = {}
for col in data.columns:
    if data[col].dtype == 'object':
        le = LabelEncoder()
        data[col] = le.fit_transform(data[col].astype(str))
        label_encoders[col] = le


# Step 9: Split dataset
X = data.drop(columns=[target])
y = data[target]
if len(data) < 5:
    raise ValueError("⚠️ Not enough samples after cleaning. Need at least 5 rows to train.")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print("\n✅ Train/Test Split Done.")
print("Training size:", X_train.shape)
print("Testing size:", X_test.shape)


# Step 10: Initialize models
models = {
    "Random Forest": RandomForestRegressor(n_estimators=200, random_state=42),
    "Gradient Boosting": GradientBoostingRegressor(n_estimators=300, learning_rate=0.05, random_state=42),
    "XGBoost": XGBRegressor(n_estimators=500, learning_rate=0.05, max_depth=6, subsample=0.8, colsample_bytree=0.8, random_state=42, verbosity=0)
}


# Step 11: Train and evaluate each model
results = []
for name, model in models.items():
    print(f"\n🚀 Training {name}...")
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    results.append({
        "Model": name,
        "MSE": round(mse, 4),
        "MAE": round(mae, 4),
        "R²": round(r2, 4)
    })


# Step 12: Show results
results_df = pd.DataFrame(results)
print("\n📊 Model Performance Comparison:")
print(results_df)


# Step 13: Identify best model
best_model = results_df.sort_values(by='R²', ascending=False).iloc[0]
print(f"\n🏆 Best Model: {best_model['Model']} with R² = {best_model['R²']}")

import pandas as pd
