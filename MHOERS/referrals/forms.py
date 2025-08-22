from django import forms
from django.forms import ModelForm
from .models import *
from patients.models import Patient

class ReferralForm(forms.ModelForm):
    patient = forms.ModelChoiceField(
        queryset=Patient.objects.all(),
        empty_label="Select Patient",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Fields for the vital signs
    weight = forms.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        required=True, 
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    height = forms.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        required=True, 
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    bp_systolic = forms.IntegerField(
        required=True, 
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Systolic'})
    )
    
    bp_diastolic = forms.IntegerField(
        required=True, 
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Diastolic'})
    )
    
    pulse_rate = forms.IntegerField(
        required=True, 
        min_value=0, max_value=150,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    respiratory_rate = forms.IntegerField(
        required=True, 
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    temperature = forms.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        required=True, 
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    oxygen_saturation = forms.IntegerField(
        required=True, 
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    # Chief Complaint and Symptoms fields
    chief_complaint = forms.CharField(
        required=True, 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    symptoms = forms.CharField(
        required=False, 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )
    
    # Work Up Details
    work_up_details = forms.CharField(
        required=False, 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )

    class Meta:
        model = Referral
        fields = ['patient', 'weight', 'height', 'bp_systolic', 'bp_diastolic', 'pulse_rate', 'respiratory_rate', 
                  'temperature', 'oxygen_saturation', 'chief_complaint', 'symptoms', 'work_up_details']