from django.db import models
from django.contrib.auth.models import User

class Facility(models.Model):
    facility_id = models.AutoField(primary_key=True)  
    name = models.CharField(max_length=100, unique=True)
    assigned_bhw = models.CharField(max_length=100)
    barangay = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.FloatField() 
    longitude = models.FloatField()
    users = models.ManyToManyField(User, related_name='shared_facilities')


    def __str__(self):
        return self.name    

class Barangay(models.Model):
    barangay_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True, help_text="Set to False to hide from selection without deleting")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Barangay"
        verbose_name_plural = "Barangays"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Purok(models.Model):
    purok_id = models.AutoField(primary_key=True)
    barangay = models.ForeignKey(
        Barangay, 
        on_delete=models.CASCADE,
        related_name='puroks'  # Allows: barangay.puroks.all()
    )
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True, help_text="Set to False to hide from selection without deleting")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Purok"
        verbose_name_plural = "Puroks"
        ordering = ['barangay', 'name']
        unique_together = [['barangay', 'name']]  # Prevents duplicate purok names in same barangay
    
    def __str__(self):
        return f"{self.name}"


