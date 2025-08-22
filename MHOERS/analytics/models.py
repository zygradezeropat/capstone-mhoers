from django.db import models
from django.contrib.auth.models import User
from facilities.models import Facility

# Disease Model
class Disease(models.Model):
    CRITICALITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    name = models.CharField(max_length=100, unique=True)  # Disease name (e.g., 'Flu')
    description = models.TextField()  # Detailed description of the disease
    symptoms = models.TextField()  # Symptoms associated with the disease
    critical_level = models.CharField(
        max_length=10,
        choices=CRITICALITY_CHOICES,
        default='medium',
        help_text="Level of urgency for this disease"
    )
    time_caters = models.FloatField()

    def __str__(self):
        return self.name


# HealthIssueTrend Model (Trend for health issues across facilities)
class HealthIssueTrend(models.Model):
    disease = models.ForeignKey('Disease', on_delete=models.SET_NULL, null=True)
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True)
    reported_count = models.IntegerField()
    period = models.DateField()  # Period when the disease was reported (e.g., date)

    def __str__(self):
        return f"{self.disease.name} - {self.facility.name} - {self.period}"

    @classmethod
    def get_top_diseases(cls, period):
        return cls.objects.filter(period=period).values('disease').annotate(
            total_cases=models.Sum('reported_count')
        ).order_by('-total_cases')


# DiseaseUrgency Model (Urgency levels associated with a disease)
class DiseaseUrgency(models.Model):
    disease = models.ForeignKey('Disease', on_delete=models.SET_NULL, null=True)
    urgency_level = models.CharField(max_length=20, choices=[
        ('Critical', 'Critical'),
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ])
    time_frame_hours = models.IntegerField(help_text="Time in hours to cater the disease based on urgency level")

    def __str__(self):
        return f'{self.disease.name} - {self.urgency_level}'


# TotalDisease Model (Total count of cases per disease)
class TotalDisease(models.Model):
    disease = models.ForeignKey('Disease', on_delete=models.SET_NULL, null=True)
    total_count = models.IntegerField()  # Total number of cases reported
    period = models.DateField()  # The time period (e.g., daily, weekly, monthly)

    def __str__(self):
        return f"{self.disease.name} - {self.total_count} - {self.period}"


# DiseasePrediction Model (AI or Machine Learning predictions for diseases)
class DiseasePrediction(models.Model):
    description = models.TextField()  # The description or symptoms provided for the prediction
    predicted_disease = models.ForeignKey('Disease', on_delete=models.SET_NULL, null=True)  # Link to the actual Disease model
    confidence_level = models.FloatField()  # The confidence level of the prediction (percentage)
    predicted_at = models.DateTimeField(auto_now_add=True)  # When the prediction was made
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  # Optional: link to the user who provided the description

    def __str__(self):
        return f"{self.predicted_disease.name} - {self.confidence_level}% confidence"

