from django.db import models
from django.contrib.auth.models import User  
from facilities.models import Facility
from datetime import date

class Patient(models.Model):
    CIVIL_STATUS_CHOICES = [
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Widowed', 'Widowed'),
        ('Divorced', 'Divorced'),
        ('Separated', 'Separated'),
    ]
    
    PHIC_STATUS_CHOICES = [
        ('M', 'Member'),
        ('D', 'Dependent'),
        ('N', 'N/A'),
    ]
    
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
    
    # Additional fields from CSV
    cct_beneficiary = models.BooleanField(default=False, verbose_name='CCT Beneficiary')
    phic_status = models.CharField(max_length=1, choices=PHIC_STATUS_CHOICES, blank=True, null=True, verbose_name='PHIC Status')
    civil_status = models.CharField(max_length=20, choices=CIVIL_STATUS_CHOICES, blank=True, null=True, verbose_name='Civil Status')
    is_pwd = models.BooleanField(default=False, verbose_name='Person With Disability')
    sitio = models.CharField(max_length=100, blank=True, null=True, verbose_name='Sitio')
    barangay = models.CharField(max_length=100, blank=True, null=True, verbose_name='Barangay')
    
    # PhilHealth Information
    philhealth_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='PhilHealth Number')
    philhealth_category = models.CharField(
        max_length=20,
        choices=[('Sponsored', 'Sponsored'), ('Self Paying', 'Self Paying')],
        blank=True, null=True,
        verbose_name='PhilHealth Category'
    )
    private_company_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Private Company Name')
    is_dependent = models.BooleanField(default=False, verbose_name='Is Dependent')
    dependent_member_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='Dependent Member Name')
    dependent_member_birthday = models.DateField(blank=True, null=True, verbose_name='Dependent Member Birthday')
    dependent_philhealth_no = models.CharField(max_length=50, blank=True, null=True, verbose_name='Dependent PhilHealth Number')
    
    # Family History
    family_history_hypertension = models.BooleanField(default=False, verbose_name='Family History: Hypertension')
    family_history_diabetes = models.BooleanField(default=False, verbose_name='Family History: Diabetes')
    family_history_cancer = models.BooleanField(default=False, verbose_name='Family History: Cancer')
    family_history_asthma = models.BooleanField(default=False, verbose_name='Family History: Asthma')
    family_history_epilepsy = models.BooleanField(default=False, verbose_name='Family History: Epilepsy')
    family_history_tuberculosis = models.BooleanField(default=False, verbose_name='Family History: Tuberculosis')
    family_history_others = models.TextField(blank=True, null=True, verbose_name='Family History: Others')
    
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


class SMSReminderLog(models.Model):
    """Track SMS reminders sent to prevent duplicates"""
    reminder_id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='sms_reminders')
    medical_history = models.ForeignKey(Medical_History, on_delete=models.CASCADE, related_name='sms_reminders', null=True, blank=True)
    followup_date = models.DateField()
    reminder_type = models.CharField(max_length=20, choices=[
        ('today', 'Today'),
        ('tomorrow', 'Tomorrow'),
    ])
    sent_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='sent', choices=[
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ])
    
    class Meta:
        unique_together = [['patient', 'followup_date', 'reminder_type']]
        indexes = [
            models.Index(fields=['patient', 'followup_date', 'reminder_type']),
        ]
    
    def __str__(self):
        return f"SMS Reminder for {self.patient} on {self.followup_date}"
