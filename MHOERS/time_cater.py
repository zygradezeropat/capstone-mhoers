import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore")

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.model_selection import KFold
from sklearn.model_selection import GridSearchCV

# -----------------------
# Load dataset
# -----------------------
df = pd.read_csv("C:/Users/User/Desktop/Project-Capstone/MHO-ERS/MHOERS/sample_datasets/MHO-NewCorella-data.csv", encoding='ISO-8859-1')

# -----------------------
# Clean and preprocess datetime
# -----------------------
df['SENT TIME'] = pd.to_datetime(df['SENT TIME'], errors='coerce', dayfirst=True)
df['CATERED TIME'] = pd.to_datetime(df['CATERED TIME'], errors='coerce', dayfirst=True)
df['SEX'] = df['SEX'].astype(str).str.strip().replace('', np.nan)
# Drop invalid datetime rows
df = df.dropna(subset=['SENT TIME', 'CATERED TIME'])

# Compute catered duration in minutes
df['Catered_Duration'] = (df['CATERED TIME'] - df['SENT TIME']).dt.total_seconds() / 60

# -----------------------
# Feature Engineering
# -----------------------
df['Sent_Hour'] = df['SENT TIME'].dt.hour
df['Sent_Weekday'] = df['SENT TIME'].dt.weekday
df['Is_Weekend'] = df['Sent_Weekday'].isin([5, 6]).astype(int)
df['Catered_Hour'] = df['CATERED TIME'].dt.hour


# -----------------------
# Clean categorical columns
# -----------------------
cat_cols = ['COMPLAINTS', 'ICD10 CODE', 'SITIO/BARANGAY']
for col in cat_cols:
    df[col] = df[col].astype(str).str.strip().replace('', np.nan)

# -----------------------
# Remove rows with missing important data
# -----------------------
important_cols = ['AGE', 'ICD10 CODE', 'COMPLAINTS', 'SITIO/BARANGAY', 'SEX']
df = df.dropna(subset=important_cols)

# -----------------------
# Add Urgency_Level based on ICD10 CODE and AGE
# -----------------------
def determine_urgency(icd_code, age):
    if pd.isna(icd_code) or pd.isna(age):
        return 'Unknown'
    icd_prefix = icd_code.strip().upper()[:1]
    if (age <= 5 or age >= 65) and icd_prefix in ['I', 'J', 'A']:
        return 'High'
    elif icd_prefix in ['K', 'N', 'E']:
        return 'Medium'
    elif 20 <= age <= 60 and icd_prefix in ['Z', 'H', 'M', 'L']:
        return 'Low'
    else:
        return 'Medium'

df['Urgency_Level'] = df.apply(lambda row: determine_urgency(row['ICD10 CODE'], row['AGE']), axis=1)

df = df[df['Catered_Duration'] > 0]
df = df.drop(['#', 'DATE', 'PHIC(M/D)', 'NAME', 'DATE OF BIRTH', 'TYPE', 'CAUSE', 'TREATMENTS', 'REMARKS', 'SENT TIME', 'CATERED TIME'], axis=1)

X = df.drop("Catered_Duration", axis=1)
y = df["Catered_Duration"]


categorical_features = ["COMPLAINTS", "Urgency_Level", "SITIO/BARANGAY", "ICD10 CODE", "SEX"]
numeric_features = ["AGE", "Sent_Hour", "Catered_Hour", "Sent_Weekday", "Is_Weekend"]

preprocessor = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
    ('num', StandardScaler(), numeric_features)
])



models = {
    "LinearRegression": LinearRegression(),
    "RandomForestRegressor": RandomForestRegressor(random_state=42),
    "GradientBoostingRegressor": GradientBoostingRegressor(random_state=42)
}

rf_grid = {
    'regressor__n_estimators': [100, 200],
    'regressor__max_depth': [None, 10]
}
gb_grid = {
    'regressor__n_estimators': [100, 200],
    'regressor__learning_rate': [0.05, 0.1]
}

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


for name, model in models.items():
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', model)
    ])
    if name == "RandomForestRegressor":
        grid = GridSearchCV(pipeline, rf_grid, cv=3, scoring='r2', n_jobs=-1)
        grid.fit(X_train, y_train)
        best_model = grid.best_estimator_
    
    elif name == "GradientBoostingRegressor":
        grid = GridSearchCV(pipeline, gb_grid, cv=3, scoring='r2', n_jobs=-1)
        grid.fit(X_train, y_train)
        best_model = grid.best_estimator_
     
    else:
        best_model = pipeline
        best_model.fit(X_train, y_train)

    y_pred = best_model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    print(f"\n{name} Performance:")
    print(f"  MAE: {mean_absolute_error(y_test, y_pred):.2f}")
    print(f"  RMSE: {np.sqrt(mean_squared_error(y_test, y_pred)):.2f}")
    print(f"  R² Score: {r2:.2f}")


   
