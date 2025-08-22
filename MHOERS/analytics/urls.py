from django.urls import path
from . import views

urlpatterns = [
  path('api/monthly-diagnosis-trends/', views.get_monthly_diagnosis_trends, name='monthly_diagnosis_trends'),
] 