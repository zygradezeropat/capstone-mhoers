
from django.db import models
from django.contrib.auth.models import User
from facilities.models import Facility
from datetime import datetime

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