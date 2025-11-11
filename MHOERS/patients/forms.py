from django import forms
from .models import Patient
from facilities.models import Facility

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['first_name', 'middle_name', 'last_name', 'p_address', 'p_number', 'date_of_birth', 'sex', 'facility',
                  'cct_beneficiary', 'phic_status', 'civil_status', 'is_pwd', 'sitio', 'barangay',
                  # PhilHealth fields
                  'philhealth_number', 'philhealth_category', 'private_company_name', 'is_dependent',
                  'dependent_member_name', 'dependent_member_birthday', 'dependent_philhealth_no',
                  # Family history fields
                  'family_history_hypertension', 'family_history_diabetes', 'family_history_cancer',
                  'family_history_asthma', 'family_history_epilepsy', 'family_history_tuberculosis',
                  'family_history_others']
        
    # Customize widget for better UX
    cct_beneficiary = forms.BooleanField(required=False, label='CCT Beneficiary')
    is_pwd = forms.BooleanField(required=False, label='Person With Disability (PWD)')
    phic_status = forms.ChoiceField(
        choices=[('', 'Select Status')] + Patient.PHIC_STATUS_CHOICES,
        required=False,
        label='PHIC Status'
    )
    civil_status = forms.ChoiceField(
        choices=[('', 'Select Status')] + Patient.CIVIL_STATUS_CHOICES,
        required=False,
        label='Civil Status'
    )
    sitio = forms.CharField(required=False, max_length=100, label='Sitio')
    barangay = forms.CharField(required=False, max_length=100, label='Barangay')
    
    # PhilHealth fields
    philhealth_number = forms.CharField(required=False, max_length=50, label='PhilHealth Number')
    philhealth_category = forms.ChoiceField(
        choices=[('', 'Select Category'), ('Sponsored', 'Sponsored'), ('Self Paying', 'Self Paying')],
        required=False,
        label='PhilHealth Category'
    )
    private_company_name = forms.CharField(required=False, max_length=100, label='Private Company Name')
    is_dependent = forms.BooleanField(required=False, label='Is Dependent')
    dependent_member_name = forms.CharField(required=False, max_length=200, label='Dependent Member Name')
    dependent_member_birthday = forms.DateField(required=False, label='Dependent Member Birthday', widget=forms.DateInput(attrs={'type': 'date'}))
    dependent_philhealth_no = forms.CharField(required=False, max_length=50, label='Dependent PhilHealth Number')
    
    # Family history fields
    family_history_hypertension = forms.BooleanField(required=False, label='Family History: Hypertension')
    family_history_diabetes = forms.BooleanField(required=False, label='Family History: Diabetes')
    family_history_cancer = forms.BooleanField(required=False, label='Family History: Cancer')
    family_history_asthma = forms.BooleanField(required=False, label='Family History: Asthma')
    family_history_epilepsy = forms.BooleanField(required=False, label='Family History: Epilepsy')
    family_history_tuberculosis = forms.BooleanField(required=False, label='Family History: Tuberculosis')
    family_history_others = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}), label='Family History: Others')

 