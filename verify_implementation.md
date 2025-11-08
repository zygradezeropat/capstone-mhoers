# How to Verify Advanced Time Prediction Implementation

## Method 1: Quick Code Check ✅

### Check Function Exists:
```python
# In Django shell: python manage.py shell
from analytics.ml_utils import predict_time_to_cater_advanced
print("✓ Function exists!" if callable(predict_time_to_cater_advanced) else "✗ Not found")
```

### Check URL Route:
```python
from referrals.urls import urlpatterns
url_names = [p.name for p in urlpatterns if hasattr(p, 'name')]
print("✓ URL exists!" if 'get_time_prediction_advanced' in url_names else "✗ Not found")
```

### Check View Function:
```python
from referrals.views import get_time_prediction_advanced
print("✓ View exists!" if callable(get_time_prediction_advanced) else "✗ Not found")
```

## Method 2: Test with Real Data 🔍

### Step 1: Train the Model (if not done yet)
Visit in browser (as staff user):
```
http://your-domain/referrals/train/time-model/
```

Or in Django shell:
```python
from analytics.ml_utils import train_time_prediction_model_advanced
result = train_time_prediction_model_advanced()
print(result)
```

### Step 2: Check Model Files Exist
```python
import os
from analytics.ml_utils import get_ml_models_path
models_dir = get_ml_models_path()

files = [
    'time_prediction_model_advanced.pkl',
    'time_vectorizer_advanced.pkl',
    'time_scaler_advanced.pkl',
    'diag_time_encoder_advanced.pkl'
]

for f in files:
    path = os.path.join(models_dir, f)
    print(f"{'✓' if os.path.exists(path) else '✗'} {f}")
```

### Step 3: Test Prediction
```python
from referrals.models import Referral
from analytics.ml_utils import predict_time_to_cater_advanced

# Get a referral ID from your database
referral = Referral.objects.exclude(symptoms__isnull=True).exclude(symptoms='').first()
if referral:
    result = predict_time_to_cater_advanced(referral.referral_id)
    print(f"Prediction: {result} hours")
    print(f"✓ Working!" if isinstance(result, (int, float)) and result >= 0.25 else "✗ Error or invalid")
```

## Method 3: Browser Test 🌐

1. **Train Model** (first time only):
   - Login as staff user
   - Visit: `http://your-domain/referrals/train/time-model/`
   - Should return JSON with training results

2. **Test Prediction**:
   - Create/assess a patient referral
   - Note the referral_id (e.g., 123)
   - Visit: `http://your-domain/referrals/referral/time-predict/123/`
   - Should return JSON like:
     ```json
     {
       "prediction": 1.5,
       "unit": "hours",
       "prediction_minutes": 90.0
     }
     ```

## Method 4: Check for Negative Fix ✅

Verify the clamping code exists:
```python
# In ml_utils.py, line ~608 should have:
predicted_time = max(0.25, min(predicted_time, 4.0))
```

This ensures predictions are ALWAYS between 0.25 and 4.0 hours (no negatives!).

## Expected Results:

✅ **If working correctly:**
- Function exists and is callable
- URL route is registered
- Model files exist (after training)
- Predictions return values between 0.25-4.0 hours
- No negative values ever returned

❌ **If not working:**
- Import errors = function not found
- 404 error = URL route not found
- "Model not found" = need to train first
- Negative values = clamping code missing (but we added it!)

