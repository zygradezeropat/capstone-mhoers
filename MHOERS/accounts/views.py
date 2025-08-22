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
 
@login_required
@never_cache
def profile(request):
    return render(request, 'accounts/profile.html', {'active_page': 'profile'})

@login_required
@never_cache
def phistory(request):
    return render(request, 'patients/admin/patient_history.html', {'active_page': 'phistory'})

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
    return render(request, 'analytics/user_report.html', {'active_page': 'user_report'})

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