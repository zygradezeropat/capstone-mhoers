# How Disease Peak Analytics Works - Complete Explanation

## Overview
This system predicts which diseases will peak each month in 2025 based on patterns learned from 2023-2024 historical referral data.

---

## Step-by-Step Process

### **Step 1: Data Loading** 📊
```python
Referral.objects.filter(created_at__year__in=[2023, 2024])
```

**What happens:**
- Queries all `Referral` records from 2023-2024
- Excludes records without patients or diagnoses
- Uses `select_related('patient')` to efficiently load related patient data

**Data Retrieved:**
- Patient age (calculated from `date_of_birth`)
- Patient sex
- Chief complaint or symptoms
- Initial/final diagnosis
- **ICD10 code** (from `icd10_code` field if you added it, or extracted from diagnosis text)

---

### **Step 2: Data Conversion** 🔄
```python
queryset_to_dataframe(referrals)
```

**What happens:**
- Converts Django QuerySet to pandas DataFrame
- Maps each referral to a row with columns: `AGE`, `SEX`, `COMPLAINTS`, `DIAGNOSIS`, `ICD10 CODE`
- **ICD10 Code Priority:**
  1. First checks if `referral.icd10_code` field exists and has a value
  2. If not, extracts ICD10 code from diagnosis text using regex
  3. If still not found, uses first 50 chars of diagnosis as proxy

**Example:**
```
Referral → {
    'AGE': 45,
    'SEX': 'Male',
    'COMPLAINTS': 'Chest pain and shortness of breath',
    'DIAGNOSIS': 'Acute myocardial infarction (I21.9)',
    'ICD10 CODE': 'I21.9'  # Extracted or from field
}
```

---

### **Step 3: Identify Top Diseases** 🔍
```python
get_top_diseases(df, top_n=5)
```

**What happens:**
- Counts frequency of each ICD10 code
- Selects the top N most common diseases (default: 5)
- Filters dataset to only include these top diseases

**Why?**
- Focuses analysis on diseases that actually occur in your data
- Reduces noise from rare diseases
- Makes predictions more meaningful

**Example Output:**
```
Top 5 ICD10 codes found: ['T14.1', 'W54.99', 'J06.9', 'Z00', 'I10.1']
```

---

### **Step 4: Data Encoding** 🔧
```python
LabelEncoder() for each feature
```

**What happens:**
- Converts text/categorical data to numbers (ML models need numbers)
- Creates separate encoders for: `AGE`, `SEX`, `COMPLAINTS`, `DIAGNOSIS`
- Creates target encoder for `ICD10 CODE`

**Example:**
```
Before: SEX = "Male" → After: SEX = 0
Before: SEX = "Female" → After: SEX = 1
Before: ICD10 = "T14.1" → After: ICD10 = 2
```

**Why encoding?**
- Machine learning algorithms work with numerical data
- Each unique value gets a unique number
- Encoders remember the mapping to decode predictions later

---

### **Step 5: Train/Test Split** 📈
```python
train_test_split(X, y, test_size=0.2)
```

**What happens:**
- Splits data: 80% for training, 20% for testing
- Training set: Used to teach the model
- Test set: Used to evaluate how well the model learned

**Why split?**
- Tests if model can predict on new, unseen data
- Prevents overfitting (memorizing instead of learning patterns)

---

### **Step 6: Model Training** 🧠
```python
RandomForestClassifier, GradientBoostingClassifier, LinearSVC
```

**What happens:**
- Trains 3 different machine learning models:
  1. **Random Forest**: Ensemble of decision trees
  2. **Gradient Boosting**: Sequentially improves predictions
  3. **Linear SVM**: Finds best separating boundary

**How each model learns:**
- Analyzes patterns: "Patients aged 40-60 with chest pain → I21.9"
- "Female patients with fever → J06.9"
- Builds rules to predict disease from patient features

**Evaluation Metrics:**
- **Accuracy**: % of correct predictions
- **Macro F1**: Average performance across all diseases
- **Weighted F1**: Performance weighted by disease frequency

---

### **Step 7: Select Best Model** 🏆
```python
best_model = models[best_model_name]
```

**What happens:**
- Compares all 3 models' accuracy scores
- Selects the one with highest accuracy
- This model will be used for 2025 predictions

**Example:**
```
Random Forest: 0.85 accuracy
Gradient Boosting: 0.82 accuracy
Linear SVM: 0.78 accuracy
→ Random Forest selected
```

---

### **Step 8: Simulate 2025 Data** 🗓️
```python
Generate 100 random samples per month
```

**What happens:**
- Creates synthetic patient data for each month in 2025
- For each month, generates N samples (default: 100) with:
  - Random age (1-90)
  - Random sex (Male/Female)
  - Random complaint (from historical data)
  - Random diagnosis (from historical data)

**Why simulate?**
- We don't have real 2025 data yet
- Uses realistic ranges based on historical patterns
- Creates diverse scenarios for prediction

**Example:**
```
January: 100 simulated patients
February: 100 simulated patients
...
December: 100 simulated patients
Total: 1,200 simulated patients
```

---

### **Step 9: Encode Simulated Data** 🔢
```python
Apply same encoders to simulated data
```

**What happens:**
- Uses the same encoders from Step 4
- Converts simulated text data to numbers
- Handles new values not seen in training (maps to closest match)

**Why same encoders?**
- Model expects same format as training data
- Ensures consistency

---

### **Step 10: Make Predictions** 🔮
```python
best_model.predict(sim_df[features])
```

**What happens:**
- For each simulated patient, predicts their disease (ICD10 code)
- Model uses learned patterns: age + sex + complaints + diagnosis → predicted disease

**Example:**
```
Simulated Patient:
  AGE: 45 (encoded as 12)
  SEX: Male (encoded as 0)
  COMPLAINTS: "Chest pain" (encoded as 5)
  DIAGNOSIS: "Cardiac" (encoded as 3)
  
Model Prediction: I21.9 (encoded as 2)
```

---

### **Step 11: Decode Predictions** 🔄
```python
reverse_encoder.map(predicted_encoded)
```

**What happens:**
- Converts encoded predictions back to ICD10 codes
- Maps numbers back to disease labels

**Example:**
```
Encoded: 2 → Decoded: "I21.9"
Encoded: 0 → Decoded: "T14.1"
```

---

### **Step 12: Identify Monthly Peaks** 📅
```python
groupby(["Month", "Predicted_Disease_Label"]).size()
```

**What happens:**
- Counts how many times each disease was predicted per month
- Groups by month and disease
- Sorts by count (highest first)

**Example:**
```
January:
  I21.9: 35 predictions
  J06.9: 28 predictions
  T14.1: 22 predictions
  → Peak: I21.9 (35 cases)
```

---

### **Step 13: Final Output** ✅
```python
peak_disease_per_month
```

**What happens:**
- Extracts the top disease for each month
- Displays results in a table

**Final Output Example:**
```
Month      | Predicted_Disease_Label | Count
-----------|-------------------------|-------
January    | I21.9                   | 35
February   | J06.9                   | 42
March      | T14.1                   | 38
...
```

---

## Key Concepts Explained

### **What is Machine Learning Here?**
The model learns patterns like:
- "Older patients with chest pain often have cardiac issues (I21.9)"
- "Young patients with fever often have respiratory infections (J06.9)"
- "Accidents (T14.1) are more common in certain demographics"

### **Why Predict Monthly Peaks?**
- **Resource Planning**: Know which diseases to prepare for each month
- **Staffing**: Allocate specialists based on predicted peaks
- **Supplies**: Stock medications for predicted high-demand diseases
- **Prevention**: Focus public health campaigns on upcoming peaks

### **How Accurate Are Predictions?**
- Depends on:
  - Amount of historical data (more = better)
  - Quality of ICD10 codes (direct field > extracted > proxy)
  - Consistency in diagnosis patterns
- Model accuracy is shown in Step 6 (typically 70-90% for good datasets)

### **What If I Don't Have ICD10 Codes?**
The system handles this:
1. Uses `icd10_code` field if you added it
2. Extracts from diagnosis text using regex
3. Falls back to diagnosis text as proxy

---

## Data Flow Diagram

```
Django Models (Referral + Patient)
    ↓
QuerySet (2023-2024 data)
    ↓
DataFrame (pandas)
    ↓
Top Diseases Filter
    ↓
Feature Encoding (text → numbers)
    ↓
Train/Test Split
    ↓
Model Training (3 models)
    ↓
Best Model Selection
    ↓
2025 Simulation (synthetic data)
    ↓
Predictions (encoded)
    ↓
Decode Predictions
    ↓
Monthly Peak Analysis
    ↓
Final Results (disease peaks per month)
```

---

## Example Walkthrough

**Input Data:**
- 1,000 referrals from 2023-2024
- Top 5 diseases: T14.1, W54.99, J06.9, Z00, I10.1

**Process:**
1. Load 1,000 records → Filter to 800 with top diseases
2. Train models → Random Forest wins (85% accuracy)
3. Simulate 1,200 patients for 2025 (100/month × 12 months)
4. Predict diseases for each simulated patient
5. Count predictions per month

**Output:**
```
January: J06.9 (respiratory) - 42 cases predicted
February: T14.1 (injuries) - 38 cases predicted
March: I10.1 (hypertension) - 35 cases predicted
...
```

This tells you: "Prepare for respiratory cases in January, injuries in February, etc."

---

## Tips for Better Results

1. **More Data**: More historical referrals = better predictions
2. **Consistent ICD10**: Use the `icd10_code` field consistently
3. **Quality Data**: Ensure diagnoses are accurate and complete
4. **Regular Updates**: Re-run predictions as new data comes in
5. **Validate**: Compare predictions with actual results to improve

---

## Questions?

The system is designed to be flexible and handle missing data gracefully. If you have questions about any step, the code is well-commented and follows this exact flow!

