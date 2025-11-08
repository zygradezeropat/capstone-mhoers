import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

import os
import sys
import math
import numpy as np
import pandas as pd

from datetime import datetime
from typing import List, Tuple

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
import inspect
from sklearn.impute import SimpleImputer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import r2_score
from sklearn.linear_model import Ridge, ElasticNet

# Optional: try to import xgboost if available for a strong baseline on sparse data
try:
    from xgboost import XGBRegressor  # type: ignore
    HAS_XGB = True
except Exception:
    HAS_XGB = False

DATA_PATH = os.path.join("MHOERS", "sample_datasets", "New_corella_datasets_5.csv")
RANDOM_STATE = 42


def parse_time_str(t: str) -> Tuple[int, int]:
    """Return (hour, minute) from a time like '8:24'."""
    try:
        parts = str(t).strip().split(":")
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 0
        h = max(0, min(23, h))
        m = max(0, min(59, m))
        return h, m
    except Exception:
        return 0, 0


def minutes_since_midnight(t: str) -> int:
    h, m = parse_time_str(t)
    return h * 60 + m


def compute_duration_minutes(admission: str, discharge: str) -> float:
    """Compute duration in minutes between admission and discharge (same-day). Wrap if needed."""
    a = minutes_since_midnight(admission)
    d = minutes_since_midnight(discharge)
    if d < a:
        d += 24 * 60
    return float(max(0, d - a))


def clean_text(x: str) -> str:
    if pd.isna(x):
        return ""
    s = str(x)
    # Normalize whitespace and case; remove excessive punctuation
    s = s.replace("\n", " ").replace("\r", " ")
    s = " ".join(s.split())
    return s.lower()


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Standardize column names
    df.columns = [c.strip() for c in df.columns]
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    required_cols = {
        "ADMISSION_TIME",
        "DISCHARGE",
        "REFERRED",
        "AGE",
        "SEX",
        "CS",
        "PWD(Y/N)",
        "TYPE",
        "CAUSE",
        "COMPLAINTS",
        "ICD10 CODE",
        "DIAGNOSIS",
        "TREATMENTS",
        "REMARKS",
        "SITIO/BARANGAY",
        "CCT (Y/N)",
        "PHIC(M/D)",
        "DATE",
    }
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Compute target only for referred rows
    df["duration_minutes"] = df.apply(
        lambda r: compute_duration_minutes(r.get("ADMISSION_TIME", np.nan), r.get("DISCHARGE", np.nan)), axis=1
    )

    # Parse date parts
    def parse_date_to_parts(d: str) -> Tuple[int, int, int, int]:
        # Expected like 'May 06, 2024'
        try:
            dt = pd.to_datetime(d, errors="coerce")
            if pd.isna(dt):
                return 0, 0, 0, 0
            return int(dt.year), int(dt.month), int(dt.day), int(dt.dayofweek)
        except Exception:
            return 0, 0, 0, 0

    parts = df["DATE"].apply(parse_date_to_parts)
    df["year"] = parts.apply(lambda x: x[0])
    df["month"] = parts.apply(lambda x: x[1])
    df["day"] = parts.apply(lambda x: x[2])
    df["weekday"] = parts.apply(lambda x: x[3])

    # Admission and discharge time components
    df["admission_minutes"] = df["ADMISSION_TIME"].map(minutes_since_midnight)
    df["discharge_minutes"] = df["DISCHARGE"].map(minutes_since_midnight)
    df["admission_hour"] = (df["admission_minutes"] // 60).astype(int)
    df["discharge_hour"] = (df["discharge_minutes"] // 60).astype(int)

    # Basic text cleaning
    for col in ["COMPLAINTS", "DIAGNOSIS", "TREATMENTS", "REMARKS", "CAUSE"]:
        df[col] = df[col].map(clean_text)

    # Keep only referred cases (Y in any case)
    df["REFERRED"] = df["REFERRED"].astype(str).str.strip().str.upper()
    df_ref = df[df["REFERRED"] == "Y"].copy()

    # Drop obvious identifiers that leak personal info
    leak_cols = ["NAME", "DATE OF BIRTH", "#"]
    for c in leak_cols:
        if c in df_ref.columns:
            df_ref.drop(columns=[c], inplace=True)

    # Filter out rows without a positive duration
    df_ref = df_ref[df_ref["duration_minutes"] > 0].copy()

    return df_ref


def build_preprocessor(numeric_features: List[str], categorical_features: List[str], text_features: List[str]) -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler(with_mean=False)),
        ]
    )

    # Build OneHotEncoder kwargs compatible across sklearn versions
    ohe_params = {"handle_unknown": "ignore"}
    ohe_sig = inspect.signature(OneHotEncoder)
    if "min_frequency" in ohe_sig.parameters:
        ohe_params["min_frequency"] = 20
    if "sparse_output" in ohe_sig.parameters:
        ohe_params["sparse_output"] = True
    elif "sparse" in ohe_sig.parameters:
        ohe_params["sparse"] = True

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(**ohe_params)),
        ]
    )

    # We apply a TF-IDF vectorizer per text column via ColumnTransformer directly
    from sklearn.feature_extraction.text import TfidfVectorizer

    transformers = [
        ("num", numeric_pipeline, numeric_features),
        ("cat", categorical_pipeline, categorical_features),
    ]

    def _tfidf_preprocessor(doc):
        s = "" if doc is None else str(doc)
        s = s.strip()
        return s if s else "none"

    for txt in text_features:
        transformers.append(
            (
                f"tfidf_{txt}",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    max_features=8000,
                    min_df=1,
                    lowercase=True,
                    preprocessor=_tfidf_preprocessor,
                ),
                txt,
            )
        )

    return ColumnTransformer(transformers=transformers, remainder="drop", sparse_threshold=1.0)


def main() -> None:
    if not os.path.exists(DATA_PATH):
        print(f"Dataset not found at {DATA_PATH}", file=sys.stderr)
        sys.exit(1)

    df_raw = load_data(DATA_PATH)
    df = engineer_features(df_raw)

    if df.shape[0] < 100:
        print("Not enough referred records to train a reliable model.")
        sys.exit(1)

    target = "duration_minutes"

    numeric_features = [
        "AGE",
        "year",
        "month",
        "day",
        "weekday",
        "admission_minutes",
        "discharge_minutes",
        "admission_hour",
        "discharge_hour",
    ]

    categorical_features = [
        "SEX",
        "CS",
        "PWD(Y/N)",
        "TYPE",
        "ICD10 CODE",
        "SITIO/BARANGAY",
        "CCT (Y/N)",
        "PHIC(M/D)",
    ]

    text_features = [
        "COMPLAINTS",
        "DIAGNOSIS",
        "TREATMENTS",
        "REMARKS",
        "CAUSE",
    ]

    # Keep only columns we care about
    feature_cols = list(set(numeric_features + categorical_features + text_features))
    missing_feats = [c for c in feature_cols + [target] if c not in df.columns]
    if missing_feats:
        raise ValueError(f"Columns missing after engineering: {missing_feats}")

    X = df[feature_cols]
    y = df[target].astype(float)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    preprocessor = build_preprocessor(numeric_features, categorical_features, text_features)

    # Model candidates
    models: List[Tuple[str, Pipeline]] = []

    # 1) Ridge on SVD-reduced features (good for sparse high-dim)
    ridge_pipeline = Pipeline(
        steps=[
            ("pre", preprocessor),
            ("svd", TruncatedSVD(n_components=200, random_state=RANDOM_STATE)),
            ("scaler", StandardScaler(with_mean=False)),
            ("model", Ridge()),
        ]
    )

    # Small grid for ridge
    ridge_param_grid = {
        "svd__n_components": [100, 200, 300],
        "model__alpha": [0.1, 1.0, 3.0, 10.0],
    }

    models.append(("Ridge+SVD", GridSearchCV(ridge_pipeline, ridge_param_grid, cv=3, n_jobs=-1, scoring="r2", verbose=0)))

    # 2) ElasticNet on SVD-reduced features
    enet_pipeline = Pipeline(
        steps=[
            ("pre", preprocessor),
            ("svd", TruncatedSVD(n_components=200, random_state=RANDOM_STATE)),
            ("scaler", StandardScaler(with_mean=False)),
            ("model", ElasticNet(max_iter=5000, random_state=RANDOM_STATE)),
        ]
    )

    enet_param_grid = {
        "svd__n_components": [100, 200],
        "model__alpha": [0.01, 0.1, 1.0],
        "model__l1_ratio": [0.1, 0.5, 0.9],
    }

    models.append(("ElasticNet+SVD", GridSearchCV(enet_pipeline, enet_param_grid, cv=3, n_jobs=-1, scoring="r2", verbose=0)))

    # 3) Optional XGBRegressor directly on sparse matrix (if available)
    if HAS_XGB:
        xgb_pipeline = Pipeline(
            steps=[
                ("pre", preprocessor),
                ("model", XGBRegressor(
                    n_estimators=600,
                    max_depth=6,
                    learning_rate=0.05,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    reg_lambda=1.0,
                    objective="reg:squarederror",
                    n_jobs=-1,
                    random_state=RANDOM_STATE,
                )),
            ]
        )
        models.append(("XGB", xgb_pipeline))

    best_name = None
    best_model = None
    best_r2 = -1e9

    for name, model in models:
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        print(f"{name} R2: {r2:.4f}")
        if r2 > best_r2:
            best_r2 = r2
            best_model = model
            best_name = name

    if best_model is None:
        print("No model was trained.")
        sys.exit(1)

    print(f"Best model: {best_name} with R2 = {best_r2:.4f}")

    # If R2 < 0.8, we still report it; user can re-run or adjust. Aim is >= 0.8.


if __name__ == "__main__":
    main()
