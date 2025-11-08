# Complete System Explanation: Disease Peak Analytics

## 📋 Overview
This system predicts which diseases will peak each month in 2025 by analyzing patterns from your 2023-2024 referral data using machine learning.

---

## 🗂️ **Your Data Models**

### **Patient Model** (`patients/models.py`)
```python
- patients_id (Primary Key)
- first_name, middle_name, last_name
- date_of_birth → Used to calculate age (property)
- sex → Male/Female
- facility → Links to Facility
```

**Key Property:**
- `age` - Automatically calculated from `date_of_birth`

### **Referral Model** (`referrals/models.py`)
```python
- referral_id (Primary Key)
- patient → ForeignKey to Patient
- chief_complaint → Patient's main complaint
- symptoms → Additional symptoms
- initial_diagnosis → First diagnosis
- final_diagnosis → Confirmed diagnosis (if available)
- ICD_code → ICD10 code field (you added this!)
- created_at → Date/time of referral
```

**Data Flow:**
```
Referral → Links to → Patient
  ↓                      ↓
ICD_code            age, sex
diagnosis
complaints
```

---

## 🔄 **How the System Works - Complete Flow**

### **PHASE 1: Data Collection** 📊

**Step 1.1: Query Historical Data**
```python
Referral.objects.filter(created_at__year__in=[2023, 2024])
```
- Gets all referrals from 2023-2024
- Excludes records without patients or diagnoses
- Uses `select_related('patient')` for efficient database queries

**What Gets Loaded:**
- Every referral with its related patient information
- Only referrals that have complete data (patient + diagnosis)

---

### **PHASE 2: Data Transformation** 🔄

**Step 2.1: Convert to DataFrame** (`queryset_to_dataframe`)
```python
For each referral:
  - Get patient.age (calculated property)
  - Get patient.sex
  - Get referral.chief_complaint or symptoms
  - Get referral.final_diagnosis or initial_diagnosis
  - Get ICD10 code (priority order):
      1. referral.ICD_code (your field)
      2. Extract from diagnosis text (regex)
      3. Use diagnosis text as fallback
```

**Example Transformation:**
```
Django Model:
  Referral.ICD_code = "T14.1"
  Referral.patient.age = 45
  Referral.patient.sex = "Male"
  Referral.chief_complaint = "Chest pain"

↓ Converts to ↓

DataFrame Row:
  AGE: 45
  SEX: "Male"
  COMPLAINTS: "Chest pain"
  DIAGNOSIS: "Acute injury"
  ICD10 CODE: "T14.1"
```

**ICD10 Code Priority:**
1. ✅ **First**: Uses `referral.ICD_code` field (if you filled it)
2. 🔍 **Second**: Extracts from diagnosis text using regex pattern `[A-Z]\d{2}(\.\d{1,2})?`
3. 📝 **Third**: Uses first 50 characters of diagnosis text

---

### **PHASE 3: Disease Selection** 🔍

**Step 3.1: Find Top Diseases** (`get_top_diseases`)
```python
Count frequency of each ICD10 CODE
Select top N (default: 5) most common diseases
Filter dataset to only include these diseases
```

**Why?**
- Focuses on diseases that actually occur in your system
- Reduces noise from rare diseases
- Makes predictions more meaningful

**Example:**
```
All Diseases Found:
  T14.1: 150 cases
  W54.99: 120 cases
  J06.9: 100 cases
  Z00: 80 cases
  I10.1: 75 cases
  X99.1: 5 cases (rare)

Top 5 Selected: [T14.1, W54.99, J06.9, Z00, I10.1]
Dataset filtered to only these 5 diseases
```

---

### **PHASE 4: Data Encoding** 🔢

**Step 4.1: Convert Text to Numbers**
```python
LabelEncoder for each feature:
  - AGE → Already numeric
  - SEX → "Male"=0, "Female"=1
  - COMPLAINTS → "Chest pain"=5, "Fever"=12, etc.
  - DIAGNOSIS → "Cardiac"=3, "Respiratory"=7, etc.
  - ICD10 CODE → "T14.1"=0, "J06.9"=1, etc.
```

**Why Encoding?**
- Machine learning models only understand numbers
- Each unique text value gets a unique number
- Encoders remember the mapping to decode later

**Example:**
```
Before Encoding:
  SEX: "Male"
  COMPLAINTS: "Chest pain"
  ICD10 CODE: "T14.1"

After Encoding:
  SEX: 0
  COMPLAINTS: 5
  ICD10 CODE: 0
```

---

### **PHASE 5: Model Training** 🧠

**Step 5.1: Split Data**
```python
80% → Training set (teach the model)
20% → Test set (evaluate the model)
```

**Step 5.2: Train Three Models**
```python
1. Random Forest
   - Creates many decision trees
   - Votes on final prediction
   - Good for complex patterns

2. Gradient Boosting
   - Sequentially improves predictions
   - Learns from mistakes
   - Very accurate

3. Linear SVM
   - Finds best separating boundary
   - Good for clear patterns
   - Fast training
```

**What Each Model Learns:**
The models analyze patterns like:
- "Patients aged 40-60 with chest pain → usually I21.9"
- "Female patients with fever → often J06.9"
- "Accidents (T14.1) more common in certain demographics"

**Step 5.3: Evaluate Models**
```python
For each model:
  - Predict on test set
  - Calculate accuracy (% correct)
  - Calculate F1 scores (balanced performance)
  - Compare results
```

**Example Results:**
```
Random Forest:     85% accuracy
Gradient Boosting: 82% accuracy
Linear SVM:        78% accuracy

→ Random Forest selected as best model
```

---

### **PHASE 6: 2025 Prediction** 🔮

**Step 6.1: Simulate 2025 Data**
```python
For each month (Jan-Dec):
  Generate 100 synthetic patients:
    - Random age (1-90)
    - Random sex (Male/Female)
    - Random complaint (from historical data)
    - Random diagnosis (from historical data)
```

**Why Simulate?**
- We don't have real 2025 data yet
- Creates realistic scenarios based on historical patterns
- Provides diverse data for prediction

**Example Simulation:**
```
January: 100 simulated patients
  Patient 1: Age 45, Male, "Chest pain", "Cardiac"
  Patient 2: Age 30, Female, "Fever", "Respiratory"
  ...
```

**Step 6.2: Encode Simulated Data**
```python
Use same encoders from training
Convert simulated text → numbers
Handle new values gracefully
```

**Step 6.3: Make Predictions**
```python
For each simulated patient:
  best_model.predict([age, sex, complaints, diagnosis])
  → Returns predicted ICD10 code (encoded)
```

**Example:**
```
Simulated Patient:
  AGE: 45 (encoded: 12)
  SEX: Male (encoded: 0)
  COMPLAINTS: "Chest pain" (encoded: 5)
  DIAGNOSIS: "Cardiac" (encoded: 3)

Model Prediction: I21.9 (encoded as 2)
```

**Step 6.4: Decode Predictions**
```python
Convert encoded predictions back to ICD10 codes
Map numbers → disease labels
```

---

### **PHASE 7: Identify Peaks** 📅

**Step 7.1: Count Predictions Per Month**
```python
Group by Month and Predicted Disease
Count how many times each disease appears
Sort by count (highest first)
```

**Example:**
```
January Predictions:
  J06.9: 42 cases
  T14.1: 28 cases
  I10.1: 20 cases
  Z00: 10 cases

→ Peak: J06.9 (42 cases)
```

**Step 7.2: Extract Top Disease Per Month**
```python
For each month:
  Get the disease with highest count
  This is the predicted peak
```

**Final Output:**
```
Month      | Predicted Disease | Count
-----------|-------------------|-------
January    | J06.9             | 42
February   | T14.1             | 38
March      | I10.1             | 35
April      | J06.9             | 40
...
```

---

## 🎯 **Real-World Example**

### **Input: Your Database**
```
2023-2024 Referrals:
  - 1,000 total referrals
  - Top 5 diseases: T14.1, W54.99, J06.9, Z00, I10.1
  - Patients: Ages 1-90, Male/Female
  - Complaints: Various
```

### **Process:**
1. Load 1,000 referrals → Convert to DataFrame
2. Filter to top 5 diseases → 800 records remain
3. Encode data → Text becomes numbers
4. Train models → Random Forest wins (85% accuracy)
5. Simulate 1,200 patients for 2025 (100/month × 12)
6. Predict diseases → Model predicts for each simulated patient
7. Count peaks → Find most common disease per month

### **Output:**
```
Predicted Disease Peaks for 2025:
  January:   J06.9 (Respiratory) - 42 cases
  February:  T14.1 (Injuries) - 38 cases
  March:     I10.1 (Hypertension) - 35 cases
  April:     J06.9 (Respiratory) - 40 cases
  ...
```

**Actionable Insight:**
- "Prepare for respiratory cases (J06.9) in January"
- "Stock up on injury treatment supplies for February"
- "Focus hypertension screening in March"

---

## 🔑 **Key Components**

### **1. Data Source: Django Models**
- `Referral` model with `ICD_code` field
- `Patient` model with `age` property and `sex` field
- Relationship: `Referral.patient` → `Patient`

### **2. Data Processing: Pandas DataFrame**
- Converts Django QuerySet to DataFrame
- Enables machine learning operations
- Handles missing data gracefully

### **3. Machine Learning: Scikit-learn**
- **LabelEncoder**: Converts text to numbers
- **RandomForestClassifier**: Ensemble learning
- **GradientBoostingClassifier**: Sequential improvement
- **LinearSVC**: Support vector machine

### **4. Prediction Logic**
- Trains on historical patterns
- Applies patterns to simulated future data
- Identifies monthly trends

---

## 📊 **Data Flow Diagram**

```
┌─────────────────────────────────────┐
│   Django Database                   │
│   - Referral (with ICD_code)       │
│   - Patient (with age, sex)         │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Query 2023-2024 Referrals         │
│   Filter & Select Related Patients   │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Convert to DataFrame               │
│   - Extract ICD10 codes              │
│   - Map model fields to columns     │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Find Top 5 Diseases                │
│   Filter to these diseases only      │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Encode Data                        │
│   Text → Numbers                     │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Train 3 ML Models               │
│   Select Best Model                 │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Simulate 2025 Data                 │
│   100 patients × 12 months           │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Predict Diseases                   │
│   Using Best Model                   │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Count Peaks Per Month              │
│   Identify Top Disease Each Month    │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Final Output                       │
│   Monthly Disease Peaks              │
└─────────────────────────────────────┘
```

---

## 🚀 **How to Use**

### **Run the Command:**
```bash
python manage.py predict_disease_peaks_2025
```

### **Customize Options:**
```bash
# Analyze top 10 diseases instead of 5
python manage.py predict_disease_peaks_2025 --top-n 10

# Generate 200 samples per month instead of 100
python manage.py predict_disease_peaks_2025 --samples-per-month 200

# Both options together
python manage.py predict_disease_peaks_2025 --top-n 10 --samples-per-month 200
```

---

## ✅ **What Makes This Work**

1. **Your ICD_code Field**: The script now checks for `ICD_code` field first
2. **Patient Relationship**: Uses `select_related('patient')` for efficient queries
3. **Flexible ICD10 Handling**: Works with direct field, extracted codes, or diagnosis text
4. **Robust Encoding**: Handles missing values and new categories gracefully
5. **Model Selection**: Automatically picks the best performing model
6. **Realistic Simulation**: Uses actual complaint/diagnosis patterns from your data

---

## 🎓 **Understanding the Output**

The final table shows:
- **Month**: Which month in 2025
- **Predicted Disease**: ICD10 code that will peak
- **Count**: How many cases predicted (out of 100 simulated patients)

**Use this for:**
- Resource planning (medications, supplies)
- Staff allocation (specialists needed)
- Public health campaigns (focus areas)
- Budget planning (expected case volumes)

---

## 🔧 **Technical Details**

### **ICD10 Code Extraction Regex:**
```python
pattern = r'\b([A-Z]\d{2}(?:\.\d{1,2})?)\b'
```
Matches: `T14.1`, `W54.99`, `J06.9`, `Z00`, `I10.1`

### **Model Hyperparameters:**
- **Random Forest**: 200 trees, parallel processing
- **Gradient Boosting**: 150 estimators, 0.1 learning rate
- **Linear SVM**: C=1.0, 5000 max iterations

### **Train/Test Split:**
- 80% training, 20% testing
- Random seed: 42 (for reproducibility)

---

## 📝 **Summary**

**In Simple Terms:**
1. The system looks at your past referrals (2023-2024)
2. Learns patterns: "What diseases do patients with certain characteristics get?"
3. Creates fake 2025 patients based on your historical patterns
4. Predicts what diseases those fake patients would have
5. Counts which disease appears most each month
6. Tells you: "Prepare for Disease X in Month Y"

**The Magic:**
- Machine learning finds patterns humans might miss
- Simulation creates realistic future scenarios
- Monthly peaks help with proactive planning

---

This system transforms your historical data into actionable predictions for better healthcare resource management! 🎯

