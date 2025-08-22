from django.db import models
from django.contrib.auth.models import User
from patients.models import Patient

# this model is for referral table  

class Referral(models.Model):
    referral_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    height = models.DecimalField(max_digits=5, decimal_places=2)
    bp_systolic = models.IntegerField()
    bp_diastolic = models.IntegerField()
    pulse_rate = models.IntegerField()
    respiratory_rate = models.IntegerField()
    temperature = models.DecimalField(max_digits=4, decimal_places=1)
    oxygen_saturation = models.IntegerField()
    chief_complaint = models.TextField()
    symptoms = models.TextField()
    work_up_details = models.TextField()
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    followup_date = models.DateField(null=True, blank=True)
    initial_diagnosis = models.TextField()
    final_diagnosis = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"Referral #{self.referral_id} - {self.patient}"
    
    
class ReferralLog(models.Model):
    # Foreign key to Referral
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name='logs')

    # Foreign key to User (who made the update)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # Note about the update
    note = models.TextField()

    # Timestamp when the log is created
    created_at = models.DateTimeField(auto_now_add=True)

    # Status before the update
    status_before = models.CharField(max_length=50)

    # Status after the update
    status_after = models.CharField(max_length=50)

    def __str__(self):
        return f"Referral Log {self.id} - {self.referral.referral_id} by {self.user.username if self.user else 'Unknown'}"