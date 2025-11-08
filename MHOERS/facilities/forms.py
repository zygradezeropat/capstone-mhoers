from django import forms
from facilities.models import Facility
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
    
class FacilityForm(forms.Form):
    name = forms.CharField(max_length=100)
    assigned_bhw = forms.CharField(max_length=100)
    latitude = forms.FloatField()
    longitude = forms.FloatField()

    def clean_name(self):
        name = self.cleaned_data['name']
        # Enforce case-insensitive uniqueness at form level
        if Facility.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError("A facility with this name already exists.")
        return name

