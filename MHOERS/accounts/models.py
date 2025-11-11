
from django.db import models
from django.contrib.auth.models import User
from facilities.models import Facility
from datetime import datetime
from django.utils import timezone

# This extends the User model to associate a user with a specific facility
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.user.username

class BHWRegistration(models.Model):
    STATUS_CHOICES = [
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    bhw_id = models.AutoField(primary_key=True)
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    accreditationNumber = models.CharField(max_length=100)
    registrationNumber = models.CharField(max_length=100)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    
    # Registration status fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_APPROVAL')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_bhw_registration')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Additional fields from registration form
    phone = models.CharField(max_length=15, blank=True)
    street_address = models.CharField(max_length=200, blank=True)
    barangay = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    
    # Professional fields
    bhw_sub_role = models.CharField(max_length=20, blank=True)  # BHW_COMMUNITY, BHW_NURSE
    assigned_barangay = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self): 
        return f"{self.first_name} {self.last_name}"

class Doctors(models.Model):
    STATUS_CHOICES = [
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    doctor_id = models.AutoField(primary_key=True)
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    specialization = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    phone = models.CharField(max_length=15)
    license_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Registration status fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_APPROVAL')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_doctors')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Additional fields from registration form
    street_address = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    barangay = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    
    # Professional fields
    mho_sub_role = models.CharField(max_length=20, blank=True)  # MHO_DOCTOR, MHO_NURSE
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self): 
        return f"Dr. {self.first_name} {self.last_name}"
   
 
class Nurses(models.Model):
    STATUS_CHOICES = [
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    nurse_id = models.AutoField(primary_key=True)
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    
    # Registration status fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_APPROVAL')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_nurses')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Additional fields from registration form
    email = models.EmailField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    street_address = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    barangay = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    
    # Professional fields
    nurse_license_number = models.CharField(max_length=100, blank=True)
    prc_license_number = models.CharField(max_length=100, blank=True)
    nursing_school = models.CharField(max_length=200, blank=True)
    nursing_graduation_year = models.DateField(null=True, blank=True)
    nursing_specialization = models.CharField(max_length=200, blank=True)
    nursing_affiliation = models.CharField(max_length=200, blank=True)
    nursing_experience_years = models.IntegerField(null=True, blank=True)
    nursing_certification = models.CharField(max_length=200, blank=True)
    nursing_assigned_area = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self): 
        return f"Nurse {self.first_name} {self.last_name}"


class UserConsent(models.Model):
    """Model to track user privacy and data processing consent"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='consent')
    privacy_policy_accepted = models.BooleanField(default=False)
    privacy_policy_accepted_at = models.DateTimeField(null=True, blank=True)
    data_processing_consent = models.BooleanField(default=False)
    data_processing_consent_at = models.DateTimeField(null=True, blank=True)
    marketing_consent = models.BooleanField(default=False, help_text="Consent for marketing communications")
    consent_version = models.CharField(max_length=20, default='1.0', help_text="Version of privacy policy accepted")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Consent"
        verbose_name_plural = "User Consents"
    
    def __str__(self):
        return f"Consent for {self.user.username}"


class AccountDeletionRequest(models.Model):
    """Model to track user requests for account deletion (GDPR Right to be Forgotten)"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='deletion_request')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    requested_at = models.DateTimeField(auto_now_add=True)
    scheduled_deletion_date = models.DateTimeField(null=True, blank=True, help_text="Date when account will be deleted (typically 30 days after request)")
    completed_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True, help_text="Reason if deletion was cancelled")
    notes = models.TextField(blank=True, help_text="Administrative notes")
    
    class Meta:
        verbose_name = "Account Deletion Request"
        verbose_name_plural = "Account Deletion Requests"
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Deletion request for {self.user.username} - {self.status}"


class LoginLog(models.Model):
    """Model to track user login events"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_logs')
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    
    class Meta:
        verbose_name = "Login Log"
        verbose_name_plural = "Login Logs"
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['-login_time']),
            models.Index(fields=['user', '-login_time']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.login_time}"