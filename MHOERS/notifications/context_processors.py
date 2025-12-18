from django.shortcuts import get_object_or_404
from .models import Notification

def is_doctor(user):
    """Check if user is a doctor"""
    try:
        from accounts.models import Doctors
        doctor = Doctors.objects.get(user=user)
        return doctor.status == 'ACTIVE'
    except:
        return False

#unread markers
def unread_notifications(request):
    unread_count = 0
    user_unread_count = 0

    if request.user.is_authenticated:
        if is_doctor(request.user):
            # Doctors only receive notifications about referrals from BHW
            from accounts.models import BHWRegistration
            bhw_user_ids = list(BHWRegistration.objects.filter(
                status='ACTIVE'
            ).exclude(
                user__is_staff=True
            ).exclude(
                user__is_superuser=True
            ).values_list('user_id', flat=True))
            
            # Only filter by BHW user IDs if there are any BHW users
            if bhw_user_ids:
                unread_count = Notification.objects.filter(
                    recipient=request.user, 
                    is_read=False,
                    notification_type='referral_sent',
                    referral__user_id__in=bhw_user_ids
                ).count()
            else:
                unread_count = 0
            print(f"🔍 Doctor {request.user.username} has {unread_count} unread notifications (BHW referrals only)")
        elif request.user.is_staff or request.user.is_superuser:
            # Admins only receive account approval request notifications
            # Count pending users (BHW, Doctors, Nurses)
            from accounts.models import BHWRegistration, Doctors, Nurses
            pending_bhw_count = BHWRegistration.objects.filter(status='PENDING_APPROVAL').count()
            pending_doctors_count = Doctors.objects.filter(status='PENDING_APPROVAL').count()
            pending_nurses_count = Nurses.objects.filter(status='PENDING_APPROVAL').count()
            unread_count = pending_bhw_count + pending_doctors_count + pending_nurses_count
            print(f"🔍 Admin {request.user.username} has {unread_count} unread notifications (account approvals only)")
        else:
            # Users receive all notifications
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
        if is_doctor(request.user):
            # Doctors only see notifications about referrals from BHW
            from accounts.models import BHWRegistration
            bhw_user_ids = list(BHWRegistration.objects.filter(
                status='ACTIVE'
            ).exclude(
                user__is_staff=True
            ).exclude(
                user__is_superuser=True
            ).values_list('user_id', flat=True))
            
            # Only filter by BHW user IDs if there are any BHW users
            if bhw_user_ids:
                messages_notif = Notification.objects.filter(
                    recipient=request.user,
                    is_read=False,
                    notification_type='referral_sent',
                    referral__user_id__in=bhw_user_ids
                ).order_by('-created_at')[:5]
            else:
                messages_notif = Notification.objects.none()
            print(f"🔍 Doctor {request.user.username} dropdown has {len(messages_notif)} notifications (BHW referrals only)")
        elif request.user.is_staff or request.user.is_superuser:
            # Admins only see account approval requests (handled by pending_users_count in template)
            # No Notification objects shown in dropdown for admins
            messages_notif = Notification.objects.none()
            print(f"🔍 Admin {request.user.username} dropdown has 0 notifications (only account approvals)")
        else:
            # Users see all notifications
            messages_notif = Notification.objects.filter(
                recipient=request.user,
                is_read=False
            ).order_by('-created_at')[:5]
            print(f"🔍 User {request.user.username} dropdown has {len(messages_notif)} notifications")
    else:
        messages_notif = []
    
    return {'messages_notif': messages_notif}