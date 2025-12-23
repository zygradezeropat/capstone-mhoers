from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import Group, User
from django.http import HttpResponse, JsonResponse
from notifications.models import Notification
from patients.models import Medical_History, Patient
from referrals.models import Referral
from facilities.models import Facility
from django.core import serializers
from collections import Counter
from django.db.models import Q
from datetime import datetime
from django.utils import timezone
from accounts.models import BHWRegistration, Nurses, Doctors, Midwives, PasswordResetToken
from referrals.utils import send_sms_iprog
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordResetView
from django.conf import settings
from urllib.parse import urlparse
from django.core.mail import send_mail
import re


class CustomPasswordResetView(PasswordResetView):
    """Custom password reset that uses SITE_URL from settings"""
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    html_email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = '/accounts/password-reset/done/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(settings, 'SITE_URL') and settings.SITE_URL:
            parsed = urlparse(settings.SITE_URL)
            context['domain'] = parsed.netloc
            context['protocol'] = parsed.scheme
        return context


@login_required
@never_cache
def profile(request):
    """
    Render the user profile page with:
    - total/pending/in-progress/completed referrals (shared per facility)
    - assigned facility info
    - recent referral activities
    - If user is staff/admin, show all activities across all facilities
    """
    # Check if user is approved - if not, redirect to pending dashboard
    is_approved = True
    is_pending = False
    
    # Check BHW status
    try:
        bhw_profile = BHWRegistration.objects.get(user=request.user)
        if bhw_profile.status == 'PENDING_APPROVAL':
            is_approved = False
            is_pending = True
        elif bhw_profile.status == 'REJECTED':
            is_approved = False
    except BHWRegistration.DoesNotExist:
        pass
    
    # Check Doctor status
    try:
        doctor_profile = Doctors.objects.get(user=request.user)
        if doctor_profile.status == 'PENDING_APPROVAL':
            is_approved = False
            is_pending = True
        elif doctor_profile.status == 'REJECTED':
            is_approved = False
    except Doctors.DoesNotExist:
        pass
    
    # Check Nurse status
    try:
        nurse_profile = Nurses.objects.get(user=request.user)
        if nurse_profile.status == 'PENDING_APPROVAL':
            is_approved = False
            is_pending = True
        elif nurse_profile.status == 'REJECTED':
            is_approved = False
    except Nurses.DoesNotExist:
        pass
    
    # Check Midwife status
    try:
        midwife_profile = Midwives.objects.get(user=request.user)
        if midwife_profile.status == 'PENDING_APPROVAL':
            is_approved = False
            is_pending = True
        elif midwife_profile.status == 'REJECTED':
            is_approved = False
    except Midwives.DoesNotExist:
        pass
    
    # If user has a profile and is not approved, redirect to pending dashboard
    has_profile = any([
        BHWRegistration.objects.filter(user=request.user).exists(),
        Doctors.objects.filter(user=request.user).exists(),
        Nurses.objects.filter(user=request.user).exists(),
        Midwives.objects.filter(user=request.user).exists()
    ])
    
    if has_profile and not is_approved:
        return redirect('pending_dashboard')
    
    # Get the facility (or facilities) that this user is assigned to
    facilities = request.user.shared_facilities.all()

    # Just in case a user belongs to multiple facilities
    facility = facilities.first() if facilities.exists() else None

    # Check if user is a doctor
    is_doctor = False
    try:
        doctor_profile = Doctors.objects.get(user=request.user)
        if doctor_profile.status == 'ACTIVE':
            is_doctor = True
    except Doctors.DoesNotExist:
        pass
    
    # If user is staff/admin, get referrals from ALL facilities
    # Otherwise, get referrals only from their assigned facilities
    if request.user.is_staff or request.user.is_superuser:
        # Staff/admin can see all referrals across all facilities
        user_referrals = Referral.objects.all()
        facility = None  # Not assigned to a specific facility
    else:
        # Regular users see only their facility's referrals
        user_referrals = Referral.objects.filter(facility__in=facilities)

    # Referral stats
    # For doctors:
    # - Pending: All pending referrals (system-wide, not filtered by facility or examined_by)
    # - In-Progress: Only referrals they accepted (examined_by = doctor)
    # - Completed: Only referrals they completed (examined_by = doctor and status = completed)
    if is_doctor and not (request.user.is_staff or request.user.is_superuser):
        # Doctor view: pending shows all pending system-wide, but in-progress and completed only show their own
        total_referrals = Referral.objects.count()  # Total for reference (not displayed but may be used)
        pending_referrals = Referral.objects.filter(status='pending').count()
        active_referrals = Referral.objects.filter(status='in-progress', examined_by=request.user).count()
        completed_referrals = Referral.objects.filter(status='completed', examined_by=request.user).count()
    else:
        # Non-doctor view: show all referrals based on facility
        total_referrals = user_referrals.count()
        pending_referrals = user_referrals.filter(status='pending').count()
        active_referrals = user_referrals.filter(status='in-progress').count()
        completed_referrals = user_referrals.filter(status='completed').count()

    # Recent 10 referrals
    # For doctors, show only referrals they examined (in-progress and completed) or all pending
    if is_doctor and not (request.user.is_staff or request.user.is_superuser):
        # Doctor view: show all pending referrals + their own in-progress and completed
        recent_referrals = (
            Referral.objects.filter(
                Q(status='pending') | 
                Q(status='in-progress', examined_by=request.user) |
                Q(status='completed', examined_by=request.user)
            )
            .select_related('patient', 'patient__facility', 'facility')
            .order_by('-created_at')[:10]
        )
    else:
        recent_referrals = (
            user_referrals.select_related('patient', 'patient__facility', 'facility')
            .order_by('-created_at')[:10]
        )

    # Build the recent activity list
    recent_activities = []
    for r in recent_referrals:
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

        patient_name = getattr(r.patient, 'first_name', f"#{r.patient_id}")
        if hasattr(r.patient, 'last_name'):
            patient_name = f"{r.patient.first_name} {r.patient.last_name}".strip()

        # Get facility name - check both referral.facility and patient.facility
        facility_name = "No Facility"
        if r.facility:
            facility_name = r.facility.name
        elif r.patient and r.patient.facility:
            facility_name = r.patient.facility.name

        recent_activities.append({
            'type': activity_type,
            'icon': activity_icon,
            'patient': patient_name,
            'status': r.status,
            'badge_class': badge_class,
            'created_at': r.created_at,
            'facility': facility_name,
        })

    # Get user consent information
    from .models import UserConsent, AccountDeletionRequest
    try:
        user_consent = request.user.consent
    except UserConsent.DoesNotExist:
        user_consent = None
    
    try:
        deletion_request = request.user.deletion_request
    except AccountDeletionRequest.DoesNotExist:
        deletion_request = None

    context = {
        'active_page': 'profile',
        'facility': facility,
        'total_referrals': total_referrals,
        'pending_referrals': pending_referrals,
        'active_referrals': active_referrals,
        'completed_referrals': completed_referrals,
        'recent_activities': recent_activities,
        'user_consent': user_consent,
        'deletion_request': deletion_request,
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
    user = request.user
    notifications = Notification.objects.filter(recipient=user).order_by('-created_at')

    # Get facility for this user (if applicable)
    # Check multiple sources: shared_facilities, BHWRegistration, and users relationship
    facility = None
    
    # First, check if user has shared facilities (ManyToMany relationship)
    facility = user.shared_facilities.first()
    
    # If no facility from shared_facilities, check if user is BHW and get facility from BHWRegistration
    if not facility:
        try:
            bhw_profile = BHWRegistration.objects.select_related('facility').get(user=user)
            if bhw_profile.facility:
                facility = bhw_profile.facility
        except BHWRegistration.DoesNotExist:
            pass
    
    # If still no facility, check the users relationship (fallback)
    if not facility:
        facility = Facility.objects.filter(users=user).first()

    # Get medical history
    history_data = Medical_History.objects.filter(user_id=user)
    history_json = serializers.serialize('json', history_data)

    # Referral and patient stats
    if facility:
        # Show all patients in the facility (not just ones created by this user)
        total_patients = Patient.objects.filter(facility=facility).count()
        pending_referrals = Referral.objects.filter(facility=facility, status='pending').count()
        # Ongoing Referrals includes both pending and in-progress
        active_referrals = Referral.objects.filter(facility=facility, status__in=['pending', 'in-progress']).count()
        completed_referrals = Referral.objects.filter(facility=facility, status='completed').count()
    else:
        total_patients = pending_referrals = active_referrals = completed_referrals = 0

    context = {
        'history_json': history_json,
        'notifications': notifications,
        'active_page': 'home',
        'facility': facility,
        'total_patients': total_patients,
        'pending_referrals': pending_referrals,
        'active_referrals': active_referrals,
        'completed_referrals': completed_referrals,
    }

    return render(request, 'analytics/dashboard.html', context)

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
    """
    Admin dashboard showing utilities statistics only (not medical data).
    Superuser should only see system utilities: users, facilities, approvals.
    """
    # ✅ UTILITIES STATISTICS (not medical)
    total_users = User.objects.count()
    total_facilities = Facility.objects.count()
    
    # Pending user approvals
    pending_bhw = BHWRegistration.objects.filter(status='PENDING_APPROVAL').count()
    pending_doctors = Doctors.objects.filter(status='PENDING_APPROVAL').count()
    pending_nurses = Nurses.objects.filter(status='PENDING_APPROVAL').count()
    pending_midwives = Midwives.objects.filter(status='PENDING_APPROVAL').count()
    total_pending_users = pending_bhw + pending_doctors + pending_nurses + pending_midwives
    
    # Active users
    active_bhw = BHWRegistration.objects.filter(status='APPROVED').count()
    active_doctors = Doctors.objects.filter(status='ACTIVE').count()
    active_nurses = Nurses.objects.filter(status='APPROVED').count()
    active_midwives = Midwives.objects.filter(status='APPROVED').count()
    total_active_users = active_bhw + active_doctors + active_nurses + active_midwives
    
    # ❌ REMOVED: Medical statistics (patients, referrals)
    # These should not be shown to superuser - only utilities
    
    return render(request, 'analytics/admin_dashboard.html', {
        'active_page': 'admin_dashboard',
        # ✅ UTILITIES DATA
        'total_users': total_users,
        'total_facilities': total_facilities,
        'total_pending_users': total_pending_users,
        'total_active_users': total_active_users,
        'pending_bhw': pending_bhw,
        'pending_doctors': pending_doctors,
        'pending_nurses': pending_nurses,
        'pending_midwives': pending_midwives,
        # ❌ REMOVED: Medical data (patients, referrals, etc.)
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
    from facilities.models import Facility
    
    # Get facilities based on user permissions
    if request.user.is_staff or request.user.is_superuser:
        facilities = Facility.objects.all().order_by('name')
    else:
        facilities = request.user.shared_facilities.all().order_by('name')
    
    return render(request, 'analytics/report_analytics.html', {
        'active_page': 'report_analytics',
        'facilities': facilities
    })

@login_required
@never_cache
def diseases(request):
    from analytics.models import Disease
    from accounts.models import Doctors
    
    diseases = Disease.objects.all().order_by('icd_code')
    # Get doctors for the verification dropdown
    # If the logged-in user is a doctor, show only that doctor
    # Otherwise, show all approved doctors (for staff/admin)
    current_doctor_id = None
    try:
        current_doctor = Doctors.objects.get(user=request.user, status__in=['APPROVED', 'ACTIVE'])
        # Show only the logged-in doctor
        doctors = Doctors.objects.filter(doctor_id=current_doctor.doctor_id)
        current_doctor_id = current_doctor.doctor_id
    except Doctors.DoesNotExist:
        # User is not a doctor, show all approved doctors
        doctors = Doctors.objects.filter(status='APPROVED').order_by('last_name', 'first_name')
    
    # Map verified_by users to doctor profiles for quick lookup
    # Need to get all approved doctors for the lookup, not just the filtered list
    all_doctors = Doctors.objects.filter(status='APPROVED')
    doctor_lookup = {doctor.user_id: doctor for doctor in all_doctors if doctor.user_id}
    
    diseases_payload = []
    for disease in diseases:
        verified_by_name = disease.verified_by.get_full_name() if disease.verified_by else None
        verified_by_email = disease.verified_by.email if disease.verified_by else None
        verified_at_display = (
            timezone.localtime(disease.verified_at).strftime('%B %d, %Y %I:%M %p')
            if disease.verified_at else None
        )
        verified_doctor_id = None
        if disease.verified_by_id and disease.verified_by_id in doctor_lookup:
            verified_doctor_id = str(doctor_lookup[disease.verified_by_id].doctor_id)
        
        diseases_payload.append({
            'id': disease.id,
            'icd_code': disease.icd_code,
            'name': disease.name,
            'description': disease.description,
            'critical_level': disease.critical_level,
            'common_symptoms': disease.common_symptoms or "",
            'treatment_protocol': disease.treatment_protocol or "",
            'treatment_guidelines': disease.treatment_guidelines or "",
            'verified_by': verified_by_name,
            'verified_by_email': verified_by_email,
            'verified_at': verified_at_display,
            'verified_doctor_id': verified_doctor_id,
        })
    
    return render(request, 'analytics/diseases.html', {
        'active_page': 'diseases',
        'diseases': diseases,
        'doctors': doctors,
        'diseases_payload': diseases_payload,
        'current_doctor_id': current_doctor_id,
    })

@login_required
@never_cache
def add_disease(request):
    from analytics.models import Disease
    from accounts.models import Doctors
    from django.contrib import messages
    
    if request.method == 'POST':
        try:
            icd_code = request.POST.get('icd_code', '').strip()
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            critical_level = request.POST.get('critical_level', 'medium')
            
            # Validate required fields
            if not all([icd_code, name, description]):
                messages.error(request, "All required fields must be filled.")
                return redirect('diseases')
            
            # Validate critical level
            if critical_level not in ['high', 'medium', 'low']:
                critical_level = 'medium'
            
            # Check if ICD code already exists
            if Disease.objects.filter(icd_code=icd_code).exists():
                messages.error(request, f"Disease with ICD code '{icd_code}' already exists.")
                return redirect('diseases')
            
            # Check if name already exists
            if Disease.objects.filter(name=name).exists():
                messages.error(request, f"Disease '{name}' already exists.")
                return redirect('diseases')
            
            # Get symptoms and treatment fields
            common_symptoms = request.POST.get('common_symptoms', '').strip()
            treatment_protocol = request.POST.get('treatment_protocol', '').strip()
            treatment_guidelines = request.POST.get('treatment_guidelines', '').strip()
            
            # Get verified_by doctor
            verified_by_user = None
            verified_at = None
            doctor_id = request.POST.get('verified_by_doctor', '').strip()
            
            if doctor_id:
                try:
                    doctor = Doctors.objects.get(doctor_id=doctor_id)
                    # Get the User associated with this doctor
                    if doctor.user:
                        verified_by_user = doctor.user
                        verified_at = timezone.now()
                except Doctors.DoesNotExist:
                    pass
            
            # If no doctor selected, use current user as verifier
            if not verified_by_user:
                verified_by_user = request.user
                verified_at = timezone.now()
            
            # Create new disease
            disease = Disease.objects.create(
                icd_code=icd_code,
                name=name,
                description=description,
                critical_level=critical_level,
                common_symptoms=common_symptoms if common_symptoms else None,
                treatment_protocol=treatment_protocol if treatment_protocol else None,
                treatment_guidelines=treatment_guidelines if treatment_guidelines else None,
                verified_by=verified_by_user,
                verified_at=verified_at,
            )
            
            messages.success(request, f"Disease '{name}' (ICD: {icd_code}) has been successfully added!")
            return redirect('diseases')
            
        except Exception as e:
            messages.error(request, f"Error adding disease: {str(e)}")
            return redirect('diseases')
    
    return redirect('diseases')


@login_required
@never_cache
@require_http_methods(["POST"])
def update_disease(request, disease_id):
    from analytics.models import Disease
    from accounts.models import Doctors
    
    disease = get_object_or_404(Disease, pk=disease_id)
    
    try:
        icd_code = request.POST.get('icd_code', '').strip()
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        critical_level = request.POST.get('critical_level', 'medium')
        
        if not all([icd_code, name, description]):
            return JsonResponse({'error': "ICD code, name, and description are required."}, status=400)
        
        if critical_level not in ['high', 'medium', 'low']:
            critical_level = 'medium'
        
        if Disease.objects.exclude(pk=disease_id).filter(icd_code=icd_code).exists():
            return JsonResponse({'error': f"Another disease already uses ICD code '{icd_code}'."}, status=400)
        
        if Disease.objects.exclude(pk=disease_id).filter(name=name).exists():
            return JsonResponse({'error': f"Another disease already uses the name '{name}'."}, status=400)
        
        disease.icd_code = icd_code
        disease.name = name
        disease.description = description
        disease.critical_level = critical_level
        disease.common_symptoms = request.POST.get('common_symptoms', '').strip() or None
        disease.treatment_protocol = request.POST.get('treatment_protocol', '').strip() or None
        disease.treatment_guidelines = request.POST.get('treatment_guidelines', '').strip() or None
        
        doctor_id = request.POST.get('verified_by_doctor', '').strip()
        if doctor_id:
            try:
                doctor = Doctors.objects.get(doctor_id=doctor_id)
                if doctor.user:
                    disease.verified_by = doctor.user
                    disease.verified_at = timezone.now()
            except Doctors.DoesNotExist:
                pass
        elif disease.verified_by is None:
            disease.verified_by = request.user
            disease.verified_at = timezone.now()
        
        disease.save()
        return JsonResponse({'message': f"Disease '{name}' has been updated successfully."})
    except Exception as exc:
        return JsonResponse({'error': f"Unable to update disease: {exc}"}, status=400)


@login_required
@never_cache
@require_http_methods(["POST"])
def delete_disease(request, disease_id):
    from analytics.models import Disease
    
    disease = get_object_or_404(Disease, pk=disease_id)
    disease_name = disease.name
    
    try:
        disease.delete()
        return JsonResponse({'message': f"Disease '{disease_name}' has been deleted."})
    except Exception as exc:
        return JsonResponse({'error': f"Unable to delete disease: {exc}"}, status=400)

def heatmap(request):
    return render(request, 'analytics/heatmap.html', {'active_page': 'heatmap'})

# System configuration view removed - feature not implemented
# @login_required 
# @never_cache
# def system_configuration(request):
#     """System configuration management - superuser only"""
#     pass

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
    
    # Get facilities associated with the user
    from facilities.models import Facility
    facilities = Facility.objects.filter(users=user).distinct()
    
    context = {
        'active_page': 'user_report',
        'total_referrals': total_referrals,
        'pending_referrals': pending_referrals,
        'completed_referrals': completed_referrals,
        'top_diagnoses': top_diagnoses,
        'current_year': current_year,
        'facilities': facilities
    }
    
    return render(request, 'analytics/user_report.html', context)

@login_required
@never_cache
def user_management(request):
    active_tab = request.GET.get('active_tab', 'tab1')
    facilities = Facility.objects.all()
    
    # Show all approved BHWs from whitelist in Accredited BHW tab
    from accounts.models import ApprovedBHW
    bhwnames = ApprovedBHW.objects.all().order_by('-created_at')
    # Get all doctors (will filter in template to only show those with users)
    doctors = Doctors.objects.all().order_by('last_name', 'first_name')
    nurses = Nurses.objects.filter(status='APPROVED')
    midwives = Midwives.objects.filter(status='APPROVED')
    
    # Get pending users
    pending_bhw = BHWRegistration.objects.filter(status='PENDING_APPROVAL')
    pending_doctors = Doctors.objects.filter(status='PENDING_APPROVAL')
    pending_nurses = Nurses.objects.filter(status='PENDING_APPROVAL')
    pending_midwives = Midwives.objects.filter(status='PENDING_APPROVAL')
    
    # Get active users (users that are active and have profiles)
    from django.contrib.auth.models import User
    active_users = User.objects.filter(is_active=True).select_related().order_by('username')
    inactive_users = User.objects.filter(is_active=False).select_related().order_by('username')
    
    # Get user details with their roles
    active_users_list = []
    for user in active_users:
        user_info = {
            'user': user,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': 'Unknown',
            'profile_id': None,
            'date_created': timezone.localtime(user.date_joined).strftime('%B %d, %Y %I:%M %p'),
        }
        
        # Check what type of user they are and get facility
        facility_name = None
        try:
            bhw = BHWRegistration.objects.select_related('facility').get(user=user)
            if bhw.status == 'ACTIVE':
                user_info['role'] = 'BHW'
                user_info['profile_id'] = bhw.bhw_id
                if bhw.facility:
                    facility_name = bhw.facility.name
        except BHWRegistration.DoesNotExist:
            pass
        
        try:
            doctor = Doctors.objects.select_related('facility').get(user=user)
            if doctor.status in ['APPROVED', 'ACTIVE']:
                user_info['role'] = 'Doctor'
                user_info['profile_id'] = doctor.doctor_id
                if doctor.facility:
                    facility_name = doctor.facility.name
        except Doctors.DoesNotExist:
            pass
        
        try:
            nurse = Nurses.objects.get(user=user)
            if nurse.status == 'APPROVED':
                user_info['role'] = 'Nurse'
                user_info['profile_id'] = nurse.nurse_id
        except Nurses.DoesNotExist:
            pass
        
        try:
            midwife = Midwives.objects.get(user=user)
            if midwife.status == 'APPROVED':
                user_info['role'] = 'Midwife'
                user_info['profile_id'] = midwife.midwife_id
        except Midwives.DoesNotExist:
            pass
        
        # Get facility from shared_facilities if not already found
        if not facility_name:
            facility = user.shared_facilities.first()
            if facility:
                facility_name = facility.name
            else:
                # Fallback: check Facility.users relationship
                facility = Facility.objects.filter(users=user).first()
                if facility:
                    facility_name = facility.name
        
        user_info['facility'] = facility_name or 'N/A'
        
        # Only include users with a role (exclude superusers without profiles)
        if user_info['role'] != 'Unknown' or user.is_superuser:
            if user.is_superuser:
                user_info['role'] = 'Administrator'
            user_info['status'] = 'Active' if user.is_active else 'Inactive'
            active_users_list.append(user_info)

    # Get inactive users details with their roles
    inactive_users_list = []
    for user in inactive_users:
        user_info = {
            'user': user,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': 'Unknown',
            'profile_id': None,
        }
        
        # Check what type of user they are and get facility
        facility_name = None
        try:
            bhw = BHWRegistration.objects.select_related('facility').get(user=user)
            user_info['role'] = 'BHW'
            user_info['profile_id'] = bhw.bhw_id
            if bhw.facility:
                facility_name = bhw.facility.name
        except BHWRegistration.DoesNotExist:
            pass
        
        try:
            doctor = Doctors.objects.select_related('facility').get(user=user)
            user_info['role'] = 'Doctor'
            user_info['profile_id'] = doctor.doctor_id
            if doctor.facility:
                facility_name = doctor.facility.name
        except Doctors.DoesNotExist:
            pass
        
        try:
            nurse = Nurses.objects.get(user=user)
            user_info['role'] = 'Nurse'
            user_info['profile_id'] = nurse.nurse_id
        except Nurses.DoesNotExist:
            pass
        
        try:
            midwife = Midwives.objects.get(user=user)
            user_info['role'] = 'Midwife'
            user_info['profile_id'] = midwife.midwife_id
        except Midwives.DoesNotExist:
            pass
        
        # Get facility from shared_facilities if not already found
        if not facility_name:
            facility = user.shared_facilities.first()
            if facility:
                facility_name = facility.name
            else:
                # Fallback: check Facility.users relationship
                facility = Facility.objects.filter(users=user).first()
                if facility:
                    facility_name = facility.name
        
        user_info['facility'] = facility_name or 'N/A'
        
        # Only include users with a role (exclude superusers without profiles)
        if user_info['role'] != 'Unknown' or user.is_superuser:
            if user.is_superuser:
                user_info['role'] = 'Administrator'
            user_info['status'] = 'Inactive'
            inactive_users_list.append(user_info)

    return render(request, 'accounts/user_management.html', {
        'active_page': 'user_management', 
        'facilities': facilities,
        'active_tab': active_tab,
        'bhwnames': bhwnames,
        'doctors': doctors,
        'nurses': nurses,
        'midwives': midwives,
        'pending_bhw': pending_bhw,
        'pending_doctors': pending_doctors,
        'pending_nurses': pending_nurses,
        'pending_midwives': pending_midwives,
        'active_users': active_users_list,
        'inactive_users': inactive_users_list,
    })

@login_required
@never_cache
def admin_change_user_password(request):
    """Allow admin to change any user's password"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_password = request.POST.get('new_password')
        
        if not user_id or not new_password:
            return JsonResponse({'error': 'User ID and new password are required'}, status=400)
        
        if len(new_password) < 8:
            return JsonResponse({'error': 'Password must be at least 8 characters long'}, status=400)
        
        try:
            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.save()
            return JsonResponse({'success': True, 'message': f'Password updated successfully for {user.username}'})
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required
@require_POST
def admin_update_user_state(request):
    """Activate, deactivate, or delete a user account."""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    user_id = request.POST.get('user_id')
    action = request.POST.get('action')
    
    if not user_id or not action:
        return JsonResponse({'error': 'User ID and action are required'}, status=400)
    
    try:
        user = User.objects.get(id=user_id)
        
        if user == request.user and action == 'delete':
            return JsonResponse({'error': 'You cannot delete your own account.'}, status=400)
        
        if action == 'activate':
            user.is_active = True
            user.save()
            return JsonResponse({'success': True, 'message': f'{user.username} is now active.', 'status': 'Active'})
        elif action == 'deactivate':
            user.is_active = False
            user.save()
            return JsonResponse({'success': True, 'message': f'{user.username} is now inactive.', 'status': 'Inactive'})
        elif action == 'delete':
            username = user.username
            user.delete()
            return JsonResponse({'success': True, 'message': f'User {username} has been deleted.'})
        else:
            return JsonResponse({'error': 'Invalid action.'}, status=400)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def user_login(request):
    if request.method == 'POST':
        username_or_email = request.POST['username']
        password = request.POST['password']
        
        # Check if input is an email (contains @)
        if '@' in username_or_email:
            try:
                # Try to find user by email
                user_obj = User.objects.get(email=username_or_email)
                username = user_obj.username
            except User.DoesNotExist:
                username = None
        else:
            # Use as username
            username = username_or_email
        
        # Authenticate with username (or None if email not found)
        user = authenticate(request, username=username, password=password) if username else None

        if user:
            # Check if user's registration is approved or pending
            is_approved = False
            is_pending = False
            
            # Check BHW status
            try:
                bhw_profile = BHWRegistration.objects.get(user=user)
                if bhw_profile.status == 'ACTIVE':
                    is_approved = True
                elif bhw_profile.status == 'PENDING_APPROVAL':
                    is_pending = True
                elif bhw_profile.status == 'REJECTED':
                    messages.error(request, f'Your registration was rejected. Reason: {bhw_profile.rejection_reason}')
                    return redirect('login')
            except BHWRegistration.DoesNotExist:
                pass
            
            # Check Doctor status
            try:
                doctor_profile = Doctors.objects.get(user=user)
                if doctor_profile.status == 'ACTIVE':
                    is_approved = True
                elif doctor_profile.status == 'PENDING_APPROVAL':
                    is_pending = True
                elif doctor_profile.status == 'REJECTED':
                    messages.error(request, f'Your registration was rejected. Reason: {doctor_profile.rejection_reason}')
                    return redirect('login')
            except Doctors.DoesNotExist:
                pass
            
            # Check Nurse status
            try:
                nurse_profile = Nurses.objects.get(user=user)
                if nurse_profile.status == 'APPROVED':
                    is_approved = True
                elif nurse_profile.status == 'PENDING_APPROVAL':
                    is_pending = True
                elif nurse_profile.status == 'REJECTED':
                    messages.error(request, f'Your registration was rejected. Reason: {nurse_profile.rejection_reason}')
                    return redirect('login')
            except Nurses.DoesNotExist:
                pass
            
            # Check Midwife status
            try:
                midwife_profile = Midwives.objects.get(user=user)
                if midwife_profile.status == 'APPROVED':
                    is_approved = True
                elif midwife_profile.status == 'PENDING_APPROVAL':
                    is_pending = True
                elif midwife_profile.status == 'REJECTED':
                    messages.error(request, f'Your registration was rejected. Reason: {midwife_profile.rejection_reason}')
                    return redirect('login')
            except Midwives.DoesNotExist:
                pass
            
            # If user has no profile or is approved, allow full login
            if is_approved or not any([BHWRegistration.objects.filter(user=user).exists(), 
                                     Doctors.objects.filter(user=user).exists(), 
                                     Nurses.objects.filter(user=user).exists(),
                                     Midwives.objects.filter(user=user).exists()]):
                login(request, user)
                # Log the login
                from .models import LoginLog
                LoginLog.objects.create(
                    user=user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
                )
                # Check if user is a doctor and redirect to doctor dashboard
                try:
                    doctor_profile = Doctors.objects.get(user=user)
                    if doctor_profile.status == 'ACTIVE':
                        return redirect('doctor_dashboard')
                except Doctors.DoesNotExist:
                    pass
                
                return redirect('admin_dashboard' if user.is_staff else 'home')
            
            # If pending, allow login but redirect to pending dashboard
            if is_pending:
                login(request, user)
                # Log the login
                from .models import LoginLog
                LoginLog.objects.create(
                    user=user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
                )
                return redirect('pending_dashboard')
            
            # Fallback: block if neither approved nor pending
            messages.error(request, 'Your account is not approved yet.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid username/email or password.')
            return redirect('login')

    # Make sure GET request renders login.html
    response = render(request, 'accounts/login.html')
    # Prevent back navigation after logout
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@login_required
def create_doctor(request):
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            middle_name = request.POST.get('middle_name', '')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            specialization = request.POST.get('specialization')
            license_number = request.POST.get('license_number')
            
            # Validate required fields (license_number is optional based on model)
            if not all([first_name, last_name, email, phone, specialization]):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'type': 'error', 'title': 'Error', 'message': 'All required fields must be filled.'}, status=400)
                messages.error(request, "All required fields must be filled.")
                return redirect('user_management')
            
            # Check if there's already a Doctors profile with this email
            existing_doctor = Doctors.objects.filter(email=email).first()
            if existing_doctor:
                error_msg = f"Email already registered to Dr. {existing_doctor.first_name} {existing_doctor.last_name}. Please use a different email or update the existing doctor profile."
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'type': 'error', 'title': 'Error', 'message': error_msg}, status=400)
                messages.error(request, error_msg)
                return redirect('user_management')
            
            # Create doctor profile WITHOUT User account
            doctor = Doctors.objects.create(
                user=None,  # No user account created
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                email=email,
                phone=phone,
                specialization=specialization,
                license_number=license_number or '',  # Allow empty string
                status='ACTIVE',  # Auto-approve when created by admin
                approved_by=request.user,
                approved_at=timezone.now(),
            )
            
            success_msg = f"Doctor {first_name} {last_name} has been successfully registered!"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'type': 'success', 'title': 'Success', 'message': success_msg})
            messages.success(request, success_msg)
            return redirect('user_management')
            
        except Exception as e:
            error_msg = f"Error creating doctor: {str(e)}"
            print(f"Error details: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'type': 'error', 'title': 'Error', 'message': error_msg}, status=500)
            messages.error(request, error_msg)
            return redirect('user_management')
    
    return redirect('user_management')


@login_required
def create_midwife(request):
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            middle_name = request.POST.get('middle_name', '')
            phone = request.POST.get('phone')
            email = request.POST.get('email_account') or request.POST.get('email', '')
            # REMOVED: username, password1, password2 - no longer needed
            license_number = request.POST.get('license_number', '')
            prc_license_number = request.POST.get('prc_license_number', '')
            specialization = request.POST.get('specialization', '')
            facility_id = request.POST.get('facility', '')
            street_address = request.POST.get('street_address', '')
            barangay = request.POST.get('barangay', '')
            city = request.POST.get('city', '')
            province = request.POST.get('province', '')
            postal_code = request.POST.get('postal_code', '')
            assigned_area = request.POST.get('assigned_area', '')
            
            # Validate required fields (removed username, password1, password2)
            if not all([first_name, last_name, phone]):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'type': 'error', 'title': 'Error', 'message': 'All required fields must be filled.'}, status=400)
                messages.error(request, "All required fields must be filled.")
                return redirect('user_management')
            
            # Check if email already exists in Midwives (if provided)
            if email and Midwives.objects.filter(email=email).exists():
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'type': 'error', 'title': 'Error', 'message': 'Email already registered to a midwife profile.'}, status=400)
                messages.error(request, "Email already registered to a midwife profile.")
                return redirect('user_management')
            
            # Get facility if provided
            facility = None
            if facility_id:
                try:
                    facility = Facility.objects.get(facility_id=facility_id)
                    if not assigned_area:
                        assigned_area = facility.name
                except Facility.DoesNotExist:
                    pass
            
            # Create Midwife registration WITHOUT User account
            midwife_registration = Midwives.objects.create(
                user=None,  # No user account created
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                phone=phone,
                email=email,
                street_address=street_address,
                barangay=barangay,
                city=city,
                province=province,
                postal_code=postal_code,
                midwife_license_number=license_number,
                prc_license_number=prc_license_number,
                midwifery_specialization=specialization,
                midwifery_assigned_area=assigned_area,
                facility=facility,
                status='APPROVED',  # Auto-approve when created by admin
                approved_by=request.user,
                approved_at=timezone.now(),
            )
            
            success_msg = f"Midwife {first_name} {last_name} has been successfully registered!"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'type': 'success', 'title': 'Success', 'message': success_msg})
            messages.success(request, success_msg)
            return redirect('user_management')
            
        except Exception as e:
            error_msg = f"Error creating midwife: {str(e)}"
            print(f"Error details: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'type': 'error', 'title': 'Error', 'message': error_msg}, status=500)
            messages.error(request, error_msg)
            return redirect('user_management')
    
    return redirect('user_management')


@login_required
def create_bhw(request):
    """Create an ApprovedBHW entry in the whitelist"""
    if request.method == 'POST':
        try:
            from accounts.models import ApprovedBHW
            import re
            
            # Get form data
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            middle_name = request.POST.get('middle_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            email = request.POST.get('email', '').strip()
            accreditation_number = request.POST.get('accreditation_number', '').strip()
            registration_number = request.POST.get('registration_number', '').strip()
            # Removed fields: barangay, notes (using defaults)
            barangay = ''  # Not in form anymore
            notes = ''  # Not in form anymore
            is_active = request.POST.get('is_active') == 'on'  # Checkbox returns 'on' if checked
            
            # Validate required fields
            if not all([first_name, last_name, accreditation_number, registration_number]):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'type': 'error', 'title': 'Error', 'message': 'First Name, Last Name, Registration Number, and Accreditation Number are required.'}, status=400)
                messages.error(request, "First Name, Last Name, Registration Number, and Accreditation Number are required.")
                return redirect('user_management')
            
            # Validate registration and accreditation number format (XX-XXX)
            exact_format_pattern = re.compile(r'^\d{2}-\d{3}$')
            if not exact_format_pattern.match(registration_number):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'type': 'error', 'title': 'Error', 'message': 'Registration Number must be in format XX-XXX (e.g., 32-424).'}, status=400)
                messages.error(request, "Registration Number must be in format XX-XXX (e.g., 32-424).")
                return redirect('user_management')
            
            if not exact_format_pattern.match(accreditation_number):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'type': 'error', 'title': 'Error', 'message': 'Accreditation Number must be in format XX-XXX (e.g., 32-424).'}, status=400)
                messages.error(request, "Accreditation Number must be in format XX-XXX (e.g., 32-424).")
                return redirect('user_management')
            
            # Check if registration number already exists
            if ApprovedBHW.objects.filter(registration_number=registration_number).exists():
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'type': 'error', 'title': 'Error', 'message': 'Registration Number already exists in the whitelist.'}, status=400)
                messages.error(request, "Registration Number already exists in the whitelist.")
                return redirect('user_management')
            
            # Check if accreditation number already exists
            if ApprovedBHW.objects.filter(accreditation_number=accreditation_number).exists():
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'type': 'error', 'title': 'Error', 'message': 'Accreditation Number already exists in the whitelist.'}, status=400)
                messages.error(request, "Accreditation Number already exists in the whitelist.")
                return redirect('user_management')
            
            # Create ApprovedBHW entry
            approved_bhw = ApprovedBHW.objects.create(
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name if middle_name else None,
                phone=phone if phone else '',
                email=email if email else '',
                registration_number=registration_number,
                accreditation_number=accreditation_number,
                barangay=barangay if barangay else '',
                notes=notes if notes else '',
                is_active=is_active,
                created_by=request.user
            )
            
            success_msg = f"BHW {first_name} {last_name} has been successfully added to the whitelist!"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'type': 'success', 'title': 'Success', 'message': success_msg})
            messages.success(request, success_msg)
            return redirect('user_management')
            
        except Exception as e:
            error_msg = f"Error adding BHW to whitelist: {str(e)}"
            print(f"Error details: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'type': 'error', 'title': 'Error', 'message': error_msg}, status=500)
            messages.error(request, error_msg)
            return redirect('user_management')
    
    return redirect('user_management')


def check_username(request):
    """API endpoint to check if username already exists"""
    username = request.GET.get('username', '').strip()
    
    if not username:
        return JsonResponse({'exists': False, 'available': True})
    
    exists = User.objects.filter(username=username).exists()
    
    return JsonResponse({
        'exists': exists,
        'available': not exists
    })

def check_email(request):
    """API endpoint to check if email already exists"""
    email = request.GET.get('email', '').strip()
    
    if not email:
        return JsonResponse({'exists': False, 'available': True})
    
    exists = User.objects.filter(email=email).exists()
    
    return JsonResponse({
        'exists': exists,
        'available': not exists
    })

def check_phone(request):
    """API endpoint to check if phone number already exists"""
    phone = request.GET.get('phone', '').strip()
    
    if not phone:
        return JsonResponse({'exists': False, 'available': True})
    
    # Phone numbers can be reused - no duplicate checking
    return JsonResponse({
        'exists': False,
        'available': True
    })

def check_registration_number(request):
    """API endpoint to check if registration number already exists"""
    registration_number = request.GET.get('registration_number', '').strip()
    
    if not registration_number:
        return JsonResponse({'exists': False, 'available': True})
    
    from accounts.models import BHWRegistration
    
    # Check if registration number exists (exact match)
    exists = BHWRegistration.objects.filter(registrationNumber=registration_number).exists()
    
    return JsonResponse({
        'exists': exists,
        'available': not exists
    })

def check_accreditation_number(request):
    """API endpoint to check if accreditation number already exists"""
    accreditation_number = request.GET.get('accreditation_number', '').strip()
    
    if not accreditation_number:
        return JsonResponse({'exists': False, 'available': True})
    
    from accounts.models import BHWRegistration
    
    # Check if accreditation number exists (exact match)
    exists = BHWRegistration.objects.filter(accreditationNumber=accreditation_number).exists()
    
    return JsonResponse({
        'exists': exists,
        'available': not exists
    })

def register(request):
    """
    User registration view
    Handles registration for BHW and Doctor roles
    """
    
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.POST.get('firstname', '').strip()
            middle_name = request.POST.get('middlename', '').strip()
            last_name = request.POST.get('lastname', '').strip()
            email = request.POST.get('email', '').strip()
            username = request.POST.get('username', '').strip()
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')
            phone = request.POST.get('phone', '').strip()
            main_role = request.POST.get('main_role', '').strip()
            
            # Address fields
            province = request.POST.get('province', 'Davao del Norte').strip()
            municipality = request.POST.get('municipality', 'New Corella').strip()
            barangay_name = request.POST.get('barangay', '').strip()
            purok_name_input = request.POST.get('purok', '').strip()
            assigned_facility_id = request.POST.get('assigned_facility', '')
            assigned_facility_doctor_id = request.POST.get('assigned_facility_doctor', '')
            
            # Doctor-specific fields
            specialization = request.POST.get('specialization', '').strip()
            license_number = request.POST.get('license_number', '').strip()
            
            # BHW-specific fields
            registration_number = request.POST.get('registration_number', '').strip()
            accreditation_number = request.POST.get('accreditation_number', '').strip()
            
            # Check privacy consent
            privacy_consent = request.POST.get('privacy_consent')
            if not privacy_consent:
                messages.error(request, "You must agree to the Data Privacy Terms and Agreement to register.")
                return redirect('register')
            
            # Validation
            if not all([first_name, last_name, email, username, password1, password2, phone, main_role]):
                messages.error(request, "Please fill in all required fields.")
                return redirect('register')
            
            # Role-specific validation
            if main_role == 'BHW':
                # Registration Number and Accreditation Number are now optional
                # No validation required
                pass
            elif main_role == 'DOCTOR':
                if not specialization:
                    messages.error(request, "Specialization is required for doctors.")
                    return redirect('register')
                
                if not license_number:
                    messages.error(request, "PRC License Number is required for doctors.")
                    return redirect('register')
                
                # MHO facility will always be assigned automatically
                
                # No whitelist check - any doctor can register, admin will approve
                # Check if email already exists for a doctor account
                from accounts.models import Doctors
                if Doctors.objects.filter(email__iexact=email).exists():
                    messages.error(request, "This email is already associated with a doctor account.")
                    return redirect('register')
            
            if password1 != password2:
                messages.error(request, "Passwords do not match.")
                return redirect('register')
            
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists. Please choose a different username.")
                return redirect('register')
            
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already registered. Please use a different email.")
                return redirect('register')
            
            # BHW-specific uniqueness validation removed - Registration and Accreditation numbers are optional
            
            if main_role == 'DOCTOR':
                if not specialization:
                    messages.error(request, "Specialization is required for doctors.")
                    return redirect('register')
                
                if Doctors.objects.filter(email__iexact=email).exists():
                    messages.error(request, "This email is already associated with a doctor account.")
                    return redirect('register')
            
            # Create User account
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create UserConsent record
            from .models import UserConsent
            UserConsent.objects.create(
                user=user,
                privacy_policy_accepted=True,
                privacy_policy_accepted_at=timezone.now(),
                data_processing_consent=True,
                data_processing_consent_at=timezone.now(),
                consent_version='1.0'
            )
            
            # Create registration based on role
            if main_role == 'BHW':
                # Get facility if assigned
                facility = None
                if assigned_facility_id:
                    try:
                        facility = Facility.objects.get(facility_id=assigned_facility_id)
                    except Facility.DoesNotExist:
                        pass
                
                # Handle registration certificate image upload
                registration_certificate = None
                if 'profile_picture' in request.FILES:
                    registration_certificate = request.FILES['profile_picture']
                
                # Save registration and accreditation numbers
                # Format: XX-XXX (e.g., 32-424)
                
                # Create BHW registration
                bhw_registration = BHWRegistration.objects.create(
                    user=user,
                    first_name=first_name,
                    middle_name=middle_name if middle_name else '',
                    last_name=last_name,
                    phone=phone,
                    barangay=barangay_name,
                    city=municipality,  # Using municipality as city
                    province=province,
                    bhw_sub_role='BHW',  # Default, can be updated later
                    assigned_barangay=barangay_name,
                    facility=facility,
                    registration_certificate=registration_certificate,
                    registration_number=registration_number if registration_number else None,
                    accreditation_number=accreditation_number if accreditation_number else None,
                    status='PENDING_APPROVAL',
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )
                
                # Also add facility to ManyToMany relationship for easier access
                if facility:
                    facility.users.add(user)
                
                messages.success(request, "BHW registration submitted successfully! Please wait for admin approval.")
                
            elif main_role == 'DOCTOR':
                if not specialization:
                    messages.error(request, "Specialization is required for doctors.")
                    user.delete()  # Clean up created user
                    return redirect('register')
                
                if not license_number:
                    messages.error(request, "PRC License Number is required for doctors.")
                    user.delete()  # Clean up created user
                    return redirect('register')
                
                # Prevent duplicate doctor accounts by email
                if Doctors.objects.filter(user__email=email).exists():
                    messages.error(request, "A doctor account with this email already exists.")
                    user.delete()
                    return redirect('register')
                
                # Get assigned facility from form value (will be "MHO")
                facility = None
                if assigned_facility_doctor_id:
                    # Find facility by name containing the value (e.g., "MHO")
                    facility = Facility.objects.filter(name__icontains=assigned_facility_doctor_id).first()
                
                Doctors.objects.create(
                    user=user,
                    first_name=first_name,
                    middle_name=middle_name if middle_name else '',
                    last_name=last_name,
                    phone=phone,
                    email=email,
                    specialization=specialization,
                    license_number=license_number,
                    street_address=purok_name_input if purok_name_input else '',
                    barangay=barangay_name,
                    city=municipality,
                    province=province,
                    facility=facility,
                    status='PENDING_APPROVAL'
                )
                
                messages.success(request, "Doctor registration submitted successfully! Please wait for admin approval.")
            else:
                messages.error(request, "Invalid role selected.")
                user.delete()  # Clean up created user
                return redirect('register')
            
            # Redirect to login or pending dashboard
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return redirect('register')
    
    # GET request - show registration form
    facilities = Facility.objects.all()
    # Filter MHO facilities for doctors (facilities with "MHO" in name)
    mho_facilities = Facility.objects.filter(name__icontains='MHO').order_by('name')
    return render(request, 'accounts/register.html', {
        'facilities': facilities,
        'mho_facilities': mho_facilities,
    })


@login_required
def approve_user(request):
    """Approve a pending user registration"""
    if request.method == 'POST':
        try:
            user_type = request.POST.get('user_type')
            user_id = request.POST.get('user_id')
            
            if user_type == 'bhw':
                user = BHWRegistration.objects.get(bhw_id=user_id)
            elif user_type == 'doctor':
                user = Doctors.objects.get(doctor_id=user_id)
            elif user_type == 'nurse':
                user = Nurses.objects.get(nurse_id=user_id)
            elif user_type == 'midwife':
                user = Midwives.objects.get(midwife_id=user_id)
            else:
                error_msg = 'Invalid user type'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'type': 'error', 'title': 'Error', 'message': error_msg}, status=400)
                messages.error(request, error_msg)
                return redirect('user_management')
            
            user.status = 'ACTIVE'
            user.approved_by = request.user
            user.approved_at = timezone.now()
            user.save()
            # SMS will be sent automatically via signal (accounts/signals.py) when status changes to ACTIVE
            
            success_msg = f'{user_type.title()} approved successfully!'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'type': 'success', 'title': 'Success', 'message': success_msg})
            messages.success(request, success_msg)
            
        except Exception as e:
            error_msg = f'Error approving user: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'type': 'error', 'title': 'Error', 'message': error_msg}, status=500)
            messages.error(request, error_msg)
    
    return redirect('user_management')


@login_required
def reject_user(request):
    """Reject a pending user registration and delete the User account"""
    if request.method == 'POST':
        try:
            user_type = request.POST.get('user_type')
            user_id = request.POST.get('user_id')
            reason = request.POST.get('reason', 'No reason provided')
            
            registration = None
            user_to_delete = None
            
            if user_type == 'bhw':
                registration = BHWRegistration.objects.get(bhw_id=user_id)
            elif user_type == 'doctor':
                registration = Doctors.objects.get(doctor_id=user_id)
            elif user_type == 'nurse':
                registration = Nurses.objects.get(nurse_id=user_id)
            elif user_type == 'midwife':
                registration = Midwives.objects.get(midwife_id=user_id)
            else:
                error_msg = 'Invalid user type'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'type': 'error', 'title': 'Error', 'message': error_msg}, status=400)
                messages.error(request, error_msg)
                return redirect('user_management')
            
            # Get the associated user before updating status
            if registration.user:
                user_to_delete = registration.user
            
            # Get user details for SMS before deletion
            first_name = registration.first_name
            last_name = registration.last_name
            phone_number = registration.phone if hasattr(registration, 'phone') and registration.phone else None
            
            # Update registration status
            registration.status = 'REJECTED'
            registration.approved_by = request.user
            registration.approved_at = timezone.now()
            registration.rejection_reason = reason
            registration.save()
            
            # Send rejection SMS if phone number is available
            if phone_number:
                try:
                    full_name = f"{first_name} {last_name}".strip()
                    rejection_message = f"We regret to inform you {full_name} that your account registration for MHOERS is rejected by the Admin"
                    send_sms_iprog(
                        phone_number=phone_number,
                        first_name=first_name,
                        last_name=last_name,
                        message=rejection_message,
                        sender_id="MHO-NewCorella"
                    )
                except Exception as sms_error:
                    # Log SMS error but don't fail the rejection process
                    print(f"Error sending rejection SMS: {str(sms_error)}")
            
            # Delete the User account if it exists
            if user_to_delete:
                user_to_delete.delete()
            
            success_msg = f'{user_type.title()} rejected and account deleted.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'type': 'success', 'title': 'Success', 'message': success_msg})
            messages.success(request, success_msg)
            
        except Exception as e:
            error_msg = f'Error rejecting user: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'type': 'error', 'title': 'Error', 'message': error_msg}, status=500)
            messages.error(request, error_msg)
    
    return redirect('user_management')


def user_logout(request):
    logout(request)
    response = redirect('login')
    # Prevent back navigation after logout
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required
@never_cache
def pending_dashboard(request):
    return render(request, 'accounts/pending_dashboard.html', {
        'active_page': 'pending'
    })


@login_required
@never_cache
def update_profile(request):
    """Update user profile information"""
    if request.method == 'POST':
        try:
            user = request.user
            
            # Get form data
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            
            # Validate required fields
            if not all([first_name, last_name, username]):
                messages.error(request, 'First name, last name, and username are required.')
                return redirect('profile')
            
            # Check if username is already taken by another user
            if User.objects.filter(username=username).exclude(pk=user.pk).exists():
                messages.error(request, 'Username is already taken by another user.')
                return redirect('profile')
            
            # Check if email is already taken by another user
            if email and User.objects.filter(email=email).exclude(pk=user.pk).exists():
                messages.error(request, 'Email is already taken by another user.')
                return redirect('profile')
            
            # Update user information
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            if email:
                user.email = email
            user.save()
            
            messages.success(request, 'Profile updated successfully!')
            
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    return redirect('profile')


@login_required
@never_cache
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        try:
            user = request.user
            
            # Get form data
            old_password = request.POST.get('old_password', '')
            new_password1 = request.POST.get('new_password1', '')
            new_password2 = request.POST.get('new_password2', '')
            
            # Validate required fields
            if not all([old_password, new_password1, new_password2]):
                messages.error(request, 'All password fields are required.')
                return redirect('profile')
            
            # Check if old password is correct
            if not user.check_password(old_password):
                messages.error(request, 'Current password is incorrect.')
                return redirect('profile')
            
            # Check if new passwords match
            if new_password1 != new_password2:
                messages.error(request, 'New passwords do not match.')
                return redirect('profile')
            
            # Check password length
            if len(new_password1) < 8:
                messages.error(request, 'New password must be at least 8 characters long.')
                return redirect('profile')
            
            # Update password
            user.set_password(new_password1)
            user.save()
            
            # Update session to prevent logout
            update_session_auth_hash(request, user)
            
            messages.success(request, 'Password changed successfully!')
            
        except Exception as e:
            messages.error(request, f'Error changing password: {str(e)}')
    
    return redirect('profile')


def privacy_policy(request):
    """Display privacy policy page"""
    return render(request, 'accounts/privacy_policy.html', {'active_page': 'privacy_policy'})


@login_required
@never_cache
def manage_consent(request):
    """Manage user consent preferences"""
    from .models import UserConsent
    from .forms import ConsentForm
    from datetime import timedelta
    
    # Get or create consent record
    consent, created = UserConsent.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ConsentForm(request.POST, instance=consent)
        if form.is_valid():
            consent_obj = form.save(commit=False)
            
            # Update timestamps if consent changed
            if consent_obj.privacy_policy_accepted and not consent.privacy_policy_accepted:
                consent_obj.privacy_policy_accepted_at = timezone.now()
            if consent_obj.data_processing_consent and not consent.data_processing_consent:
                consent_obj.data_processing_consent_at = timezone.now()
            
            consent_obj.consent_version = '1.0'  # Update when policy changes
            consent_obj.save()
            
            messages.success(request, 'Consent preferences updated successfully!')
            return redirect('profile')
    else:
        form = ConsentForm(instance=consent)
    
    return render(request, 'accounts/manage_consent.html', {
        'form': form,
        'consent': consent,
        'active_page': 'profile'
    })


@login_required
@never_cache
def request_account_deletion(request):
    """Handle account deletion requests (GDPR Right to be Forgotten)"""
    from .models import AccountDeletionRequest
    from .forms import AccountDeletionRequestForm
    from datetime import timedelta
    
    # Check if user already has a pending deletion request
    existing_request = AccountDeletionRequest.objects.filter(
        user=request.user,
        status__in=['PENDING', 'PROCESSING']
    ).first()
    
    if existing_request:
        messages.warning(request, 'You already have a pending account deletion request.')
        return redirect('profile')
    
    if request.method == 'POST':
        form = AccountDeletionRequestForm(request.POST)
        if form.is_valid():
            # Create deletion request
            deletion_request = AccountDeletionRequest.objects.create(
                user=request.user,
                status='PENDING',
                scheduled_deletion_date=timezone.now() + timedelta(days=30)  # 30-day grace period
            )
            
            # TODO: Send confirmation email to user
            # TODO: Send notification to administrators
            
            messages.success(
                request,
                'Your account deletion request has been received. Your account will be deleted after 30 days. '
                'You can cancel this request from your profile page.'
            )
            return redirect('profile')
    else:
        form = AccountDeletionRequestForm()
    
    return render(request, 'accounts/request_deletion.html', {
        'form': form,
        'active_page': 'profile'
    })


@login_required
@never_cache
def cancel_deletion_request(request):
    """Cancel a pending account deletion request"""
    from .models import AccountDeletionRequest
    
    deletion_request = AccountDeletionRequest.objects.filter(
        user=request.user,
        status__in=['PENDING', 'PROCESSING']
    ).first()
    
    if deletion_request:
        deletion_request.status = 'CANCELLED'
        deletion_request.cancellation_reason = 'Cancelled by user'
        deletion_request.save()
        messages.success(request, 'Account deletion request has been cancelled.')
    else:
        messages.error(request, 'No pending deletion request found.')
    
    return redirect('profile')


@require_http_methods(["GET", "POST"])
def custom_password_reset_request(request):
    """Custom password reset request view - works with Hostinger email"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'accounts/custom_password_reset.html')
        
        try:
            # Find user by email
            user = User.objects.get(email=email)
            
            # Generate reset token
            reset_token = PasswordResetToken.generate_token(user)
            
            # Build reset URL - fix SITE_URL if it has typo
            site_url = getattr(settings, 'SITE_URL', 'https://mhoers-nc.online')
            if not site_url.startswith('http'):
                site_url = 'https://' + site_url.lstrip('https//').lstrip('http//')
            
            reset_url = f"{site_url}/accounts/custom-password-reset-confirm/{reset_token.token}/"
            
            # Get user's full name or username
            user_name = user.get_full_name() or user.username
            
            # Send email with HTML template
            subject = 'Password Reset Request - MHOERS'
            
            # Plain text version
            message = f"""
Hello {user_name},

You're receiving this email because you requested a password reset for your MHOERS account.

Please click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you didn't request a password reset, please ignore this email. Your password will remain unchanged.

This is an automated message from MHOERS. Please do not reply to this email.
            """
            
            # HTML version
            html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .email-container {{
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .content {{
            padding: 30px;
            background: #f8fafc;
        }}
        .content p {{
            margin: 15px 0;
            color: #333;
        }}
        .button-container {{
            text-align: center;
            margin: 30px 0;
        }}
        .button {{
            display: inline-block;
            padding: 14px 28px;
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .button:hover {{
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
        }}
        .link-text {{
            word-break: break-all;
            color: #3b82f6;
            font-size: 12px;
            margin-top: 20px;
            padding: 15px;
            background: #e0e7ff;
            border-radius: 4px;
        }}
        .warning {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            font-size: 12px;
            color: #64748b;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>🔐 Password Reset Request</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{user_name}</strong>,</p>
            <p>You're receiving this email because you requested a password reset for your MHOERS account.</p>
            <p>Please click the button below to reset your password:</p>
            
            <div class="button-container">
                <a href="{reset_url}" class="button">Reset Password</a>
            </div>
            
            <p>Or copy and paste this link into your browser:</p>
            <div class="link-text">{reset_url}</div>
            
            <div class="warning">
                <strong>⚠️ Important:</strong> This link will expire in 24 hours for security reasons.
            </div>
            
            <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
            
            <div class="footer">
                <p>This is an automated message from MHOERS.</p>
                <p>Please do not reply to this email.</p>
            </div>
        </div>
    </div>
</body>
</html>
            """
            
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                messages.success(
                    request,
                    'If an account exists with that email, we\'ve sent you a password reset link. '
                    'Please check your email and click the link to reset your password.'
                )
            except Exception as e:
                # Log error but don't reveal to user (security best practice)
                print(f"Email sending error: {str(e)}")
                messages.success(
                    request,
                    'If an account exists with that email, we\'ve sent you a password reset link. '
                    'Please check your email and click the link to reset your password.'
                )
            
            return redirect('custom_password_reset_done')
            
        except User.DoesNotExist:
            # Don't reveal if email exists or not (security best practice)
            messages.success(
                request,
                'If an account exists with that email, we\'ve sent you a password reset link. '
                'Please check your email and click the link to reset your password.'
            )
            return redirect('custom_password_reset_done')
        except Exception as e:
            print(f"Password reset error: {str(e)}")
            messages.error(request, 'An error occurred. Please try again later.')
            return render(request, 'accounts/custom_password_reset.html')
    
    return render(request, 'accounts/custom_password_reset.html')


@require_http_methods(["GET", "POST"])
def custom_password_reset_confirm(request, token):
    """Custom password reset confirmation view"""
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        
        if not reset_token.is_valid():
            messages.error(request, 'This password reset link has expired or has already been used.')
            return redirect('custom_password_reset')
        
        if request.method == 'POST':
            new_password1 = request.POST.get('new_password1', '').strip()
            new_password2 = request.POST.get('new_password2', '').strip()
            
            if not new_password1 or not new_password2:
                messages.error(request, 'Please fill in both password fields.')
                return render(request, 'accounts/custom_password_reset_confirm.html', {
                    'token': token,
                    'valid_token': True
                })
            
            if new_password1 != new_password2:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'accounts/custom_password_reset_confirm.html', {
                    'token': token,
                    'valid_token': True
                })
            
            if len(new_password1) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'accounts/custom_password_reset_confirm.html', {
                    'token': token,
                    'valid_token': True
                })
            
            # Set new password
            user = reset_token.user
            user.set_password(new_password1)
            user.save()
            
            # Mark token as used
            reset_token.mark_as_used()
            
            messages.success(request, 'Your password has been reset successfully! You can now log in with your new password.')
            return redirect('login')
        
        return render(request, 'accounts/custom_password_reset_confirm.html', {
            'token': token,
            'valid_token': True
        })
        
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid password reset link.')
        return redirect('custom_password_reset')


def custom_password_reset_done(request):
    """Password reset request confirmation page"""
    return render(request, 'accounts/custom_password_reset_done.html')


@login_required
def update_bhw_status(request):
    """Update the status of a BHW registration"""
    if request.method == 'POST':
        try:
            bhw_id = request.POST.get('bhw_id')
            new_status = request.POST.get('status')
            
            if not bhw_id or not new_status:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Missing required fields'}, status=400)
                messages.error(request, 'Missing required fields.')
                return redirect('user_management')
            
            # Validate status choice
            valid_statuses = [choice[0] for choice in BHWRegistration.STATUS_CHOICES]
            if new_status not in valid_statuses:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Invalid status'}, status=400)
                messages.error(request, 'Invalid status.')
                return redirect('user_management')
            
            # Get the BHW registration
            bhw = get_object_or_404(BHWRegistration, bhw_id=bhw_id)
            old_status = bhw.status
            old_status_display = bhw.get_status_display()
            bhw.status = new_status
            
            # Update approved_by and approved_at if status is APPROVED
            if new_status == 'APPROVED' and old_status != 'APPROVED':
                bhw.approved_by = request.user
                bhw.approved_at = timezone.now()
            
            bhw.save()
            
            success_msg = f"Status updated successfully from {old_status_display} to {bhw.get_status_display()}."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': success_msg,
                    'status': new_status,
                    'status_display': bhw.get_status_display()
                })
            messages.success(request, success_msg)
            return redirect('user_management')
            
        except Exception as e:
            error_msg = f"Error updating status: {str(e)}"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg}, status=500)
            messages.error(request, error_msg)
            return redirect('user_management')
    
    return redirect('user_management')


@login_required
def edit_bhw(request, bhw_id):
    """Get or update BHW information"""
    bhw = get_object_or_404(BHWRegistration, bhw_id=bhw_id)
    
    if request.method == 'POST':
        try:
            # Update name fields
            bhw.first_name = request.POST.get('first_name', bhw.first_name)
            bhw.middle_name = request.POST.get('middle_name', bhw.middle_name)
            bhw.last_name = request.POST.get('last_name', bhw.last_name)
            
            # Update professional information
            bhw.accreditationNumber = request.POST.get('accreditation_number', bhw.accreditationNumber)
            bhw.registrationNumber = request.POST.get('registration_number', bhw.registrationNumber)
            
            # Update contact information
            bhw.phone = request.POST.get('phone', bhw.phone)
            
            # Update status if provided
            new_status = request.POST.get('status')
            if new_status and new_status in dict(BHWRegistration.STATUS_CHOICES):
                bhw.status = new_status
            
            bhw.updated_at = timezone.now()
            bhw.save()
            
            success_msg = f"BHW {bhw.first_name} {bhw.last_name} updated successfully!"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': success_msg})
            messages.success(request, success_msg)
            return redirect('user_management')
            
        except Exception as e:
            error_msg = f"Error updating BHW: {str(e)}"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg}, status=500)
            messages.error(request, error_msg)
            return redirect('user_management')
    
    # GET request - return JSON data for editing
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'bhw': {
                'bhw_id': bhw.bhw_id,
                'first_name': bhw.first_name,
                'middle_name': bhw.middle_name or '',
                'last_name': bhw.last_name,
                'accreditation_number': bhw.accreditationNumber,
                'registration_number': bhw.registrationNumber,
                'phone': bhw.phone or '',
                'status': bhw.status,
            }
        })
    
    return redirect('user_management')


@login_required
def edit_approved_bhw(request, approved_bhw_id):
    """Get or update ApprovedBHW information"""
    from accounts.models import ApprovedBHW
    approved_bhw = get_object_or_404(ApprovedBHW, approved_bhw_id=approved_bhw_id)
    
    if request.method == 'POST':
        try:
            # Update name fields
            approved_bhw.first_name = request.POST.get('first_name', approved_bhw.first_name)
            approved_bhw.middle_name = request.POST.get('middle_name', approved_bhw.middle_name)
            approved_bhw.last_name = request.POST.get('last_name', approved_bhw.last_name)
            
            # Update professional information
            approved_bhw.accreditation_number = request.POST.get('accreditation_number', approved_bhw.accreditation_number)
            approved_bhw.registration_number = request.POST.get('registration_number', approved_bhw.registration_number)
            
            # Update contact information
            approved_bhw.phone = request.POST.get('phone', approved_bhw.phone)
            approved_bhw.email = request.POST.get('email', approved_bhw.email)
            approved_bhw.barangay = request.POST.get('barangay', approved_bhw.barangay)
            
            # Update is_active status
            approved_bhw.is_active = request.POST.get('is_active') == 'true'
            
            approved_bhw.save()
            
            success_msg = f"Approved BHW {approved_bhw.first_name} {approved_bhw.last_name} updated successfully!"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': success_msg})
            messages.success(request, success_msg)
            return redirect('user_management')
            
        except Exception as e:
            error_msg = f"Error updating Approved BHW: {str(e)}"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg}, status=500)
            messages.error(request, error_msg)
            return redirect('user_management')
    
    # GET request - return JSON data for editing
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'bhw': {
                'approved_bhw_id': approved_bhw.approved_bhw_id,
                'first_name': approved_bhw.first_name,
                'middle_name': approved_bhw.middle_name or '',
                'last_name': approved_bhw.last_name,
                'accreditation_number': approved_bhw.accreditation_number,
                'registration_number': approved_bhw.registration_number,
                'phone': approved_bhw.phone or '',
                'email': approved_bhw.email or '',
                'barangay': approved_bhw.barangay or '',
                'is_active': approved_bhw.is_active,
            }
        })
    
    return redirect('user_management')


@login_required
def doctor_dashboard(request):
    """Doctor dashboard - same as admin dashboard showing all statistics"""
    from accounts.models import Doctors
    from referrals.models import Referral
    from patients.models import Patient
    from django.db.models import Q, Count
    from django.utils import timezone
    from datetime import datetime, date
    
    # Check if user is a doctor
    try:
        doctor_profile = Doctors.objects.get(user=request.user)
        if doctor_profile.status != 'ACTIVE':
            messages.error(request, "Your account is not active. Please contact administrator.")
            return redirect('home')
    except Doctors.DoesNotExist:
        messages.error(request, "Access denied. This page is for doctors only.")
        return redirect('home')
    
    # Get all notifications for the logged-in user
    from notifications.models import Notification
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    
    # Count unread notifications
    notification_count = notifications.filter(is_read=False).count()
    
    # Get today's date (start and end of day)
    today_start = timezone.make_aware(datetime.combine(date.today(), datetime.min.time()))
    today_end = timezone.make_aware(datetime.combine(date.today(), datetime.max.time()))
    
    # Get statistics from models
    # Doctors see only their accepted referrals in active count
    total_patients = Patient.objects.count()
    
    # Pending Referrals: All pending referrals (all-time)
    pending_count = Referral.objects.filter(status='pending').count()
    
    # Active Referrals: In-progress (only doctor's accepted ones) - all-time
    doctor_active_count = Referral.objects.filter(
        status='in-progress',
        examined_by=request.user
    ).count()
    active_referrals = doctor_active_count
    
    # Today's Completed: Completed today (only doctor's own referrals)
    todays_completed = Referral.objects.filter(
        status='completed',
        examined_by=request.user,
        completed_at__gte=today_start,
        completed_at__lte=today_end
    ).count()
    
    # All Time Record: Total referrals (only doctor's own referrals - all-time)
    total_referrals = Referral.objects.filter(
        examined_by=request.user
    ).count()
    
    return render(request, 'analytics/doctor_dashboard.html', {
        'active_page': 'doctor_dashboard',
        'total_patients': total_patients,
        'pending_count': pending_count,
        'active_referrals': active_referrals,
        'todays_completed': todays_completed,
        'total_referrals': total_referrals,
        'doctor_profile': doctor_profile,
        'notifications': notifications,
        'unread_count': notification_count,
    })


@login_required
def doctor_transactions_report(request):
    """Doctor transactions report showing referrals handled by the doctor with date filters"""
    from accounts.models import Doctors
    from referrals.models import Referral
    from django.utils import timezone
    from datetime import datetime, date, timedelta
    from django.db.models import Q, Count, Sum
    import calendar
    
    # Check if user is a doctor
    try:
        doctor_profile = Doctors.objects.get(user=request.user)
        if doctor_profile.status != 'ACTIVE':
            messages.error(request, "Your account is not active. Please contact administrator.")
            return redirect('home')
    except Doctors.DoesNotExist:
        messages.error(request, "Access denied. This page is for doctors only.")
        return redirect('home')
    
    # Parse date filter parameters
    filter_type = request.GET.get('filter_type', 'all')  # all, day, week, month, year, custom (kept for backward compatibility)
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    year = request.GET.get('year', '')
    month = request.GET.get('month', '')
    week_start = request.GET.get('week_start', '')
    week_end = request.GET.get('week_end', '')
    
    # Base queryset: Only completed referrals examined by this doctor
    referrals_qs = Referral.objects.filter(
        examined_by=request.user,
        status='completed'
    ).select_related('patient', 'patient__facility', 'user').order_by('-created_at')
    
    # Apply date filters
    today = timezone.now().date()
    date_filter_applied = False
    
    # Primary filtering: Use date_from and date_to if provided (new simplified filter)
    if date_from or date_to:
        try:
            if date_from and date_to:
                # Both dates provided - filter by range
                start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                referrals_qs = referrals_qs.filter(
                    created_at__date__gte=start_date,
                    created_at__date__lte=end_date
                )
                date_filter_applied = True
            elif date_from:
                # Only start date provided - filter from that date onwards
                start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                referrals_qs = referrals_qs.filter(
                    created_at__date__gte=start_date
                )
                date_filter_applied = True
            elif date_to:
                # Only end date provided - filter up to that date
                end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                referrals_qs = referrals_qs.filter(
                    created_at__date__lte=end_date
                )
                date_filter_applied = True
        except ValueError:
            pass
    # Legacy filter_type support (for backward compatibility)
    elif filter_type == 'day' and date_from:
        try:
            filter_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            referrals_qs = referrals_qs.filter(
                created_at__date=filter_date
            )
            date_filter_applied = True
        except ValueError:
            pass
    elif filter_type == 'week' and week_start and week_end:
        try:
            start_date = datetime.strptime(week_start, '%Y-%m-%d').date()
            end_date = datetime.strptime(week_end, '%Y-%m-%d').date()
            referrals_qs = referrals_qs.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )
            date_filter_applied = True
        except ValueError:
            pass
    elif filter_type == 'month' and year and month:
        try:
            year_int = int(year)
            month_int = int(month)
            referrals_qs = referrals_qs.filter(
                created_at__year=year_int,
                created_at__month=month_int
            )
            date_filter_applied = True
        except ValueError:
            pass
    elif filter_type == 'year' and year:
        try:
            year_int = int(year)
            referrals_qs = referrals_qs.filter(
                created_at__year=year_int
            )
            date_filter_applied = True
        except ValueError:
            pass
    elif filter_type == 'custom' and date_from and date_to:
        try:
            start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            referrals_qs = referrals_qs.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )
            date_filter_applied = True
        except ValueError:
            pass
    
    # Get statistics (all are completed since we filter by status='completed')
    total_referrals = referrals_qs.count()
    pending_count = 0  # Not applicable since we only show completed
    in_progress_count = 0  # Not applicable since we only show completed
    completed_count = total_referrals  # All referrals shown are completed
    
    # Get referrals list
    referrals_list = list(referrals_qs[:1000])  # Limit to 1000 for performance
    
    # Calculate date range for display
    if referrals_list:
        first_date = referrals_list[-1].created_at.date() if referrals_list else today
        last_date = referrals_list[0].created_at.date() if referrals_list else today
    else:
        first_date = today
        last_date = today
    
    # Get current datetime for report generation timestamp
    now_datetime = timezone.now()
    
    # Get current year and month for dropdowns
    current_year = today.year
    years = list(range(current_year - 5, current_year + 1))
    years.reverse()
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    
    # Get month name if month filter is applied
    month_name = ''
    if filter_type == 'month' and year and month:
        try:
            month_int = int(month)
            month_name = calendar.month_name[month_int]
        except (ValueError, IndexError):
            pass
    
    # Calculate week range (current week)
    current_week_start = today - timedelta(days=today.weekday())
    current_week_end = current_week_start + timedelta(days=6)
    
    # Convert date strings to date objects for template display
    date_from_obj = None
    date_to_obj = None
    week_start_obj = None
    week_end_obj = None
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if week_start:
        try:
            week_start_obj = datetime.strptime(week_start, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if week_end:
        try:
            week_end_obj = datetime.strptime(week_end, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    return render(request, 'analytics/doctor_transactions_report.html', {
        'active_page': 'doctor_transactions_report',
        'doctor_profile': doctor_profile,
        'referrals': referrals_list,
        'total_referrals': total_referrals,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'filter_type': filter_type,
        'date_from': date_from,
        'date_to': date_to,
        'date_from_obj': date_from_obj,
        'date_to_obj': date_to_obj,
        'year': year,
        'month': month,
        'week_start': week_start,
        'week_end': week_end,
        'week_start_obj': week_start_obj,
        'week_end_obj': week_end_obj,
        'date_filter_applied': date_filter_applied,
        'first_date': first_date,
        'last_date': last_date,
        'years': years,
        'months': months,
        'current_week_start': current_week_start,
        'current_week_end': current_week_end,
        'today': today,
        'now_datetime': now_datetime,
        'month_name': month_name,
    })


@login_required
def update_nurse_status(request):
    """Update the status of a Nurse registration"""
    if request.method == 'POST':
        try:
            nurse_id = request.POST.get('nurse_id')
            new_status = request.POST.get('status')
            
            if not nurse_id or not new_status:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Missing required fields'}, status=400)
                messages.error(request, 'Missing required fields.')
                return redirect('user_management')
            
            # Validate status choice
            valid_statuses = [choice[0] for choice in Nurses.STATUS_CHOICES]
            if new_status not in valid_statuses:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Invalid status'}, status=400)
                messages.error(request, 'Invalid status.')
                return redirect('user_management')
            
            # Get the Nurse registration
            nurse = get_object_or_404(Nurses, nurse_id=nurse_id)
            old_status = nurse.status
            old_status_display = nurse.get_status_display()
            nurse.status = new_status
            
            # Update approved_by and approved_at if status is APPROVED
            if new_status == 'APPROVED' and old_status != 'APPROVED':
                nurse.approved_by = request.user
                nurse.approved_at = timezone.now()
            
            nurse.save()
            
            success_msg = f"Status updated successfully from {old_status_display} to {nurse.get_status_display()}."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': success_msg,
                    'status': new_status,
                    'status_display': nurse.get_status_display()
                })
            messages.success(request, success_msg)
            return redirect('user_management')
            
        except Exception as e:
            error_msg = f"Error updating status: {str(e)}"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg}, status=500)
            messages.error(request, error_msg)
            return redirect('user_management')
    
    return redirect('user_management')


@login_required
def edit_nurse(request, nurse_id):
    """Get or update Nurse name information only"""
    nurse = get_object_or_404(Nurses, nurse_id=nurse_id)
    
    if request.method == 'POST':
        try:
            # Update only name fields
            nurse.first_name = request.POST.get('first_name', nurse.first_name)
            nurse.middle_name = request.POST.get('middle_name', nurse.middle_name)
            nurse.last_name = request.POST.get('last_name', nurse.last_name)
            nurse.updated_at = timezone.now()
            nurse.save()
            
            success_msg = f"Nurse {nurse.first_name} {nurse.last_name} updated successfully!"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': success_msg})
            messages.success(request, success_msg)
            return redirect('user_management')
            
        except Exception as e:
            error_msg = f"Error updating nurse: {str(e)}"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg}, status=500)
            messages.error(request, error_msg)
            return redirect('user_management')
    
    # GET request - return JSON data for editing
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'nurse': {
                'nurse_id': nurse.nurse_id,
                'first_name': nurse.first_name,
                'middle_name': nurse.middle_name or '',
                'last_name': nurse.last_name,
                'status': nurse.status,
            }
        })
    
    return redirect('user_management')


@login_required
def update_doctor_status(request):
    """Update the status of a Doctor registration"""
    if request.method == 'POST':
        try:
            doctor_id = request.POST.get('doctor_id')
            new_status = request.POST.get('status')
            
            if not doctor_id or not new_status:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Missing required fields'}, status=400)
                messages.error(request, 'Missing required fields.')
                return redirect('user_management')
            
            # Validate status choice
            valid_statuses = [choice[0] for choice in Doctors.STATUS_CHOICES]
            if new_status not in valid_statuses:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Invalid status'}, status=400)
                messages.error(request, 'Invalid status.')
                return redirect('user_management')
            
            # Get the Doctor registration
            doctor = get_object_or_404(Doctors, doctor_id=doctor_id)
            old_status = doctor.status
            old_status_display = doctor.get_status_display()
            doctor.status = new_status
            
            # Update approved_by and approved_at if status is APPROVED
            if new_status == 'APPROVED' and old_status != 'APPROVED':
                doctor.approved_by = request.user
                doctor.approved_at = timezone.now()
            
            doctor.save()
            
            success_msg = f"Status updated successfully from {old_status_display} to {doctor.get_status_display()}."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': success_msg,
                    'status': new_status,
                    'status_display': doctor.get_status_display()
                })
            messages.success(request, success_msg)
            return redirect('user_management')
            
        except Exception as e:
            error_msg = f"Error updating status: {str(e)}"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg}, status=500)
            messages.error(request, error_msg)
            return redirect('user_management')
    
    return redirect('user_management')


@login_required
def edit_doctor(request, doctor_id):
    """Get or update Doctor name information only"""
    doctor = get_object_or_404(Doctors, doctor_id=doctor_id)
    
    if request.method == 'POST':
        try:
            # Update only name fields
            doctor.first_name = request.POST.get('first_name', doctor.first_name)
            doctor.middle_name = request.POST.get('middle_name', doctor.middle_name)
            doctor.last_name = request.POST.get('last_name', doctor.last_name)
            doctor.updated_at = timezone.now()
            doctor.save()
            
            success_msg = f"Doctor {doctor.first_name} {doctor.last_name} updated successfully!"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': success_msg})
            messages.success(request, success_msg)
            return redirect('user_management')
            
        except Exception as e:
            error_msg = f"Error updating doctor: {str(e)}"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg}, status=500)
            messages.error(request, error_msg)
            return redirect('user_management')
    
    # GET request - return JSON data for editing
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'doctor': {
                'doctor_id': doctor.doctor_id,
                'first_name': doctor.first_name,
                'middle_name': doctor.middle_name or '',
                'last_name': doctor.last_name,
                'status': doctor.status,
            }
        })
    
    return redirect('user_management')