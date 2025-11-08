from django.urls import path
from . import views

urlpatterns = [
  path('api/monthly-diagnosis-trends/', views.get_monthly_diagnosis_trends, name='monthly_diagnosis_trends'),
  path('api/disease-diagnosis-counts/', views.get_disease_diagnosis_counts, name='disease_diagnosis_counts'),
  path('api/disease-counts-per-user/', views.get_disease_counts_per_user, name='disease_counts_per_user'),
  path('api/referral-statistics/', views.get_referral_statistics, name='referral_statistics'),
  path('api/barangay-performance/', views.get_barangay_performance, name='barangay_performance'),
  path('api/user-referral-summary/', views.get_user_referral_summary, name='user_referral_summary'),
  path('api/system-usage/', views.get_system_usage_data, name='system_usage_data'),
  path('api/disease-peak-predictions/', views.get_disease_peak_predictions, name='disease_peak_predictions'),
  path('reports/system-usage-scorecard/', views.system_usage_scorecard_report, name='system_usage_scorecard_report'),
  path('reports/morbidity/', views.morbidity_report, name='morbidity_report'),
  path('reports/facility-workforce/', views.facility_workforce_masterlist, name='facility_workforce_masterlist'),
  path('reports/referral-registry/', views.referral_registry_report, name='referral_registry_report'),
  path('reports/barangay-referral-performance/', views.barangay_referral_performance_report, name='barangay_referral_performance_report'),
] 