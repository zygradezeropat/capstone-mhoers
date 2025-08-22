# referral/urls.py
from django.urls import path
from . import views

app_name = 'referrals'

urlpatterns = [
    path('create/', views.create_referral, name='create_referral'),
    path('assessment/', views.assessment, name='assessment'),
    path('referral_list/', views.referral_list, name='referral_list'),
    path('patients/', views.admin_patient_list, name='patient_list'),
    path('update-referral/', views.update_referral_status, name='update_referral_status'),
    path('delete-referral/', views.delete_referral, name='delete_referral'),
    path('referred-referral/', views.referred_referral_status, name='referred_referral_status'),
    path('reject-referral/', views.reject_referral, name='reject_referral'),
    path('referral/predict/<int:referral_id>/', views.get_disease_prediction, name='get_disease_prediction'),
    path('patient/<int:patient_id>/history/', views.get_patient_referral_history, name='patient_referral_history'),
    path('api/referral-counts-by-user/', views.referral_counts_by_user, name='referral_counts_by_user'),
    path('api/monthly-referral-counts-by-user/', views.monthly_referral_counts_by_user, name='monthly_referral_counts_by_user'),
]

