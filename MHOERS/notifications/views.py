from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Notification
from django.contrib.auth.models import Group
from patients.models import Patient
from referrals.models import Referral
from analytics.ml_utils import predict_disease_for_referral, random_forest_regression_prediction_time
from django.db.models import Count
from facilities.models import Facility

@login_required
def check_notifications(request):
    # Filter notifications based on user role
    if request.user.is_staff or request.user.is_superuser:
        # Admins receive referral_sent notifications
        unread_count = Notification.objects.filter(
            recipient=request.user, 
            is_read=False,
            notification_type='referral_sent'
        ).count()
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
    if request.user.is_staff or request.user.is_superuser:
        # Admins see referral_sent notifications (only their own notifications)
        notifications = Notification.objects.filter(
            recipient=request.user,
            notification_type='referral_sent'
        ).select_related('referral__user').order_by('-created_at')
        
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
    
    context = {
        'active_page': 'notifications'
    }
    # Get all patients
    patients = Patient.objects.annotate(
    referral_count=Count('referral'))
    
    # get all facilities
    facility = Facility.objects.all()
    
    #get only the IDS 
    patientsFat = Patient.objects.select_related('facility').all()
    
    # Filter referrals based on their status
    pending_referrals = Referral.objects.filter(status='pending')
    active_referrals = Referral.objects.filter(status='in-progress')
    referred_referrals = Referral.objects.filter(status='completed')
    rejected_referrals = Referral.objects.filter(status='rejected')
    
    # Get predictions for all referrals
    predictions = {}
    for referral in pending_referrals | active_referrals | referred_referrals | rejected_referrals:
        # Get disease prediction
        disease_pred = predict_disease_for_referral(referral.referral_id)
        # Get completion time prediction
        time_pred =random_forest_regression_prediction_time(referral.referral_id)
        # Store both predictions in a tuple
        predictions[referral.referral_id] = (disease_pred, time_pred)
        
    
    
    # Context data
    context = {
        'active_page': 'referral_list',
        'active_tab': 'tab1',
        'facility': facility,
        'patients': patients,
        'patientFat': patientsFat,
        'pending_referrals': pending_referrals,
        'active_referrals': active_referrals,
        'referred_referrals': referred_referrals,
        'rejected_referrals': rejected_referrals,
        'predictions': predictions,
    }

    # Template selection based on user role
    if request.user.is_staff:
        template = 'patients/admin/patient_list.html'
        page = 'patient_list'
    else:
        template = 'patients/user/referral_list.html'
        page = 'referral_list'
    # Context data
    context = {
        'active_page': page,
        'active_tab': 'tab1',
        'facility': facility,
        'patients': patients,
        'patientFat': patientsFat,
        'pending_referrals': pending_referrals,
        'active_referrals': active_referrals,
        'referred_referrals': referred_referrals,
        'rejected_referrals': rejected_referrals,
        'predictions': predictions,
    }
    
    return render(request, template, context)
    

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
    if request.user.is_staff or request.user.is_superuser:
        relevant_type = 'referral_sent'
    else:
        relevant_type = 'referral_completed'

    # Mark all unread notifications of the relevant type as read
    updated_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
        notification_type=relevant_type,
    ).update(is_read=True)

    # Redirect back to notifications list
    return redirect('notifications:notification_list')
