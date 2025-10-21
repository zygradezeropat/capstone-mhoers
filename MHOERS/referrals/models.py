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


class FollowUpVisit(models.Model):
    """
    Model to store follow-up visit data including new vital signs
    """
    followup_id = models.AutoField(primary_key=True)
    medical_history = models.ForeignKey('patients.Medical_History', on_delete=models.CASCADE, related_name='followup_visits')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Healthcare worker who conducted the follow-up
    
    # New vital signs for this follow-up visit
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bp_systolic = models.IntegerField(null=True, blank=True)
    bp_diastolic = models.IntegerField(null=True, blank=True)
    pulse_rate = models.IntegerField(null=True, blank=True)
    respiratory_rate = models.IntegerField(null=True, blank=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    oxygen_saturation = models.IntegerField(null=True, blank=True)
    
    # Follow-up specific data
    visit_date = models.DateField()
    visit_notes = models.TextField(blank=True, null=True)
    current_symptoms = models.TextField(blank=True, null=True)
    treatment_response = models.TextField(blank=True, null=True)
    new_medications = models.TextField(blank=True, null=True)
    next_followup_date = models.DateField(null=True, blank=True)
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('scheduled', 'Scheduled'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
            ('no_show', 'No Show'),
        ],
        default='scheduled'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Follow-up Visit - {self.patient} on {self.visit_date}"
    
    class Meta:
        ordering = ['-visit_date']
        verbose_name = "Follow-up Visit"
        verbose_name_plural = "Follow-up Visits"


class ReferralLog(models.Model):
    # Foreign key to Referral
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE)
    # Add other fields as needed
    pass

