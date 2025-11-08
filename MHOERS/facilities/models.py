from django.db import models
from django.contrib.auth.models import User

class Facility(models.Model):
    facility_id = models.AutoField(primary_key=True)  
    name = models.CharField(max_length=100, unique=True)
    assigned_bhw = models.CharField(max_length=100)
    latitude = models.FloatField() 
    longitude = models.FloatField()
    users = models.ManyToManyField(User, related_name='shared_facilities')


    def __str__(self):
        return self.name    
