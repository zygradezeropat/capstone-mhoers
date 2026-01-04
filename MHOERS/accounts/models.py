
from django.db import models
from django.contrib.auth.models import User
from facilities.models import Facility
from datetime import datetime, timedelta
from django.utils import timezone
import secrets

# This extends the User model to associate a user with a specific facility
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.user.username

class BHWRegistration(models.Model):
    STATUS_CHOICES = [
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('ACTIVE', 'Active'),
        ('REJECTED', 'Rejected'),
        ('INACTIVE', 'Inactive'),
        ('RETIRED', 'Retired'),
        ('SUSPENDED', 'Suspended')
    ]
    
    bhw_id = models.AutoField(primary_key=True)
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
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
    
    # Registration and Accreditation Numbers (Format: XX-XXX)
    registration_number = models.CharField(max_length=10, blank=True, null=True, help_text="Format: XX-XXX (e.g., 32-424)")
    accreditation_number = models.CharField(max_length=10, blank=True, null=True, help_text="Format: XX-XXX (e.g., 32-424)")
    
    # Registration certificate image (uploaded during registration)
    registration_certificate = models.ImageField(upload_to='registration_certificates/%Y/%m/%d/', blank=True, null=True, help_text='Registration Certificate image')
    
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self): 
        return f"{self.first_name} {self.last_name}"

class Doctors(models.Model):
    STATUS_CHOICES = [
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('ACTIVE', 'Active'),
        ('REJECTED', 'Rejected'),
        ('INACTIVE', 'Inactive'), 
        ('RETIRED', 'Retired'),
        ('SUSPENDED', 'Suspended'),
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
        ('ACTIVE', 'Active'),
        ('REJECTED', 'Rejected'),
        ('INACTIVE', 'Inactive'),
        ('RETIRED', 'Retired'),
        ('SUSPENDED', 'Suspended')
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


class Midwives(models.Model):
    STATUS_CHOICES = [
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('ACTIVE', 'Active'),
        ('REJECTED', 'Rejected'),
        ('INACTIVE', 'Inactive'),
        ('RETIRED', 'Retired'),
        ('SUSPENDED', 'Suspended')
    ]
    
    midwife_id = models.AutoField(primary_key=True)
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    
    # Registration status fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_APPROVAL')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_midwives')
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
    midwife_license_number = models.CharField(max_length=100, blank=True)
    prc_license_number = models.CharField(max_length=100, blank=True)
    midwifery_school = models.CharField(max_length=200, blank=True)
    midwifery_graduation_year = models.DateField(null=True, blank=True)
    midwifery_specialization = models.CharField(max_length=200, blank=True)
    midwifery_affiliation = models.CharField(max_length=200, blank=True)
    midwifery_experience_years = models.IntegerField(null=True, blank=True)
    midwifery_certification = models.CharField(max_length=200, blank=True)
    midwifery_assigned_area = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self): 
        return f"Midwife {self.first_name} {self.last_name}"


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


class PasswordResetToken(models.Model):
    """Custom password reset token model for email-based password reset"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'used']),
        ]
        verbose_name = "Password Reset Token"
        verbose_name_plural = "Password Reset Tokens"
    
    def __str__(self):
        return f"Token for {self.user.username} - {'Used' if self.used else 'Active'}"
    
    @classmethod
    def generate_token(cls, user):
        """Generate a new password reset token for a user"""
        # Delete old unused tokens for this user
        cls.objects.filter(user=user, used=False).delete()
        
        # Generate a secure random token
        token = secrets.token_urlsafe(32)
        
        # Create token with 24 hour expiration
        expires_at = timezone.now() + timedelta(hours=24)
        
        reset_token = cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
        
        return reset_token
    
    def is_valid(self):
        """Check if token is valid (not used and not expired)"""
        if self.used:
            return False
        if timezone.now() > self.expires_at:
            return False
        return True
    
    def mark_as_used(self):
        """Mark token as used"""
        self.used = True
        self.save()


class ApprovedBHW(models.Model):
    """Whitelist of BHWs who are authorized to register accounts"""
    approved_bhw_id = models.AutoField(primary_key=True)
    registration_number = models.CharField(max_length=100, unique=True, help_text="Format: XX-XXX (e.g., 32-424)")
    accreditation_number = models.CharField(max_length=100, unique=True, help_text="Format: XX-XXX (e.g., 32-424)")
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(max_length=100, blank=True)
    barangay = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True, help_text="Set to False to revoke registration access")
    notes = models.TextField(blank=True, help_text="Administrative notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_approved_bhws')
    
    class Meta:
        verbose_name = "Approved BHW"
        verbose_name_plural = "Approved BHWs"
        ordering = ['last_name', 'first_name']
        unique_together = [['registration_number', 'accreditation_number']]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - RN: {self.registration_number}"


class ApprovedDoctor(models.Model):
    """Whitelist of Doctors who are authorized to register accounts"""
    approved_doctor_id = models.AutoField(primary_key=True)
    license_number = models.CharField(max_length=100, unique=True, blank=True, null=True, help_text="PRC License Number (optional)")
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    specialization = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(max_length=100, blank=True)
    barangay = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True, help_text="Set to False to revoke registration access")
    notes = models.TextField(blank=True, help_text="Administrative notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_approved_doctors')
    
    class Meta:
        verbose_name = "Approved Doctor"
        verbose_name_plural = "Approved Doctors"
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name} - {self.specialization}"


class SystemConfiguration(models.Model):
    """System-wide configuration settings managed by superuser"""
    SETTING_TYPES = [
        ('boolean', 'Boolean (Yes/No)'),
        ('integer', 'Integer'),
        ('string', 'Text'),
        ('email', 'Email'),
        ('url', 'URL'),
        ('password', 'Password (masked)'),
    ]
    
    CATEGORY_CHOICES = [
        ('User Management', 'User Management'),
        ('Notifications', 'Notifications'),
        ('System Behavior', 'System Behavior'),
        ('Security', 'Security'),
        ('Email/SMS', 'Email/SMS'),
        ('Display', 'Display'),
        ('Feature Flags', 'Feature Flags'),
        ('System Information', 'System Information'),
    ]
    
    setting_key = models.CharField(max_length=100, unique=True, help_text="Internal key (e.g., 'user_registration_enabled')")
    setting_name = models.CharField(max_length=200, help_text="Display name (e.g., 'User Registration Enabled')")
    setting_value = models.TextField(help_text="Current value")
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='string')
    description = models.TextField(help_text="Description of what this setting does")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='System Behavior')
    is_sensitive = models.BooleanField(default=False, help_text="If True, value will be masked in UI (for passwords/tokens)")
    is_editable = models.BooleanField(default=True, help_text="If False, setting cannot be edited from UI")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_configurations')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "System Configuration"
        verbose_name_plural = "System Configurations"
        ordering = ['category', 'setting_name']
    
    def __str__(self):
        return f"{self.setting_name} ({self.category})"
    
    def get_display_value(self):
        """Return masked value if sensitive, otherwise return actual value"""
        if self.is_sensitive and self.setting_value:
            return "••••••••"
        return self.setting_value
    
    def get_typed_value(self):
        """Convert setting_value to appropriate type based on setting_type"""
        if self.setting_type == 'boolean':
            return self.setting_value.lower() in ('true', 'yes', '1', 'on')
        elif self.setting_type == 'integer':
            try:
                return int(self.setting_value)
            except (ValueError, TypeError):
                return 0
        else:
            return self.setting_value