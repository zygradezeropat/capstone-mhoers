from django.db import models
from django.contrib.auth.models import User

class Facility(models.Model):
    facility_id = models.AutoField(primary_key=True)  
    name = models.CharField(max_length=100)
    assigned_bhw = models.CharField(max_length=100)
    latitude = models.FloatField() 
    longitude = models.FloatField()
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='facilities')


    def __str__(self):
        return self.name    
