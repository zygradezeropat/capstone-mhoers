from django.urls import path
from . import views
app_name = 'notifications'

urlpatterns = [
    path('check/', views.check_notifications, name='check_notifications'),
    path('all/', views.notifications_list, name='notification_list'),
    path('mark_notification_read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('mark_all_read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('get_details/<int:notification_id>/', views.get_notification_details, name='get_notification_details'),
    path('debug/', views.debug_notifications, name='debug_notifications'),
]
