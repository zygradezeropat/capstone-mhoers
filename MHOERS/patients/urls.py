from django.urls import path
from .views import (
    addPatient,
    editPatients,
    deletePatient,
    search_patients,
    barangayPatients,
    get_patient_details,
    get_disease_diagnosis_counts,
    get_monthly_diagnosis_trends,
    monthly_referral_counts_by_user,
    get_medical_history_followups,
    send_today_checkup_sms,
)

urlpatterns = [
    path('barangayPatients/', barangayPatients, name='barangayPatients'),
    path('add_patient/', addPatient, name='addPatient'),
    path('edit_patient/', editPatients, name='editPatient'),
    path('delete_patient/', deletePatient, name='deletePatient'),
    path('api/patients/search/', search_patients, name='search_patients'),
    path('api/patient/<str:patient_id>/', get_patient_details, name='get_patient_details'),
    path('api/disease-diagnosis-counts/', get_disease_diagnosis_counts, name='disease_diagnosis_counts'),
    path('api/monthly-diagnosis-trends/', get_monthly_diagnosis_trends, name='monthly_diagnosis_trends'),
    path('api/referral-counts-by-user/', monthly_referral_counts_by_user, name='referral_counts_by_user'),
    path('api/medical-history-followups/', get_medical_history_followups, name='medical_history_followups'),
    path('api/send-today-checkup-sms/<int:patient_id>/', send_today_checkup_sms, name='send_today_checkup_sms'),
]
