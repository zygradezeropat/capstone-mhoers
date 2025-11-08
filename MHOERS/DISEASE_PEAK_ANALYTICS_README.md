# Disease Peak Analytics - Django Integration Guide

## Overview
This document explains how the Disease Peak Analytics script has been adapted to work with your Django models instead of CSV files.

## Key Differences: CSV vs Django Models

### Field Mapping

| CSV Column | Django Model Field | Notes |
|------------|-------------------|-------|
| `AGE` | `patient.age` | Property calculated from `date_of_birth` |
| `SEX` | `patient.sex` | Direct field access |
| `COMPLAINTS` | `referral.chief_complaint` or `referral.symptoms` | Uses chief_complaint, falls back to symptoms |
| `DIAGNOSIS` | `referral.final_diagnosis` or `referral.initial_diagnosis` | Prefers final_diagnosis, falls back to initial_diagnosis |
| `ICD10 CODE` | **Extracted from diagnosis text** | Uses regex to find ICD10 codes in diagnosis text, or uses diagnosis as proxy |

### Important Note: ICD10 Code Handling

Your Django models **don't have a dedicated ICD10 code field**. The script handles this by:

1. **Extracting ICD10 codes from diagnosis text** using regex pattern matching
   - Pattern: `[A-Z]\d{2}(\.\d{1,2})?` (e.g., T14.1, W54.99, J06.9)
   - If found, uses the extracted code
   
2. **Using diagnosis text as proxy** if no ICD10 code is found
   - Takes first 50 characters of diagnosis text
   - Groups similar diagnoses together

3. **Recommendation**: Consider adding an `icd10_code` field to your `Referral` model:
   ```python
   icd10_code = models.CharField(max_length=20, blank=True, null=True)
   ```

## Usage

### Running the Command

```bash
# Basic usage (uses defaults: top 5 diseases, 100 samples per month)
python manage.py predict_disease_peaks_2025

# Customize number of top diseases
python manage.py predict_disease_peaks_2025 --top-n 10

# Customize simulation samples per month
python manage.py predict_disease_peaks_2025 --samples-per-month 200
```

### What the Command Does

1. **Loads Data**: Queries `Referral` objects from 2023-2024 with related `Patient` data
2. **Identifies Top Diseases**: Finds the most common diseases (by ICD10 code or diagnosis category)
3. **Trains Models**: Trains Random Forest, Gradient Boosting, and Linear SVM models
4. **Selects Best Model**: Chooses the model with highest accuracy
5. **Simulates 2025 Data**: Generates synthetic patient data for each month in 2025
6. **Predicts Peaks**: Predicts which disease will peak each month

### Output

The command outputs:
- Number of records loaded
- Top diseases identified
- Model evaluation results (accuracy, F1 scores)
- Best model selected
- **Predicted disease peaks for each month in 2025**

## Data Requirements

For the script to work effectively, ensure you have:

1. **Referral records** from 2023-2024 with:
   - Related `Patient` objects
   - `initial_diagnosis` or `final_diagnosis` populated
   - `chief_complaint` or `symptoms` populated

2. **Patient records** with:
   - `date_of_birth` (for age calculation)
   - `sex` field populated

## Improving Accuracy

### Option 1: Add ICD10 Code Field

Add to `referrals/models.py`:
```python
class Referral(models.Model):
    # ... existing fields ...
    icd10_code = models.CharField(max_length=20, blank=True, null=True, help_text="ICD10 diagnosis code")
```

Then run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Option 2: Extract ICD10 Codes from Existing Data

You can create a migration or management command to extract ICD10 codes from existing diagnosis text and populate the new field.

### Option 3: Use Medical History

Consider using `Medical_History.illness_name` as an additional data source for disease classification.

## Troubleshooting

### "No referral data found for 2023-2024"
- Check that referrals exist with `created_at` in 2023 or 2024
- Verify referrals have related patients and diagnoses

### "No data remaining after filtering"
- Ensure diagnoses contain ICD10 codes or meaningful text
- Check that top diseases match your actual data

### Low Model Accuracy
- Increase training data (more referrals)
- Ensure consistent diagnosis formatting
- Consider adding ICD10 code field for better classification

## Integration with Views

You can integrate this into your Django views:

```python
from analytics.management.commands.predict_disease_peaks_2025 import Command

# In a view
command = Command()
command.handle(top_n=5, samples_per_month=100)
# Access results from command output
```

Or create an API endpoint that runs the prediction and returns JSON results.

