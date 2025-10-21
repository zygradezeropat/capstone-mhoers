from django.db import models
from django.contrib.auth.models import User  
from facilities.models import Facility
from datetime import date

class Patient(models.Model):
    patients_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    p_address = models.TextField()
    p_number = models.CharField(max_length=15)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField(default=date.today)
    sex = models.CharField(max_length=15)
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True)
    
    @property
    def age(self): 
        today = date.today()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Medical_History(models.Model):
    history_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    patient_id = models.ForeignKey(Patient, on_delete=models.CASCADE)
    illness_name = models.CharField(max_length=255)
    diagnosed_date = models.DateField()
    notes = models.TextField()
    advice = models.TextField()
    followup_date = models.DateField(null=True, blank=True)
    referral = models.ForeignKey('referrals.Referral', on_delete=models.CASCADE, null=True, blank=True, related_name='medical_history')
    
    def __str__(self):
        return f"{self.illness_name} - {self.patient.first_name} {self.patient.last_name}"

