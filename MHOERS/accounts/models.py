
from django.db import models
from django.contrib.auth.models import User
from facilities.models import Facility

# This extends the User model to associate a user with a specific facility
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.user.username