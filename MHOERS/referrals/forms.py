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
    
    # Additional fields from CSV
    referral_type = forms.ChoiceField(
        choices=Referral.REFERRAL_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    cause = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter the cause of referral...'})
    )
    
    treatments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter treatments given...'})
    )
    
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter additional remarks...'})
    )

    # Lifestyle/Social History fields
    is_smoker = forms.BooleanField(required=False, label='Is Smoker', widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    smoking_sticks_per_day = forms.IntegerField(required=False, min_value=0, label='Smoking: Sticks/Packs per Day', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    is_alcoholic = forms.BooleanField(required=False, label='Is Alcoholic', widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    alcohol_bottles_per_year = forms.IntegerField(required=False, min_value=0, label='Alcohol: Bottles per Year', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    family_planning = forms.BooleanField(required=False, label='Family Planning', widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    family_planning_type = forms.ChoiceField(
        choices=[('', 'Select Type'), ('DMPA', 'DMPA'), ('IMPLANT', 'IMPLANT'), ('IUD', 'IUD'), ('PILLS', 'PILLS')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Family Planning Type'
    )
    
    # Menstrual History fields
    menarche = forms.IntegerField(required=False, min_value=0, max_value=20, label='Menarche (Age)', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    sexually_active = forms.BooleanField(required=False, label='Sexually Active', widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    number_of_partners = forms.IntegerField(required=False, min_value=0, label='Number of Partners', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    is_menopause = forms.BooleanField(required=False, label='Menopause', widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    menopause_age = forms.IntegerField(required=False, min_value=0, max_value=100, label='Menopause Age', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    last_menstrual_period = forms.DateField(required=False, label='Last Menstrual Period (LMP)', widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    period_duration = forms.IntegerField(required=False, min_value=0, label='Period Duration (Days)', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    period_interval = forms.IntegerField(required=False, min_value=0, label='Period Interval (Days)', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    pads_per_day = forms.IntegerField(required=False, min_value=0, label='Pads per Day', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    
    # Pregnancy History fields
    is_pregnant = forms.BooleanField(required=False, label='Is Pregnant', widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    gravidity = forms.IntegerField(required=False, min_value=0, label='Gravidity', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    parity = forms.IntegerField(required=False, min_value=0, label='Parity', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    delivery_type = forms.CharField(required=False, max_length=50, label='Type of Delivery', widget=forms.TextInput(attrs={'class': 'form-control'}))
    full_term_births = forms.IntegerField(required=False, min_value=0, label='Number of Full Term Births', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    premature_births = forms.IntegerField(required=False, min_value=0, label='Number of Premature Births', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    abortions = forms.IntegerField(required=False, min_value=0, label='Number of Abortions', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    living_children = forms.IntegerField(required=False, min_value=0, label='Number of Living Children', widget=forms.NumberInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Referral
        fields = ['patient', 'weight', 'height', 'bp_systolic', 'bp_diastolic', 'pulse_rate', 'respiratory_rate', 
                  'temperature', 'oxygen_saturation', 'chief_complaint', 'symptoms', 'work_up_details',
                  'referral_type', 'cause', 'treatments', 'remarks',
                  # Lifestyle/Social History
                  'is_smoker', 'smoking_sticks_per_day', 'is_alcoholic', 'alcohol_bottles_per_year',
                  'family_planning', 'family_planning_type',
                  # Menstrual History
                  'menarche', 'sexually_active', 'number_of_partners', 'is_menopause', 'menopause_age',
                  'last_menstrual_period', 'period_duration', 'period_interval', 'pads_per_day',
                  # Pregnancy History
                  'is_pregnant', 'gravidity', 'parity', 'delivery_type', 'full_term_births',
                  'premature_births', 'abortions', 'living_children']