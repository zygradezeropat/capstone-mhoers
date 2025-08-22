from django import forms
from .models import Patient
from facilities.models import Facility

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['first_name', 'middle_name', 'last_name', 'p_address', 'p_number', 'date_of_birth', 'sex', 'facility']

