from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.models import Group, User
from django.http import HttpResponse
from notifications.models import Notification
from patients.models import Medical_History, Patient
from referrals.models import Referral
from facilities.models import Facility
from django.core import serializers
from collections import Counter
from datetime import datetime
 
@login_required
@never_cache
def profile(request):
    """Render the user profile page with live stats and recent activities.

    - total/pending/in-progress/completed referrals for current user
    - assigned facility info
    - recent referral activities
    """
    # Assigned facility for this user (if any)
    facility = Facility.objects.filter(user_id=request.user).first()

    # Referral statistics for this user
    user_referrals = Referral.objects.filter(user=request.user)
    total_referrals = user_referrals.count()
    pending_referrals = user_referrals.filter(status='pending').count()
    active_referrals = user_referrals.filter(status='in-progress').count()
    completed_referrals = user_referrals.filter(status='completed').count()

    # Recent activities: latest 10 referrals by this user
    recent_referrals = (
        user_referrals.select_related('patient').order_by('-created_at')[:10]
    )

    # Prepare activity rows
    recent_activities = []
    for r in recent_referrals:
        # Determine activity type label and icon based on status
        if r.status == 'completed':
            activity_type = 'Completed Referral'
            activity_icon = 'check-circle'
            badge_class = 'success'
        elif r.status == 'in-progress':
            activity_type = 'Referral In-Progress'
            activity_icon = 'file-medical'
            badge_class = 'warning text-dark'
        else:
            activity_type = 'New Referral'
            activity_icon = 'file-medical'
            badge_class = 'secondary'

        patient_name = ''
        if hasattr(r.patient, 'first_name'):
            patient_name = f"{r.patient.first_name} {r.patient.last_name}".strip()
        else:
            patient_name = f"#{r.patient_id}"

        recent_activities.append({
            'type': activity_type,
            'icon': activity_icon,
            'patient': patient_name,
            'status': r.status,
            'badge_class': badge_class,
            'created_at': r.created_at,
        })

    context = {
        'active_page': 'profile',
        'facility': facility,
        'total_referrals': total_referrals,
        'pending_referrals': pending_referrals,
        'active_referrals': active_referrals,
        'completed_referrals': completed_referrals,
        'recent_activities': recent_activities,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
@never_cache
def phistory(request):
    # Get all patients for the admin view
    patients = Patient.objects.all().order_by('first_name', 'last_name')
    
    return render(request, 'patients/admin/patient_history.html', {
        'active_page': 'phistory',
        'patients': patients
    })

@login_required
@never_cache
def calendar_view(request):
    """
    Render the medical follow-up calendar page
    """
    return render(request, 'calendar_example.html', {'active_page': 'calendar'})

@login_required
@never_cache
def user_home(request):
        # Get all notifications for the logged-in user
        notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

        history_data = Medical_History.objects.filter(user_id=request.user)
        history_json = serializers.serialize('json', history_data)
        
        total_patients = Patient.objects.filter(user=request.user).count()
        pending_referrals = Referral.objects.filter(user=request.user, status='pending').count()
        active_referrals = Referral.objects.filter(user=request.user, status='in-progress').count()
        completed_referrals = Referral.objects.filter(user=request.user, status='completed').count()
        
        return render(request, 'analytics/dashboard.html', {
            'history_json': history_json,
            'active_page': 'home',
            'total_patients': total_patients,
            'pending_referrals': pending_referrals,
            'active_referrals': active_referrals,
            'completed_referrals': completed_referrals})

@login_required
@never_cache
def user_referral(request):
    # Get all notifications for the logged-in user
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    
    # Count unread notifications
    notification_count = notifications.filter(is_read=False).count()
    
    # Get statistics from models
    total_patients = Patient.objects.filter(user=request.user).count()
    pending_referrals = Referral.objects.filter(status='pending').count()
    active_referrals = Referral.objects.filter(status='in-progress').count()
    completed_referrals = Referral.objects.filter(status='completed').count()
    
    return render(request, 'referrals/referral.html', {
        'active_page': 'referral',
        'total_patients': total_patients,
        'pending_referrals': pending_referrals,
        'active_referrals': active_referrals,
        'completed_referrals': completed_referrals})

@login_required
@never_cache
def admin_dashboard(request):
    
    # Get all notifications for the logged-in user
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    
    # Count unread notifications
    notification_count = notifications.filter(is_read=False).count()
    
    # Get statistics from models
    total_patients = Patient.objects.count()
    pending_referrals = Referral.objects.filter(status='pending').count()
    active_referrals = Referral.objects.filter(status='in-progress').count()
    completed_referrals = Referral.objects.filter(status='completed').count()
    
    
    return render(request, 'analytics/admin_dashboard.html', {
        'active_page': 'admin_dashboard',
        'total_patients': total_patients,
        'pending_referrals': pending_referrals,
        'active_referrals': active_referrals,
        'completed_referrals': completed_referrals
    })


@login_required
@never_cache
def health_facilities(request):
    context = {
        'tab1_name': 'Nearby Facilities',
        'tab2_name': 'Requested Facilities',
        'tab3_name': 'Flagged Facilities',
        'tab4_name': 'All Health Centers',
    }
    return render(request, 'patients/admin/health_facilities.html', {'active_page': 'health_facilities'})


@login_required
@never_cache
def report_analytics(request):
    return render(request, 'analytics/report_analytics.html', {'active_page': 'report_analytics'})

def heatmap(request):
    return render(request, 'analytics/heatmap.html', {'active_page': 'heatmap'})

@login_required 
@never_cache
def system_configuration(request):
    return render(request, 'configuration/system_configuration.html', {'active_page': 'system_configuration'})

@login_required
@never_cache
def user_report(request):
    # Get some basic statistics for the current user
    user = request.user
    current_year = datetime.now().year
    
    # Get user's referral statistics
    user_referrals = Referral.objects.filter(user=user, created_at__year=current_year)
    total_referrals = user_referrals.count()
    pending_referrals = user_referrals.filter(status='pending').count()
    completed_referrals = user_referrals.filter(status='completed').count()
    
    # Get user's top diagnoses
    medical_histories = Medical_History.objects.filter(user_id=user, diagnosed_date__year=current_year)
    illness_counts = Counter(medical_histories.values_list('illness_name', flat=True))
    top_diagnoses = dict(illness_counts.most_common(5))
    
    context = {
        'active_page': 'user_report',
        'total_referrals': total_referrals,
        'pending_referrals': pending_referrals,
        'completed_referrals': completed_referrals,
        'top_diagnoses': top_diagnoses,
        'current_year': current_year
    }
    
    return render(request, 'analytics/user_report.html', context)

@login_required
@never_cache
def user_management(request):
    facilities = Facility.objects.all()
    return render(request, 'accounts/user_management.html', {
        'active_page': 'user_management',
        'facilities': facilities
    })


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('admin_dashboard' if user.is_staff else 'home')  
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')

    # Make sure GET request renders login.html
    return render(request, 'accounts/login.html')


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        role = request.POST['role']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('register')

        try:
            user = User.objects.create_user(username=username, password=password1)
            group = Group.objects.get(name=role)  # Get group based on role
            user.groups.add(group)  # Add user to the role-based group
            user.save()

            login(request, user)
            return redirect('login')

        except Exception as e:
            messages.error(request, str(e))
            return redirect('register')

    return render(request, 'accounts/register.html')

def user_logout(request):
    if not request.user.is_staff: 
        logout(request)
        return redirect('login')
    else:
        return redirect('admin_dashboard')