from django.test import TestCase
from django.contrib.auth.models import User
from referrals.models import Referral, Facility
from patients.models import Patient
from analytics.models import Disease
from analytics.ml_utils import (
    get_ml_models_path,
    train_random_forest_model_classification,
    predict_disease_for_referral,
    time_completed,
    random_forest_regression_train_model,
    random_forest_regression_prediction_time,
    train_model_disease_spike,
    disease_forecast
)
from datetime import datetime, timedelta, date
from decimal import Decimal
import os
import shutil


class MLUtilsTestCase(TestCase):
    """Comprehensive tests for ml_utils functions"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test facility
        self.facility = Facility.objects.create(
            name='Test Facility',
            assigned_bhw='Test BHW',
            latitude=14.5995,
            longitude=120.9842
        )
        
        # Create test patient
        self.patient = Patient.objects.create(
            first_name='John',
            last_name='Doe',
            p_address='123 Test Street',
            p_number='09123456789',
            user=self.user,
            date_of_birth=date(1990, 1, 1),
            sex='Male',
            facility=self.facility
        )
        
        # Create test diseases
        self.disease1 = Disease.objects.create(
            name='Flu',
            description='Influenza is a viral infection',
            symptoms='fever, cough, fatigue, body aches',
            time_caters=24.0
        )
        self.disease2 = Disease.objects.create(
            name='Common Cold',
            description='Common viral infection of the nose and throat',
            symptoms='runny nose, sneezing, mild cough',
            time_caters=48.0
        )
        
        # Create completed referral (for time testing)
        self.completed_referral = Referral.objects.create(
            facility=self.facility,
            user=self.user,
            patient=self.patient,
            weight=Decimal('70.5'),
            height=Decimal('175.0'),
            bp_systolic=120,
            bp_diastolic=80,
            pulse_rate=72,
            respiratory_rate=16,
            temperature=Decimal('36.5'),
            oxygen_saturation=98,
            chief_complaint='Test complaint',
            symptoms='fever and cough',
            work_up_details='Test details',
            status='completed',
            created_at=datetime.now() - timedelta(hours=2),
            completed_at=datetime.now()
        )
        
        # Create pending referral (for prediction testing)
        self.pending_referral = Referral.objects.create(
            facility=self.facility,
            user=self.user,
            patient=self.patient,
            weight=Decimal('65.0'),
            height=Decimal('170.0'),
            bp_systolic=115,
            bp_diastolic=75,
            pulse_rate=68,
            respiratory_rate=14,
            temperature=Decimal('37.0'),
            oxygen_saturation=97,
            chief_complaint='Another complaint',
            symptoms='runny nose and sneezing',
            work_up_details='More details',
            status='pending'
        )
        
        # Get models directory and clean it before tests
        self.models_dir = get_ml_models_path()
        # Backup existing models if they exist
        self.backup_dir = self.models_dir + '_backup'
        if os.path.exists(self.models_dir):
            if os.path.exists(self.backup_dir):
                shutil.rmtree(self.backup_dir)
            shutil.move(self.models_dir, self.backup_dir)
    
    def tearDown(self):
        """Clean up after tests"""
        # Restore backup if it existed
        if os.path.exists(self.backup_dir):
            if os.path.exists(self.models_dir):
                shutil.rmtree(self.models_dir)
            shutil.move(self.backup_dir, self.models_dir)
    
    def test_get_ml_models_path(self):
        """Test that get_ml_models_path returns absolute path"""
        path = get_ml_models_path()
        self.assertTrue(os.path.isabs(path), "Path should be absolute")
        self.assertIn('ml_models', path)
    
    def test_train_disease_classification_model(self):
        """Test disease classification model training"""
        result = train_random_forest_model_classification()
        
        # Check result
        self.assertNotIn('error', result, f"Training failed: {result}")
        self.assertEqual(result['status'], 'Training completed')
        self.assertGreater(result['num_diseases'], 0)
        
        # Check files were created
        model_path = os.path.join(self.models_dir, 'disease_rf_model.pkl')
        vectorizer_path = os.path.join(self.models_dir, 'disease_vectorizer.pkl')
        
        self.assertTrue(os.path.exists(model_path), "Model file should exist")
        self.assertTrue(os.path.exists(vectorizer_path), "Vectorizer file should exist")
    
    def test_predict_disease_for_referral_success(self):
        """Test disease prediction with trained model"""
        # First train the model
        train_random_forest_model_classification()
        
        # Now test prediction
        prediction = predict_disease_for_referral(self.pending_referral.referral_id)
        
        # Should return a disease name (not an error)
        self.assertIsInstance(prediction, str)
        self.assertNotIn('Error', prediction)
        self.assertNotIn('not found', prediction.lower())
    
    def test_predict_disease_for_referral_no_model(self):
        """Test disease prediction when model doesn't exist"""
        # Delete model files if they exist
        model_path = os.path.join(self.models_dir, 'disease_rf_model.pkl')
        if os.path.exists(model_path):
            os.remove(model_path)
        
        prediction = predict_disease_for_referral(self.pending_referral.referral_id)
        
        # Should return error message
        prediction_lower = prediction.lower() if isinstance(prediction, str) else str(prediction).lower()
        self.assertTrue('not found' in prediction_lower or 'error' in prediction_lower,
                       f"Expected error message, got: {prediction}")
    
    def test_predict_disease_for_referral_invalid_id(self):
        """Test disease prediction with invalid referral ID"""
        train_random_forest_model_classification()
        
        prediction = predict_disease_for_referral(99999)
        self.assertEqual(prediction, "Referral not found")
    
    def test_time_completed_calculation(self):
        """Test time_completed fixes the date subtraction bug"""
        time = time_completed(self.completed_referral.referral_id)
        
        # Should return positive number (bug fix verification)
        self.assertIsInstance(time, (int, float))
        self.assertGreaterEqual(time, 0, "Time should be positive (bug fixed!)")
        
        # Should be around 120 minutes (2 hours)
        self.assertGreater(time, 100)
        self.assertLess(time, 150)
    
    def test_time_completed_not_completed(self):
        """Test time_completed handles incomplete referrals"""
        time = time_completed(self.pending_referral.referral_id)
        self.assertEqual(time, "Referral not yet completed")
    
    def test_time_completed_not_found(self):
        """Test time_completed handles non-existent referral"""
        time = time_completed(99999)
        self.assertEqual(time, "Referral not found")
    
    def test_train_time_prediction_model(self):
        """Test time prediction model training"""
        result = random_forest_regression_train_model()
        
        # Check result
        self.assertNotIn('error', result, f"Training failed: {result}")
        self.assertEqual(result['status'], 'Training completed')
        self.assertIn('MAE', result)
        self.assertIn('R2_Score', result)
        
        # Check files were created
        model_path = os.path.join(self.models_dir, 'time_rf_model.pkl')
        vectorizer_path = os.path.join(self.models_dir, 'symptom_vectorizer.pkl')
        
        self.assertTrue(os.path.exists(model_path), "Time model file should exist")
        self.assertTrue(os.path.exists(vectorizer_path), "Symptom vectorizer file should exist")
    
    def test_predict_time_success(self):
        """Test time prediction with trained model"""
        # First train the model
        random_forest_regression_train_model()
        
        # Test prediction
        prediction = random_forest_regression_prediction_time(self.pending_referral)
        
        # Should return a number (hours)
        self.assertIsInstance(prediction, (int, float))
        self.assertGreater(prediction, 0)
    
    def test_predict_time_no_model(self):
        """Test time prediction when model doesn't exist"""
        # Ensure model doesn't exist
        model_path = os.path.join(self.models_dir, 'time_rf_model.pkl')
        if os.path.exists(model_path):
            os.remove(model_path)
        
        prediction = random_forest_regression_prediction_time(self.pending_referral)
        
        # Should return error message
        prediction_lower = prediction.lower() if isinstance(prediction, str) else str(prediction).lower()
        self.assertTrue('not found' in prediction_lower or 'error' in prediction_lower,
                       f"Expected error message, got: {prediction}")
    
    def test_train_model_disease_spike(self):
        """Test disease spike data preparation"""
        # Create referral with diagnosis
        self.completed_referral.final_diagnosis = 'Flu'
        self.completed_referral.save()
        
        df = train_model_disease_spike()
        
        # Should return DataFrame (even if empty)
        self.assertIsNotNone(df)
        # If we have data, check structure
        if not df.empty:
            self.assertIn('month', df.columns)
            self.assertIn('year', df.columns)
            self.assertIn('month_num', df.columns)
    
    def test_disease_forecast(self):
        """Test disease forecasting"""
        # Prepare data
        self.completed_referral.final_diagnosis = 'Flu'
        self.completed_referral.save()
        
        df = train_model_disease_spike()
        
        if not df.empty:
            forecast = disease_forecast(df, months_ahead=6)
            self.assertNotIn('error', forecast)
            self.assertIsInstance(forecast, dict)
        else:
            forecast = disease_forecast(df, months_ahead=6)
            self.assertIn('error', forecast)
    
    def test_exception_handling_specific(self):
        """Test that exception handling is specific, not bare except"""
        # This test verifies we're using specific exceptions
        # by checking the code doesn't use bare 'except:'
        import inspect
        from analytics import ml_utils
        
        source = inspect.getsource(ml_utils)
        # Should not have bare except (except:)
        self.assertNotIn('except:\n', source.replace(' ', ''), 
                        "Found bare except: - should use specific exceptions")