from django.shortcuts import get_object_or_404
from .models import Notification

#unread markers
def unread_notifications(request):
    unread_count = 0
    user_unread_count = 0

    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            # Admins receive all notifications (temporary fix)
            unread_count = Notification.objects.filter(
                recipient=request.user, 
                is_read=False
            ).count()
            print(f"🔍 Admin {request.user.username} has {unread_count} unread notifications")
        else:
            # Users receive all notifications (temporary fix)
            user_unread_count = Notification.objects.filter(
                recipient=request.user, 
                is_read=False
            ).count()
            print(f"🔍 User {request.user.username} has {user_unread_count} unread notifications")
    
    return {
        'unread_count': unread_count,             # For admin (all)
        'user_unread_count': user_unread_count,   # For users (all)
    }


def message_notification(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            # Admins see all notifications (temporary fix)
            messages_notif = Notification.objects.filter(
                recipient=request.user,
                is_read=False
            ).order_by('-created_at')[:5]
            print(f"🔍 Admin {request.user.username} dropdown has {len(messages_notif)} notifications")
        else:
            # Users see all notifications (temporary fix)
            messages_notif = Notification.objects.filter(
                recipient=request.user,
                is_read=False
            ).order_by('-created_at')[:5]
            print(f"🔍 User {request.user.username} dropdown has {len(messages_notif)} notifications")
    else:
        messages_notif = []
    
    return {'messages_notif': messages_notif}