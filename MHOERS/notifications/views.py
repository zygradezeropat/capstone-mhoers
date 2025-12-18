from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Notification
from django.contrib.auth.models import Group
from patients.models import Patient
from referrals.models import Referral
from analytics.ml_utils import predict_disease_for_referral, random_forest_regression_prediction_time
from analytics.models import Disease
from django.db.models import Count, Q
from facilities.models import Facility

def is_doctor(user):
    """Check if user is a doctor"""
    try:
        from accounts.models import Doctors
        doctor = Doctors.objects.get(user=user)
        return doctor.status == 'ACTIVE'
    except:
        return False

def is_bhw_user(user):
    """Check if user is a BHW (not staff/superuser)"""
    if user.is_staff or user.is_superuser:
        return False
    try:
        from accounts.models import BHWRegistration
        bhw = BHWRegistration.objects.get(user=user)
        return bhw.status == 'ACTIVE'
    except:
        return False

@login_required
def check_notifications(request):
    # Filter notifications based on user role
    if is_doctor(request.user):
        # Doctors only receive notifications about referrals from BHW
        # Get BHW user IDs
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
            # No active BHW users, so no notifications
            unread_count = 0
    elif request.user.is_staff or request.user.is_superuser:
        # Admins only receive account approval request notifications
        # Count pending users (BHW, Doctors, Nurses)
        from accounts.models import BHWRegistration, Doctors, Nurses
        pending_bhw_count = BHWRegistration.objects.filter(status='PENDING_APPROVAL').count()
        pending_doctors_count = Doctors.objects.filter(status='PENDING_APPROVAL').count()
        pending_nurses_count = Nurses.objects.filter(status='PENDING_APPROVAL').count()
        unread_count = pending_bhw_count + pending_doctors_count + pending_nurses_count
    else:
        # Users receive referral_completed notifications
        unread_count = Notification.objects.filter(
            recipient=request.user, 
            is_read=False,
            notification_type='referral_completed'
        ).count()
    
    return JsonResponse({'unseen_count': unread_count})

@login_required
def notifications_list(request):
    # Filter notifications based on user role
    if is_doctor(request.user):
        # Doctors only see notifications about referrals from BHW
        # Get BHW user IDs
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
            notifications = Notification.objects.filter(
                recipient=request.user,
                notification_type='referral_sent',
                referral__user_id__in=bhw_user_ids
            ).select_related('referral__user').order_by('-created_at')
        else:
            notifications = Notification.objects.none()
        
        admin_notif = None
        all_referrals = None
    elif request.user.is_staff or request.user.is_superuser:
        # Admins only see account approval requests (handled by pending_users_count in template)
        # No Notification objects shown for admins
        notifications = Notification.objects.none()
        
        # No separate admin_notif - just use notifications
        admin_notif = None
        all_referrals = None
    else:
        # Users see referral_completed notifications
        notifications = Notification.objects.filter(
            recipient=request.user,
            notification_type='referral_completed'
        ).select_related('referral__user').order_by('-created_at')
        
        # Users don't see admin notifications
        admin_notif = None
        all_referrals = None
    
    # Get predictions for notifications with referrals
    predictions = {}
    for notification in notifications:
        if notification.referral:
            try:
                disease_pred = predict_disease_for_referral(notification.referral.referral_id)
                time_pred =random_forest_regression_prediction_time(notification.referral.referral_id)
                predictions[notification.notification_id] = [disease_pred, time_pred] 
            except Exception:
                predictions[notification.notification_id] = ['No prediction available', 0]
    
    # Get unread count for the notification badge
    unread_count = notifications.filter(is_read=False).count()
    
    context = {
        'notifications': notifications,
        'admin_notif': admin_notif,
        'all_referrals': all_referrals,
        'predictions': predictions,
        'unread_count': unread_count,
        'active_page': 'notifications'
    }
    return render(request, 'notifications/notifications_list.html', context)

@login_required
def mark_notification_read(request, notification_id): 
    notification = get_object_or_404(Notification, notification_id=notification_id)
    notification.is_read = True
    notification.save()
    
    # Redirect based on user role
    if is_doctor(request.user):
        # Doctor goes to patients page with assessment mode
        from django.urls import reverse
        return redirect(reverse('referrals:patient_list') + '?mode=assessment')
    elif is_bhw_user(request.user):
        # BHW goes to referral_list
        from django.urls import reverse
        return redirect(reverse('referrals:referral_list'))
    else:
        # For staff/superuser or other users, go to referral_list
        from django.urls import reverse
        return redirect(reverse('referrals:referral_list'))
    

@login_required
def get_notification_details(request, notification_id):
    notification = get_object_or_404(Notification, notification_id=notification_id)
    
    # Get prediction data if notification has a referral
    prediction_data = None
    if notification.referral:
        try:
            disease_pred = predict_disease_for_referral(notification.referral.referral_id)
            time_pred =random_forest_regression_prediction_time(notification.referral.referral_id)
            prediction_data = {
                'disease': disease_pred,
                'time': time_pred
            }
        except Exception:
            prediction_data = {
                'disease': 'No prediction available',
                'time': 0
            }
    
    return JsonResponse({
        'title': notification.title,
        'message': notification.message,
        'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'prediction': prediction_data
    })

@login_required
def debug_notifications(request):
    """Debug view to check notification status"""
    from django.contrib.auth.models import User
    
    # Check staff users
    staff_users = User.objects.filter(is_staff=True)
    staff_info = [{'username': u.username, 'is_staff': u.is_staff, 'is_superuser': u.is_superuser} for u in staff_users]
    
    # Check all notifications
    all_notifications = Notification.objects.all()
    notification_info = []
    for notif in all_notifications:
        notification_info.append({
            'id': notif.notification_id,
            'recipient': notif.recipient.username,
            'title': notif.title,
            'type': notif.notification_type,
            'is_read': notif.is_read,
            'created_at': notif.created_at
        })
    
    # Check user's notifications
    user_notifications = Notification.objects.filter(recipient=request.user)
    user_notification_info = []
    for notif in user_notifications:
        user_notification_info.append({
            'id': notif.notification_id,
            'title': notif.title,
            'type': notif.notification_type,
            'is_read': notif.is_read,
            'created_at': notif.created_at
        })
    
    context = {
        'staff_users': staff_info,
        'all_notifications': notification_info,
        'user_notifications': user_notification_info,
        'current_user': request.user.username,
        'user_is_staff': request.user.is_staff,
        'user_is_superuser': request.user.is_superuser,
    }
    
    return render(request, 'notifications/debug.html', context)
    

    
@login_required
def mark_all_notifications_read(request):
    """Mark all relevant notifications as read for the current user."""
    # Determine which notification types are relevant to the current user
    if is_doctor(request.user):
        # Doctors only mark notifications about referrals from BHW as read
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
            updated_count = Notification.objects.filter(
                recipient=request.user,
                is_read=False,
                notification_type='referral_sent',
                referral__user_id__in=bhw_user_ids
            ).update(is_read=True)
        else:
            updated_count = 0
    elif request.user.is_staff or request.user.is_superuser:
        # Admins don't have Notification objects - only account approval requests (handled by pending_users_count)
        updated_count = 0
    else:
        relevant_type = 'referral_completed'
        updated_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
            notification_type=relevant_type,
        ).update(is_read=True)

    # Redirect back to notifications list
    return redirect('notifications:notification_list')
