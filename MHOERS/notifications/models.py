from django.db import models
from django.contrib.auth.models import User
from referrals.models import Referral

class Notification(models.Model):
    notification_id = models.AutoField(primary_key=True)
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100)
    message = models.TextField()
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipient.username}: {self.title}"
