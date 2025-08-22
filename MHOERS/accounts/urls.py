from django.urls import path
from .views import *

urlpatterns = [
    path('login/', user_login, name='login'), 
    path('home/', user_home, name='home'),  
    path('register/', register, name='register'),
    path('logout/', user_logout, name='logout'),
    path('referral/', user_referral, name='referral'),
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    path('health_facilities/', health_facilities, name='health_facilities'),
    path('report_analytics/', report_analytics, name='report_analytics'),
    path('system_configuration/', system_configuration, name='system_configuration'),
    path('user_management/', user_management, name='user_management'),
    path('profile/', profile, name='profile'),
    path('user_report/', user_report, name='user_report'),
    path('phistory/', phistory, name='phistory'),
    path('heatmap/', heatmap, name='heatmap'),
    path('calendar/', calendar_view, name='calendar')
]
