from django.db import models
from .models import MessageNotification


def chat_context(request):
    """Add chat-related context to all templates"""
    unread_message_count = 0
    
    if request.user.is_authenticated:
        # Get total unread message count for the current user
        unread_message_count = MessageNotification.objects.filter(
            user=request.user
        ).aggregate(total=models.Sum('unread_count'))['total'] or 0
    
    return {
        'unread_message_count': unread_message_count,
    }
