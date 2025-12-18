from django.urls import path
from django.contrib.auth import views as auth_views
from referrals.views import assessment
from .views import *

urlpatterns = [
    path('login/', user_login, name='login'), 
    path('home/', user_home, name='home'),  
    path('register/', register, name='register'),
    path('api/check-username/', check_username, name='check_username'),
    path('api/check-email/', check_email, name='check_email'),
    path('api/check-phone/', check_phone, name='check_phone'),
    path('api/check-registration-number/', check_registration_number, name='check_registration_number'),
    path('api/check-accreditation-number/', check_accreditation_number, name='check_accreditation_number'),
    path('pending/', pending_dashboard, name='pending_dashboard'),
    path('logout/', user_logout, name='logout'),
    path('referral/', user_referral, name='referral'),
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    path('doctor_dashboard/', doctor_dashboard, name='doctor_dashboard'),
    path('doctor_transactions_report/', doctor_transactions_report, name='doctor_transactions_report'),
    path('diseases/', diseases, name='diseases'),
    path('diseases/add/', add_disease, name='add_disease'),
    path('diseases/<int:disease_id>/update/', update_disease, name='update_disease'),
    path('diseases/<int:disease_id>/delete/', delete_disease, name='delete_disease'),
    path('report_analytics/', report_analytics, name='report_analytics'),
    path('user_management/', user_management, name='user_management'),
    path('profile/', profile, name='profile'),
    path('user_report/', user_report, name='user_report'),
    path('admin_change_user_password/', admin_change_user_password, name='admin_change_user_password'),
    path('admin_update_user_state/', admin_update_user_state, name='admin_update_user_state'),
    path('phistory/', phistory, name='phistory'),
    path('heatmap/', heatmap, name='heatmap'),
    path('calendar/', calendar_view, name='calendar'),
    path("assessment/", assessment, name="assessment"),
    path('approve_user/', approve_user, name='approve_user'),
    path('reject_user/', reject_user, name='reject_user'),
    path('create_doctor/', create_doctor, name='create_doctor'),
    path('create_bhw/', create_bhw, name='create_bhw'),
    path('create_midwife/', create_midwife, name='create_midwife'),
    path('update_bhw_status/', update_bhw_status, name='update_bhw_status'),
    path('edit_bhw/<int:bhw_id>/', edit_bhw, name='edit_bhw'),
    path('edit_approved_bhw/<int:approved_bhw_id>/', edit_approved_bhw, name='edit_approved_bhw'),
    path('update_nurse_status/', update_nurse_status, name='update_nurse_status'),
    path('edit_nurse/<int:nurse_id>/', edit_nurse, name='edit_nurse'),
    path('update_doctor_status/', update_doctor_status, name='update_doctor_status'),
    path('edit_doctor/<int:doctor_id>/', edit_doctor, name='edit_doctor'),
    path('update_profile/', update_profile, name='update_profile'),
    path('change_password/', change_password, name='change_password'),
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
    path('manage-consent/', manage_consent, name='manage_consent'),
    path('request-deletion/', request_account_deletion, name='request_deletion'),
    path('cancel-deletion/', cancel_deletion_request, name='cancel_deletion'),
    
    # Password reset URLs (Django built-in - kept for backward compatibility)
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url='/accounts/password-reset/complete/'
    ), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Custom password reset URLs (works with Hostinger email)
    path('custom-password-reset/', custom_password_reset_request, name='custom_password_reset'),
    path('custom-password-reset-confirm/<str:token>/', custom_password_reset_confirm, name='custom_password_reset_confirm'),
    path('custom-password-reset/done/', custom_password_reset_done, name='custom_password_reset_done'),
]
