from django.db import models
from django.contrib.auth.models import User
from patients.models import Patient
from facilities.models import Facility

# this model is for referral table  

class Referral(models.Model):
    REFERRAL_TYPE_CHOICES = [
        ('Emergency', 'Emergency'),
        ('Urgent', 'Urgent'),
        ('Routine', 'Routine'),
        ('Follow-up', 'Follow-up'),
        ('Preventive', 'Preventive'),
    ]

    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='referrals')
    referral_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Who created/referred
    examined_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='examinations_performed',
        verbose_name='Examined By'
    )  # Doctor/staff who performed the check-up
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
    ICD_code = models.CharField(max_length=10, null=True, blank=True)
    
    # NEW FIELD: Link to Disease database
    disease = models.ForeignKey(
        'analytics.Disease',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals',
        help_text="Verified disease from database"
    )
    disease_verified = models.BooleanField(
        default=False,
        help_text="Whether doctor verified disease information from database"
    )
    
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    followup_date = models.DateField(null=True, blank=True)
    initial_diagnosis = models.TextField()
    final_diagnosis = models.TextField(null=True, blank=True)
    
    # Additional fields from CSV
    referral_type = models.CharField(max_length=20, choices=REFERRAL_TYPE_CHOICES, blank=True, null=True, verbose_name='Referral Type')
    cause = models.TextField(blank=True, null=True, verbose_name='Cause')
    treatments = models.TextField(blank=True, null=True, verbose_name='Treatments')
    remarks = models.TextField(blank=True, null=True, verbose_name='Remarks')
    
    # Lifestyle/Social History
    is_smoker = models.BooleanField(default=False, verbose_name='Is Smoker')
    smoking_sticks_per_day = models.IntegerField(blank=True, null=True, verbose_name='Smoking: Sticks/Packs per Day')
    is_alcoholic = models.BooleanField(default=False, verbose_name='Is Alcoholic')
    alcohol_bottles_per_year = models.IntegerField(blank=True, null=True, verbose_name='Alcohol: Bottles per Year')
    family_planning = models.BooleanField(default=False, verbose_name='Family Planning')
    family_planning_type = models.CharField(
        max_length=20,
        choices=[
            # Female options
            ('DMPA', 'DMPA'),
            ('IMPLANT', 'IMPLANT'),
            ('IUD', 'IUD'),
            ('PILLS', 'PILLS'),
            # Male options
            ('CONDOM', 'CONDOM'),
            ('VASECTOMY', 'VASECTOMY'),
            ('WITHDRAWAL', 'WITHDRAWAL'),
            ('NONE', 'NONE'),
        ],
        blank=True, null=True,
        verbose_name='Family Planning Type'
    )
    
    # Menstrual History (for female patients)
    menarche = models.IntegerField(blank=True, null=True, verbose_name='Menarche (Age)')
    sexually_active = models.BooleanField(blank=True, null=True, verbose_name='Sexually Active')
    number_of_partners = models.IntegerField(blank=True, null=True, verbose_name='Number of Partners')
    is_menopause = models.BooleanField(blank=True, null=True, verbose_name='Menopause')
    menopause_age = models.IntegerField(blank=True, null=True, verbose_name='Menopause Age')
    last_menstrual_period = models.DateField(blank=True, null=True, verbose_name='Last Menstrual Period (LMP)')
    period_duration = models.IntegerField(blank=True, null=True, verbose_name='Period Duration (Days)')
    period_interval = models.IntegerField(blank=True, null=True, verbose_name='Period Interval (Days)')
    pads_per_day = models.IntegerField(blank=True, null=True, verbose_name='Pads per Day')
    
    # Pregnancy History (for female patients)
    is_pregnant = models.BooleanField(blank=True, null=True, verbose_name='Is Pregnant')
    gravidity = models.IntegerField(blank=True, null=True, verbose_name='Gravidity')
    parity = models.IntegerField(blank=True, null=True, verbose_name='Parity')
    delivery_type = models.CharField(max_length=50, blank=True, null=True, verbose_name='Type of Delivery')
    full_term_births = models.IntegerField(blank=True, null=True, verbose_name='Number of Full Term Births')
    premature_births = models.IntegerField(blank=True, null=True, verbose_name='Number of Premature Births')
    abortions = models.IntegerField(blank=True, null=True, verbose_name='Number of Abortions')
    living_children = models.IntegerField(blank=True, null=True, verbose_name='Number of Living Children')
     
    def __str__(self):
        return f"Referral #{self.referral_id} - {self.patient}"

    @property
    def completion_duration_minutes(self):
        """
        Returns the rounded number of minutes between referral creation and completion.
        """
        if not self.created_at or not self.completed_at:
            return None

        delta = self.completed_at - self.created_at
        minutes = max(round(delta.total_seconds() / 60), 0)
        return minutes


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

