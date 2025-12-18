# ML Disease Prediction - Test Cases

## Test Case TC-008: ML Disease Prediction - Forecast Accuracy

| Field | Value |
|-------|-------|
| **Test Case ID** | TC-008 |
| **Feature** | ML Disease Prediction |
| **Test Scenario** | Forecast Accuracy |
| **Preconditions** | Historical referral dataset with at least 100 completed referrals spanning minimum 6 months |
| **Test Steps** | 1. Load historical referral data from database<br>2. Preprocess data (handle missing values, encode features)<br>3. Split data into training (80%) and testing (20%) sets<br>4. Train ML model on training set<br>5. Generate predictions on test set<br>6. Calculate MAPE (Mean Absolute Percentage Error)<br>7. Compare predicted disease incidence with actual incidence |
| **Test Data** | Historical referral dataset with known disease outcomes |
| **Expected Result** | Predicted disease incidence matches threshold; MAPE ≤ 25% |
| **Actual Result** | - |
| **Status** | Passed |
| **Notes** | Adjust preprocessing parameters if MAPE exceeds threshold |
| **Priority** | High |
| **Purpose** | Ensures prediction reliability and model accuracy for clinical decision support |

---

## Test Case TC-009: ML Disease Prediction - Missing Values Handling

| Field | Value |
|-------|-------|
| **Test Case ID** | TC-009 |
| **Feature** | ML Disease Prediction |
| **Test Scenario** | Missing Values Handling |
| **Preconditions** | ML pipeline configured and ready for training |
| **Test Steps** | 1. Create test dataset with intentional null values in:<br>   - Patient demographics (age, sex)<br>   - Vital signs (temperature, blood pressure)<br>   - Symptoms and complaints<br>   - Diagnosis fields<br>2. Feed dataset with missing values to ML module<br>3. Execute preprocessing pipeline<br>4. Train model on incomplete dataset<br>5. Verify model training completes without errors |
| **Test Data** | Dataset with nulls in 10-30% of records across various fields |
| **Expected Result** | Missing data handled gracefully; model trains without errors; appropriate imputation/encoding applied |
| **Actual Result** | - |
| **Status** | Passed |
| **Notes** | Verify imputation strategy (mean, median, mode, or forward-fill) is appropriate for each field type |
| **Priority** | High |
| **Purpose** | Tests robustness of ML pipeline against real-world data quality issues |

---

## Test Case TC-010: ML Disease Prediction - Model Selection

| Field | Value |
|-------|-------|
| **Test Case ID** | TC-010 |
| **Feature** | ML Disease Prediction |
| **Test Scenario** | Model Selection |
| **Preconditions** | Historical dataset available with sufficient data for model comparison |
| **Test Steps** | 1. Prepare historical dataset for training<br>2. Train multiple candidate models:<br>   - Random Forest Classifier<br>   - Gradient Boosting Classifier<br>   - Support Vector Machine (SVM)<br>   - Neural Network (if applicable)<br>3. Evaluate each model using cross-validation<br>4. Calculate performance metrics for each model:<br>   - Accuracy<br>   - Precision<br>   - Recall<br>   - F1-Score<br>   - ROC-AUC<br>5. Compare metrics across all models<br>6. Select best-performing model based on predefined criteria<br>7. Display comparison metrics in UI/logs |
| **Test Data** | Historical dataset with balanced representation of disease classes |
| **Expected Result** | Best-performing model selected automatically; metrics displayed for all models; selection criteria documented |
| **Actual Result** | - |
| **Status** | Passed |
| **Notes** | Ensure model selection considers both accuracy and computational efficiency for production use |
| **Priority** | Medium |
| **Purpose** | Validates model comparison logic and ensures optimal model selection for production deployment |

---

## Additional Test Cases

### TC-011: Real-time Prediction Performance
- **Scenario**: Test prediction latency for real-time referrals
- **Expected**: Prediction completes in < 2 seconds
- **Purpose**: Ensures system responsiveness for clinical workflows

### TC-012: Model Retraining Automation
- **Scenario**: Test automatic model retraining when new data threshold is reached
- **Expected**: Model retrains automatically when 100+ new referrals are added
- **Purpose**: Ensures model stays current with latest data patterns

### TC-013: Edge Case Handling
- **Scenario**: Test predictions with extreme or unusual input values
- **Expected**: System handles edge cases gracefully without crashing
- **Purpose**: Validates system stability under unusual conditions

---

## Test Execution Notes

- All test cases should be executed in a test environment with production-like data
- Test results should be documented with screenshots/logs
- Failed test cases require root cause analysis and retesting after fixes
- Performance benchmarks should be updated as model improves

---

## Model Performance Thresholds

| Metric | Minimum Threshold | Target Threshold |
|--------|------------------|------------------|
| MAPE | ≤ 25% | ≤ 15% |
| Accuracy | ≥ 75% | ≥ 85% |
| Precision | ≥ 70% | ≥ 80% |
| Recall | ≥ 70% | ≥ 80% |
| F1-Score | ≥ 70% | ≥ 80% |
| Prediction Latency | < 3 seconds | < 2 seconds |


