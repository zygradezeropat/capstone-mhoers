from django import forms
from django.forms import ModelForm
from .models import *

class BHWRegistrationForm(forms.ModelForm):
    class meta:
        model = BHWRegistration
        fields = ['accreditationNumber', 'registrationNumber', 'first_name', 'middle_name', 'last_name', 'barangay', 'phone', 'street_address', 'city', 'province', 'postal_code', 'bhw_sub_role', 'assigned_barangay']

