from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.models import Group, User
from django.http import HttpResponse, JsonResponse
from notifications.models import Notification
from patients.models import Medical_History, Patient
from referrals.models import Referral
from facilities.models import Facility
from django.core import serializers
from collections import Counter
from datetime import datetime
from django.utils import timezone
from accounts.models import BHWRegistration, Nurses, Doctors
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
 
@login_required
@never_cache
def profile(request):
    """
    Render the user profile page with:
    - total/pending/in-progress/completed referrals (shared per facility)
    - assigned facility info
    - recent referral activities
    """
    # Get the facility (or facilities) that this user is assigned to
    facilities = request.user.shared_facilities.all()

    # Just in case a user belongs to multiple facilities
    facility = facilities.first() if facilities.exists() else None

    # Get referrals for all facilities the user belongs to
    user_referrals = Referral.objects.filter(facility__in=facilities)

    # Referral stats shared within facility
    total_referrals = user_referrals.count()
    pending_referrals = user_referrals.filter(status='pending').count()
    active_referrals = user_referrals.filter(status='in-progress').count()
    completed_referrals = user_referrals.filter(status='completed').count()

    # Recent 10 referrals for this facility
    recent_referrals = (
        user_referrals.select_related('patient', 'facility')
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

        recent_activities.append({
            'type': activity_type,
            'icon': activity_icon,
            'patient': patient_name,
            'status': r.status,
            'badge_class': badge_class,
            'created_at': r.created_at,
            'facility': r.facility.name if r.facility else "No Facility",
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
    user = request.user
    notifications = Notification.objects.filter(recipient=user).order_by('-created_at')

    # Get facility for this user (if applicable)
    facility = Facility.objects.filter(users=user).first()

    # Get medical history
    history_data = Medical_History.objects.filter(user_id=user)
    history_json = serializers.serialize('json', history_data)

    # Referral and patient stats
    if facility:
        total_patients = Patient.objects.filter(facility=facility).count()
        pending_referrals = Referral.objects.filter(facility=facility, status='pending').count()
        active_referrals = Referral.objects.filter(facility=facility, status='in-progress').count()
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
    active_tab = request.GET.get('active_tab', 'tab1')
    facilities = Facility.objects.all()
    
    # Get approved users
    bhwnames = BHWRegistration.objects.filter(status='APPROVED')
    doctors = Doctors.objects.filter(status='APPROVED')
    nurses = Nurses.objects.filter(status='APPROVED')
    
    # Get pending users
    pending_bhw = BHWRegistration.objects.filter(status='PENDING_APPROVAL')
    pending_doctors = Doctors.objects.filter(status='PENDING_APPROVAL')
    pending_nurses = Nurses.objects.filter(status='PENDING_APPROVAL')

    return render(request, 'accounts/user_management.html', {
        'active_page': 'user_management', 
        'facilities': facilities,
        'active_tab': active_tab,
        'bhwnames': bhwnames,
        'doctors': doctors,
        'nurses': nurses,
        'pending_bhw': pending_bhw,
        'pending_doctors': pending_doctors,
        'pending_nurses': pending_nurses,
    })

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user:
            # Check if user's registration is approved or pending
            is_approved = False
            is_pending = False
            
            # Check BHW status
            try:
                bhw_profile = BHWRegistration.objects.get(user=user)
                if bhw_profile.status == 'APPROVED':
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
                if doctor_profile.status == 'APPROVED':
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
            
            # If user has no profile or is approved, allow full login
            if is_approved or not any([BHWRegistration.objects.filter(user=user).exists(), 
                                     Doctors.objects.filter(user=user).exists(), 
                                     Nurses.objects.filter(user=user).exists()]):
                login(request, user)
                return redirect('admin_dashboard' if user.is_staff else 'home')
            
            # If pending, allow login but redirect to pending dashboard
            if is_pending:
                login(request, user)
                return redirect('pending_dashboard')
            
            # Fallback: block if neither approved nor pending
            messages.error(request, 'Your account is not approved yet.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')

    # Make sure GET request renders login.html
    return render(request, 'accounts/login.html')

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
            
            # Debug: Print form data
            print(f"Form data received:")
            print(f"First name: {first_name}")
            print(f"Last name: {last_name}")
            print(f"Email: {email}")
            print(f"Phone: {phone}")
            print(f"Specialization: {specialization}")
            print(f"License: {license_number}")
            
            # Validate required fields
            if not all([first_name, last_name, email, phone, specialization, license_number]):
                messages.error(request, "All required fields must be filled.")
                return redirect('user_management')
                  
            
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already registered.")
                return redirect('user_management')
            
            
            # Create doctor profile
            doctor = Doctors.objects.create(
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                email=email,
                phone=phone,
                specialization=specialization,
                license_number=license_number
            )
            
            # Add user to doctors group if it exists
            try:
                doctors_group = Group.objects.get(name='Doctors')
            except Group.DoesNotExist:
                # Create doctors group if it doesn't exist
                doctors_group = Group.objects.create(name='Doctors')
            
            messages.success(request, f"Doctor {first_name} {last_name} has been successfully registered!")
            return redirect('user_management')
            
        except Exception as e:
            messages.error(request, f"Error creating doctor: {str(e)}")
            print(f"Error details: {str(e)}")
            return redirect('user_management')
    
    return redirect('user_management')


def register(request):
    if request.method == 'POST':
        # Get basic user information
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        created_at = timezone.now()
        
        # Get personal information
        first_name = request.POST.get('firstname', '')
        last_name = request.POST.get('lastname', '')
        middlename = request.POST.get('middlename', '')
        phone = request.POST.get('phone', '')
        
        # Get role information
        main_role = request.POST.get('main_role', '')
        bhw_sub_role = request.POST.get('bhw_sub_role', '')
        mho_sub_role = request.POST.get('mho_sub_role', '')
        
        # Validate required selections
        if not main_role:
            messages.error(request, "Please select a role.")
            return redirect('register')
        
        # Get address information
        street_address = request.POST.get('street_address', '')
        city = request.POST.get('city', '')
        barangay = request.POST.get('barangay', '')
        province = request.POST.get('province', '')
        postal_code = request.POST.get('postal_code', '')

        # Validate passwords
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('register')

        try:
            # Create User account with hashed password
            user = User.objects.create_user(
                username=username,
                password=password1,
                first_name=first_name,
                last_name=last_name,
            )
            
            # Determine the final role and create appropriate profile
            if main_role == 'BHW':
                if bhw_sub_role == 'BHW':
                    # Create BHW profile linked to user
                    # Get the selected facility
                    facility_id = request.POST.get('bhw_assigned_barangay', '')
                    facility = None
                    if facility_id:
                        try:
                            facility = Facility.objects.get(facility_id=facility_id)
                        except Facility.DoesNotExist:
                            pass
                    
                    bhw_profile = BHWRegistration.objects.create(
                        user=user,
                        first_name=first_name,
                        last_name=last_name,
                        middle_name=middlename,
                        phone=phone,
                        street_address=street_address,
                        city=city,
                        barangay=barangay,
                        province=province,
                        postal_code=postal_code,
                        bhw_sub_role=bhw_sub_role,
                        registrationNumber=request.POST.get('registration_number', ''),
                        accreditationNumber=request.POST.get('accreditation_number', ''),
                        assigned_barangay=facility.name if facility else '',
                        facility=facility,
                        status='PENDING_APPROVAL',
                        created_at = created_at
                    )
                    # Add to BHW group
                    group = Group.objects.get(name='BHW')
                    user.groups.add(group)
                    
                    # Add user to facility
                    if facility:
                        facility.users.add(user)
                    
                    
                elif bhw_sub_role == 'BHW_NURSE':
                    # Get the selected facility
                    facility_id = request.POST.get('nurse_assigned_barangay', '')
                    facility = None
                    if facility_id:
                        try:
                            facility = Facility.objects.get(facility_id=facility_id)
                        except Facility.DoesNotExist:
                            pass
                    
                    # Create Nurse profile for BHW Nurse linked to user
                    nurse_profile = Nurses.objects.create(
                        user=user,
                        first_name=first_name,
                        last_name=last_name,
                        middle_name=middlename,
                        phone=phone,
                        email=request.POST.get('email', ''),
                        street_address=street_address,
                        city=city,
                        barangay=barangay,
                        province=province,
                        postal_code=postal_code,
                        nurse_license_number=request.POST.get('nurse_license_number', ''),
                        prc_license_number=request.POST.get('prc_license_number', ''),
                        nursing_school=request.POST.get('nursing_school', ''),
                        nursing_graduation_year=request.POST.get('nursing_graduation_year') or None,
                        nursing_specialization=request.POST.get('nursing_specialization', ''),
                        nursing_affiliation=request.POST.get('nursing_affiliation', ''),
                        nursing_experience_years=request.POST.get('nursing_experience_years') or None,
                        nursing_certification=request.POST.get('nursing_certification', ''),
                        nursing_assigned_area=facility.name if facility else '',
                        facility=facility,
                        status='PENDING_APPROVAL'
                    )
                    # Add to Nurses group
                    group = Group.objects.get(name='Nurses')
                    user.groups.add(group)
                    
                    # Add user to facility
                    if facility:
                        facility.users.add(user)
                    
            elif main_role == 'MHO':
                if mho_sub_role == 'MHO_DOCTOR':
                    # Get the selected facility
                    facility_id = request.POST.get('doctor_assigned_barangay', '')
                    facility = None
                    if facility_id:
                        try:
                            facility = Facility.objects.get(facility_id=facility_id)
                        except Facility.DoesNotExist:
                            pass
                    
                    # Create Doctor profile for MHO Doctor linked to user
                    doctor_profile = Doctors.objects.create(
                        user=user,
                        first_name=first_name,
                        last_name=last_name,
                        middle_name=middlename,
                        email=request.POST.get('email', ''),
                        phone=phone,
                        specialization=request.POST.get('medical_specialization', ''),
                        license_number=request.POST.get('doctor_license_number', ''),
                        street_address=street_address,
                        city=city,
                        barangay=barangay,
                        province=province,
                        postal_code=postal_code,
                        mho_sub_role=mho_sub_role,
                        medical_school=request.POST.get('medical_school', ''),
                        medical_graduation_year=request.POST.get('medical_graduation_year') or None,
                        hospital_affiliation=request.POST.get('hospital_affiliation', ''),
                        years_medical_practice=request.POST.get('years_medical_practice') or None,
                        medical_board_certification=request.POST.get('medical_board_certification', ''),
                        medical_assigned_area=facility.name if facility else '',
                        facility=facility,
                        status='PENDING_APPROVAL'
                    )
                    # Add to Doctors group
                    group = Group.objects.get(name='Doctors')
                    user.groups.add(group)
                    
                    # Add user to facility
                    if facility:
                        facility.users.add(user)
                    
                elif mho_sub_role == 'MHO_NURSE':
                    # Get the selected facility
                    facility_id = request.POST.get('nurse_assigned_barangay', '')
                    facility = None
                    if facility_id:
                        try:
                            facility = Facility.objects.get(facility_id=facility_id)
                        except Facility.DoesNotExist:
                            pass
                    
                    # Create Nurse profile for MHO Nurse linked to user
                    nurse_profile = Nurses.objects.create(
                        user=user,
                        first_name=first_name,
                        last_name=last_name,
                        middle_name=middlename,
                        phone=phone,
                        email=request.POST.get('email', ''),
                        street_address=street_address,
                        city=city,
                        barangay=barangay,
                        province=province,
                        postal_code=postal_code,
                        nurse_license_number=request.POST.get('mho_registration_number', ''),
                        prc_license_number=request.POST.get('mho_accreditation_number', ''),
                        nursing_school=request.POST.get('medical_school', ''),
                        nursing_graduation_year=request.POST.get('graduation_year') or None,
                        nursing_specialization=request.POST.get('specialization', ''),
                        nursing_affiliation=request.POST.get('hospital_affiliation', ''),
                        nursing_experience_years=request.POST.get('years_practice') or None,
                        nursing_certification=request.POST.get('nursing_certification', ''),
                        nursing_assigned_area=facility.name if facility else '',
                        facility=facility,
                        status='PENDING_APPROVAL'
                    )
                    # Add to Nurses group
                    group = Group.objects.get(name='Nurses')
                    user.groups.add(group)
                    
                    # Add user to facility
                    if facility:
                        facility.users.add(user)

            # Don't auto-login, show pending approval message
            messages.success(request, "Registration submitted successfully! Your account is pending MHO approval. You'll receive an email once reviewed.")
            return redirect('login')

        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return redirect('register')

    # Get all facilities for the dropdown
    facilities = Facility.objects.all()
    return render(request, 'accounts/register.html', {'facilities': facilities})


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
            else:
                messages.error(request, 'Invalid user type')
                return redirect('user_management')
            
            user.status = 'APPROVED'
            user.approved_by = request.user
            user.approved_at = timezone.now()
            user.save()
            
            messages.success(request, f'{user_type.title()} approved successfully!')
            
        except Exception as e:
            messages.error(request, f'Error approving user: {str(e)}')
    
    return redirect('user_management')


@login_required
def reject_user(request):
    """Reject a pending user registration"""
    if request.method == 'POST':
        try:
            user_type = request.POST.get('user_type')
            user_id = request.POST.get('user_id')
            reason = request.POST.get('reason', 'No reason provided')
            
            if user_type == 'bhw':
                user = BHWRegistration.objects.get(bhw_id=user_id)
            elif user_type == 'doctor':
                user = Doctors.objects.get(doctor_id=user_id)
            elif user_type == 'nurse':
                user = Nurses.objects.get(nurse_id=user_id)
            else:
                messages.error(request, 'Invalid user type')
                return redirect('user_management')
            
            user.status = 'REJECTED'
            user.approved_by = request.user
            user.approved_at = timezone.now()
            user.rejection_reason = reason
            user.save()
            
            messages.success(request, f'{user_type.title()} rejected.')
            
        except Exception as e:
            messages.error(request, f'Error rejecting user: {str(e)}')
    
    return redirect('user_management')


def user_logout(request):
    return redirect('login')


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