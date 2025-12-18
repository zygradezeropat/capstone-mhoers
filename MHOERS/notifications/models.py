from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('referral_sent', 'Referral Sent'),
        ('referral_completed', 'Referral Completed'),
        ('referral_accepted', 'Referral Accepted'),
        ('referral_rejected', 'Referral Rejected'),
        ('password_reset_request', 'Password Reset Request'),
    ]
    
    notification_id = models.AutoField(primary_key=True)
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100)
    message = models.TextField()
    notification_type = models.CharField(max_length=25, choices=NOTIFICATION_TYPES, default='referral_sent')
    referral = models.ForeignKey('referrals.Referral', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipient.username}: {self.title}"
