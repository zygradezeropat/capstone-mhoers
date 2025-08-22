from django.shortcuts import get_object_or_404
from .models import Notification

#unread markers
def unread_notifications(request):
    unread_count = 0
    user_unread_count = 0

    if request.user.is_authenticated:
        user_unread_count = Notification.objects.filter(recipient_id=request.user, is_read=False).count()
        if request.user.is_staff or request.user.is_superuser:
            unread_count = Notification.objects.filter(is_read=False).count()
    return {
        'unread_count': unread_count,             # For admin (all)
        'user_unread_count': user_unread_count,   # For the logged-in user
    }


def message_notification(request):
    if request.user.is_authenticated:
        messages_notif = Notification.objects.filter(is_read=False
        ).order_by('-created_at')[:5]  # Limit to 5 latest unread notifications
    else:
        messages_notif = []
    return {'messages_notif': messages_notif}