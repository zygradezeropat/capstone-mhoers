from django import forms
from django.contrib.auth.models import User
from facilities.models import Facility

class HealthcareProviderForm(forms.Form):
    # User model fields
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    username = forms.CharField(max_length=30)
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())
    role = forms.ChoiceField(choices=[('BHW', 'Barangay Health Worker'), ('MHO', 'Municipal Health Officer')])

    # Facility model fields
    latitude = forms.FloatField()
    longitude = forms.FloatField()
    
