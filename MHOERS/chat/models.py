from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Conversation(models.Model):
    """Represents a conversation between users"""
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        participant_names = [user.get_full_name() or user.username for user in self.participants.all()]
        return f"Conversation between {', '.join(participant_names)}"
    
    def get_other_participant(self, current_user):
        """Get the other participant in a conversation"""
        return self.participants.exclude(id=current_user.id).first()
    
    def get_last_message(self):
        """Get the last message in this conversation"""
        return self.messages.last()


class Message(models.Model):
    """Represents a message in a conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f" "
    
    def mark_as_read(self):
        """Mark the message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class MessageNotification(models.Model):
    """Tracks unread message notifications for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_notifications')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='notifications')
    unread_count = models.PositiveIntegerField(default=0)
    last_checked = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'conversation']
    
    def __str__(self):
        return f"{self.user.username} - {self.unread_count} unread messages"