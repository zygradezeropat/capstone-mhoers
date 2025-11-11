from django import forms
from django.forms import ModelForm
from .models import *

class BHWRegistrationForm(forms.ModelForm):
    class Meta:
        model = BHWRegistration
        fields = ['accreditationNumber', 'registrationNumber', 'first_name', 'middle_name', 'last_name', 'barangay', 'phone', 'street_address', 'city', 'province', 'postal_code', 'bhw_sub_role', 'assigned_barangay']
        widgets = {
            'accreditationNumber': forms.TextInput(attrs={'class': 'form-control modern-input', 'placeholder': 'Accreditation Number'}),
            'registrationNumber': forms.TextInput(attrs={'class': 'form-control modern-input', 'placeholder': 'Registration Number'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control modern-input', 'placeholder': 'First Name'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control modern-input', 'placeholder': 'Middle Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control modern-input', 'placeholder': 'Last Name'}),
            'barangay': forms.TextInput(attrs={'class': 'form-control modern-input', 'placeholder': 'Barangay'}),
            'phone': forms.TextInput(attrs={'class': 'form-control modern-input', 'placeholder': 'Phone Number'}),
            'street_address': forms.TextInput(attrs={'class': 'form-control modern-input', 'placeholder': 'Street Address'}),
            'city': forms.TextInput(attrs={'class': 'form-control modern-input', 'placeholder': 'City'}),
            'province': forms.TextInput(attrs={'class': 'form-control modern-input', 'placeholder': 'Province'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control modern-input', 'placeholder': 'Postal Code'}),
            'bhw_sub_role': forms.Select(attrs={'class': 'form-select modern-select'}),
            'assigned_barangay': forms.TextInput(attrs={'class': 'form-control modern-input', 'placeholder': 'Assigned Barangay'}),
        }


class ConsentForm(forms.ModelForm):
    """Form for managing user consent preferences"""
    class Meta:
        model = UserConsent
        fields = ['privacy_policy_accepted', 'data_processing_consent', 'marketing_consent']
        widgets = {
            'privacy_policy_accepted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'data_processing_consent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'marketing_consent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'privacy_policy_accepted': 'I accept the Privacy Policy',
            'data_processing_consent': 'I consent to data processing for healthcare services',
            'marketing_consent': 'I consent to receive marketing communications (optional)',
        }


class AccountDeletionRequestForm(forms.ModelForm):
    """Form for requesting account deletion"""
    confirm_deletion = forms.BooleanField(
        required=True,
        label='I understand that this action cannot be undone and all my data will be permanently deleted.',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = AccountDeletionRequest
        fields = []
        # No fields needed - just confirmation checkbox
