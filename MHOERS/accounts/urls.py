from django.urls import path
from referrals.views import assessment
from .views import *

urlpatterns = [
    path('login/', user_login, name='login'), 
    path('home/', user_home, name='home'),  
    path('register/', register, name='register'),
    path('pending/', pending_dashboard, name='pending_dashboard'),
    path('logout/', user_logout, name='logout'),
    path('referral/', user_referral, name='referral'),
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    path('diseases/', diseases, name='diseases'),
    path('diseases/add/', add_disease, name='add_disease'),
    path('report_analytics/', report_analytics, name='report_analytics'),
    path('system_configuration/', system_configuration, name='system_configuration'),
    path('user_management/', user_management, name='user_management'),
    path('profile/', profile, name='profile'),
    path('user_report/', user_report, name='user_report'),
    path('phistory/', phistory, name='phistory'),
    path('heatmap/', heatmap, name='heatmap'),
    path('calendar/', calendar_view, name='calendar'),
    path("assessment/", assessment, name="assessment"),
    path('approve_user/', approve_user, name='approve_user'),
    path('reject_user/', reject_user, name='reject_user'),
    path('create_doctor/', create_doctor, name='create_doctor'),
    path('create_bhw/', create_bhw, name='create_bhw'),
    path('update_profile/', update_profile, name='update_profile'),
    path('change_password/', change_password, name='change_password'),
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
    path('manage-consent/', manage_consent, name='manage_consent'),
    path('request-deletion/', request_account_deletion, name='request_deletion'),
    path('cancel-deletion/', cancel_deletion_request, name='cancel_deletion'),
]
