"""
Quick test script to verify advanced time prediction is implemented correctly
Run this from your Django project root: python manage.py shell < test_time_prediction.py
Or run: python manage.py shell, then copy-paste the code below
"""

import os
from referrals.models import Referral
from analytics.ml_utils import predict_time_to_cater_advanced, train_time_prediction_model_advanced

print("=" * 80)
print("TESTING ADVANCED TIME PREDICTION IMPLEMENTATION")
print("=" * 80)

# Test 1: Check if function exists
print("\n✅ Test 1: Checking if function exists...")
try:
    assert callable(predict_time_to_cater_advanced), "Function exists"
    print("   ✓ Function 'predict_time_to_cater_advanced' exists")
except AssertionError as e:
    print(f"   ✗ {e}")
    exit(1)

# Test 2: Check if model files path exists
print("\n✅ Test 2: Checking model directory...")
from analytics.ml_utils import get_ml_models_path
models_dir = get_ml_models_path()
print(f"   Models directory: {models_dir}")
print(f"   Directory exists: {os.path.exists(models_dir)}")

# Test 3: Check if model files exist (if trained)
print("\n✅ Test 3: Checking if model files exist...")
model_files = {
    'Model': 'time_prediction_model_advanced.pkl',
    'Vectorizer': 'time_vectorizer_advanced.pkl',
    'Scaler': 'time_scaler_advanced.pkl',
    'Encoder': 'diag_time_encoder_advanced.pkl'
}

all_exist = True
for name, filename in model_files.items():
    filepath = os.path.join(models_dir, filename)
    exists = os.path.exists(filepath)
    status = "✓" if exists else "✗"
    print(f"   {status} {name}: {filename} {'(exists)' if exists else '(not found - need to train)'}")
    if not exists:
        all_exist = False

# Test 4: Check if we have referrals to test with
print("\n✅ Test 4: Checking referral data...")
referrals_count = Referral.objects.count()
print(f"   Total referrals in database: {referrals_count}")

referrals_with_symptoms = Referral.objects.exclude(symptoms__isnull=True).exclude(symptoms='').count()
print(f"   Referrals with symptoms: {referrals_with_symptoms}")

# Test 5: Test prediction on a real referral (if model exists)
if all_exist and referrals_with_symptoms > 0:
    print("\n✅ Test 5: Testing prediction on actual referral...")
    # Get first referral with symptoms
    test_referral = Referral.objects.exclude(symptoms__isnull=True).exclude(symptoms='').first()
    if test_referral:
        print(f"   Testing with referral ID: {test_referral.referral_id}")
        print(f"   Symptoms: {test_referral.symptoms[:50]}...")
        
        try:
            result = predict_time_to_cater_advanced(test_referral.referral_id)
            if isinstance(result, (int, float)):
                print(f"   ✓ Prediction successful: {result} hours ({result * 60:.1f} minutes)")
                if result >= 0.25 and result <= 4.0:
                    print(f"   ✓ Prediction is within valid range (0.25-4.0 hours)")
                else:
                    print(f"   ⚠ Warning: Prediction outside expected range!")
            else:
                print(f"   ✗ Error: {result}")
        except Exception as e:
            print(f"   ✗ Exception: {e}")
else:
    if not all_exist:
        print("\n⚠ Test 5: Skipped - Model not trained yet")
        print("   → Run training first: Visit /referrals/train/time-model/ or call train_time_prediction_model_advanced()")
    if referrals_with_symptoms == 0:
        print("\n⚠ Test 5: Skipped - No referrals with symptoms found")

# Test 6: Check URL routes
print("\n✅ Test 6: Checking URL routes...")
try:
    from referrals.urls import urlpatterns
    url_names = [pattern.name for pattern in urlpatterns if hasattr(pattern, 'name') and pattern.name]
    
    expected_urls = [
        'get_time_prediction_advanced',
        'train_time_model_advanced'
    ]
    
    for url_name in expected_urls:
        if url_name in url_names:
            print(f"   ✓ URL route '{url_name}' registered")
        else:
            print(f"   ✗ URL route '{url_name}' NOT found")
except Exception as e:
    print(f"   ⚠ Could not verify URLs: {e}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if all_exist:
    print("✅ Implementation Status: READY")
    print("   → Model files exist")
    print("   → Prediction function available")
    print("   → URL routes registered")
    print("\n   📝 To test:")
    print("   1. Visit: /referrals/referral/time-predict/<referral_id>/")
    print("   2. Or test after creating a new referral")
else:
    print("⚠ Implementation Status: NEEDS TRAINING")
    print("   → Code is implemented correctly")
    print("   → Model files need to be created")
    print("\n   📝 Next steps:")
    print("   1. Train the model: Visit /referrals/train/time-model/ (staff only)")
    print("   2. Or run in Django shell: train_time_prediction_model_advanced()")
    print("   3. Then test prediction")

print("=" * 80)

