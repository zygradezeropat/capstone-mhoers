from django.shortcuts import render
from django.http import JsonResponse
from analytics.models import Disease
from patients.models import Medical_History, Patient
from referrals.models import Referral, FollowUpVisit
from facilities.models import Facility
from accounts.models import BHWRegistration, Doctors
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from django.db.models import Count, Q, Avg, DurationField, ExpressionWrapper, F
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import calendar
from .models import *
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from analytics.ml_utils import predict_disease_peak_for_month, train_barangay_disease_peak_model, predict_barangay_disease_peak_2025


SINGAPORE_TZ = ZoneInfo('Asia/Singapore')


def now_in_singapore():
    return timezone.now().astimezone(SINGAPORE_TZ)


def is_doctor_user(user):
    """Check if user is an active doctor"""
    try:
        doctor_profile = Doctors.objects.get(user=user)
        return doctor_profile.status == 'ACTIVE'
    except Doctors.DoesNotExist:
        return False


def get_user_facilities(user, user_id=None):
    """
    Get facilities accessible to a user, handling both regular users and BHW users.
    For BHW users, gets facility from BHWRegistration model.
    For staff/superuser, returns all facilities or filters by user_id if provided.
    """
    if user.is_staff or user.is_superuser:
        # If user_id is provided, filter facilities to those associated with that user
        if user_id:
            # Check if the target user is a BHW
            try:
                bhw_profile = BHWRegistration.objects.select_related('facility').get(user_id=user_id)
                if bhw_profile.facility:
                    return Facility.objects.filter(pk=bhw_profile.facility.pk).order_by('name')
            except BHWRegistration.DoesNotExist:
                pass
            # Otherwise, check regular user facilities
            return Facility.objects.filter(users__id=user_id).distinct().order_by('name')
        else:
            return Facility.objects.all().order_by('name')
    else:
        # For non-staff users, check if they are BHW
        try:
            bhw_profile = BHWRegistration.objects.select_related('facility').get(user=user)
            if bhw_profile.facility:
                return Facility.objects.filter(pk=bhw_profile.facility.pk).order_by('name')
        except BHWRegistration.DoesNotExist:
            pass
        
        # If not BHW, check shared_facilities or users relationship
        if hasattr(user, 'shared_facilities'):
            facilities = user.shared_facilities.all()
            if facilities.exists():
                return facilities.order_by('name')
        
        # Fallback to users relationship
        return Facility.objects.filter(users=user).order_by('name')

def get_disease_diagnosis_counts(request):
    """
    API endpoint to return disease diagnosis counts for charting.
    - Shows only the 5 capstone diseases: Open Wounds, Dog Bites, Acute respiratory infections, Pneumonia, Hypertension Level 2
    - All other diseases are grouped as 'Others'
    - All comparisons are case-insensitive
    """
    
    # Define the 5 capstone diseases
    CAPSTONE_DISEASES = {
        'open wounds': 'Open Wounds (T14.1)',
        't14.1': 'Open Wounds (T14.1)',
        'dog bites': 'Dog Bites (W54.99)',
        'w54.99': 'Dog Bites (W54.99)',
        'dog bite': 'Dog Bites (W54.99)',
        'cat bite': 'Dog Bites (W54.99)',  # Also map cat bites to dog bites
        'acute respiratory infections': 'Acute respiratory infections (J06.9)',
        'j06.9': 'Acute respiratory infections (J06.9)',
        'respiratory infection': 'Acute respiratory infections (J06.9)',
        'pneumonia': 'Pneumonia (J15)',
        'j15': 'Pneumonia (J15)',
        'hypertension level 2': 'Hypertension Level 2 (I10-1)',
        'i10-1': 'Hypertension Level 2 (I10-1)',
        'i10.1': 'Hypertension Level 2 (I10-1)',
        'hypertension': 'Hypertension Level 2 (I10-1)',
    }
    
    # Disease display names in order
    DISEASE_ORDER = [
        'Open Wounds (T14.1)',
        'Dog Bites (W54.99)',
        'Acute respiratory infections (J06.9)',
        'Pneumonia (J15)',
        'Hypertension Level 2 (I10-1)',
    ]
    
    year = request.GET.get('year')
    month = request.GET.get('month')
    illness_qs = Medical_History.objects.all()
    if year:
        illness_qs = illness_qs.filter(diagnosed_date__year=year)
    if month:
        illness_qs = illness_qs.filter(diagnosed_date__month=month)
    
    # Get all illness_name counts
    illness_names = list(illness_qs.values_list('illness_name', flat=True))
    
    # Initialize counts for the 5 diseases
    data = {disease: 0 for disease in DISEASE_ORDER}
    others_count = 0
    
    # Count illnesses and map to capstone diseases
    for name in illness_names:
        if not name:
            others_count += 1
            continue
        
        name_lower = name.strip().lower()
        matched = False
        
        # Check if illness name matches any capstone disease
        # Priority: Check ICD codes first, then disease names
        for key, disease_label in CAPSTONE_DISEASES.items():
            # For ICD codes, check for exact match or code in the name
            if key in ['t14.1', 'w54.99', 'j06.9', 'j15', 'i10-1', 'i10.1']:
                if key in name_lower:
                    data[disease_label] += 1
                    matched = True
                    break
            # For disease names, check if key is contained in the illness name
            elif key in name_lower:
                data[disease_label] += 1
                matched = True
                break
        
        if not matched:
            others_count += 1
    
    # Add Others if there's any count
    if others_count > 0:
        data['Others'] = others_count
    else:
        data['Others'] = 0

    # Prepare response in the specified order
    labels = DISEASE_ORDER + ['Others']
    counts = [data.get(label, 0) for label in labels]
    
    return JsonResponse({
        'labels': labels,
        'counts': counts
    })

def get_monthly_diagnosis_trends(request):
    """
    API endpoint to return monthly diagnosis trends for each disease.
    Returns a dict with:
      - months: list of YYYY-MM (always Jan to Dec of current year)
      - diseases: list of disease names (5 capstone diseases + Others)
      - data: {disease_name: [count_per_month, ...]}
    """
    # Define the 5 capstone diseases
    CAPSTONE_DISEASES = {
        'open wounds': 'Open Wounds (T14.1)',
        't14.1': 'Open Wounds (T14.1)',
        'dog bites': 'Dog Bites (W54.99)',
        'w54.99': 'Dog Bites (W54.99)',
        'dog bite': 'Dog Bites (W54.99)',
        'cat bite': 'Dog Bites (W54.99)',  # Also map cat bites to dog bites
        'acute respiratory infections': 'Acute respiratory infections (J06.9)',
        'j06.9': 'Acute respiratory infections (J06.9)',
        'respiratory infection': 'Acute respiratory infections (J06.9)',
        'pneumonia': 'Pneumonia (J15)',
        'j15': 'Pneumonia (J15)',
        'hypertension level 2': 'Hypertension Level 2 (I10-1)',
        'i10-1': 'Hypertension Level 2 (I10-1)',
        'i10.1': 'Hypertension Level 2 (I10-1)',
        'hypertension': 'Hypertension Level 2 (I10-1)',
    }
    
    # Disease display names in order
    DISEASE_ORDER = [
        'Open Wounds (T14.1)',
        'Dog Bites (W54.99)',
        'Acute respiratory infections (J06.9)',
        'Pneumonia (J15)',
        'Hypertension Level 2 (I10-1)',
    ]
    
    year = request.GET.get('year')
    month = request.GET.get('month')
    now = datetime.now()
    year = int(year) if year else now.year
    if month:
        months = [f"{year}-{'%02d' % int(month)}"]
    else:
        months = [f"{year}-{'%02d' % m}" for m in range(1, 13)]
    
    illness_records = Medical_History.objects.all()
    illness_records = illness_records.filter(diagnosed_date__year=year)
    if month:
        illness_records = illness_records.filter(diagnosed_date__month=month)
    illness_records = illness_records.values_list('illness_name', 'diagnosed_date')

    # Initialize data structure for the 5 diseases + Others
    data = {disease: [0] * len(months) for disease in DISEASE_ORDER}
    others_data = [0] * len(months)
    
    # Process each illness record
    for illness, date in illness_records:
        if not illness or not date:
            continue
        
        # Get month string
        month_str = date.strftime("%Y-%m")
        if month_str not in months:
            continue
        
        month_idx = months.index(month_str)
        illness_lc = illness.strip().lower()
        matched = False
        
        # Check if illness name matches any capstone disease
        # Priority: Check ICD codes first, then disease names
        for key, disease_label in CAPSTONE_DISEASES.items():
            # For ICD codes, check for exact match or code in the name
            if key in ['t14.1', 'w54.99', 'j06.9', 'j15', 'i10-1', 'i10.1']:
                if key in illness_lc:
                    data[disease_label][month_idx] += 1
                    matched = True
                    break
            # For disease names, check if key is contained in the illness name
            elif key in illness_lc:
                data[disease_label][month_idx] += 1
                matched = True
                break
        
        if not matched:
            others_data[month_idx] += 1
    
    # Add Others to data
    data['Others'] = others_data

    return JsonResponse({
        'months': months,
        'diseases': DISEASE_ORDER + ['Others'],
        'data': data
    })


@login_required
def medical_certificate_report(request):
    """
    Render the medical certificate template for printing/preview.
    This view returns the standalone `medical_certificate.html` template.
    It can be extended later to accept parameters (patient, date, diagnosis).
    """
    referral_id = request.GET.get('referral_id') or request.GET.get('referral')
    context = {}
    if referral_id:
        try:
            # referral_id in Referral is an AutoField primary key named referral_id
            referral = Referral.objects.select_related('patient', 'examined_by', 'disease').get(referral_id=referral_id)
            patient = referral.patient
            doctors = Doctors.objects.filter(user=referral.examined_by).first()

            patient_name = ' '.join(filter(None, [patient.first_name, patient.middle_name or '', patient.last_name]))
            diagnosis = referral.final_diagnosis or referral.initial_diagnosis or (referral.disease.name if referral.disease else '')
            certificate_date = referral.created_at.strftime('%B %d, %Y') if referral.created_at else ''

            context.update({
                'referral_id': referral.referral_id,
                'patient_name': patient_name,
                'patient_age': getattr(patient, 'age', ''),
                'patient_address': patient.p_address or '',
                'diagnosis': diagnosis or '',
                'certificate_date': certificate_date,
                'examined_by': referral.examined_by.get_full_name() if referral.examined_by else '',
                'examined_title': 'M.D',
                'remarks': referral.remarks or '',
                'treatments': referral.treatments or '',
                'followup_date': referral.followup_date,
                'referral_type': referral.referral_type or '',
            })
        except Referral.DoesNotExist:
            context['error'] = f"Referral with id {referral_id} not found."

    return render(request, 'analytics/medical_certificate.html', context)


def get_disease_counts_per_user(request):
    """Return counts of each disease grouped by user/facility for chart legends.

    Response shape:
    {
      users: ["New Corella", "Carcor", ...],
      diseases: ["Rabies", "Flu", ...],
      matrix: [[12, 0, ...], [2, 1, ...], ...]  // rows per user, cols per disease
    }
    """
    year = request.GET.get('year')
    month = request.GET.get('month')
    qs = Medical_History.objects.all()
    if year:
        qs = qs.filter(diagnosed_date__year=year)
    if month:
        qs = qs.filter(diagnosed_date__month=month)

    disease_names = list(Disease.objects.values_list('name', flat=True))
    disease_name_map = {name.lower(): name for name in disease_names}

    # Users displayed as their username; if facility exists tie by patient.facility.name when possible
    user_ids = list(qs.values_list('user_id', flat=True).distinct())
    users = list(User.objects.filter(id__in=user_ids).values_list('username', flat=True))

    # Build index maps
    disease_to_idx = {name: idx for idx, name in enumerate(disease_names)}
    user_to_idx = {name: idx for idx, name in enumerate(users)}

    # Initialize matrix
    matrix = [[0 for _ in disease_names] for _ in users]

    for illness, user in qs.values_list('illness_name', 'user_id__username'):
        if not illness or not user or user not in user_to_idx:
            continue
        name_lc = illness.strip().lower()
        if name_lc in ["cat bite", "dog bite"]:
            name_lc = "possible rabies"
        elif name_lc == "lbm":
            name_lc = "gastrointestinal issue"
        disease_label = disease_name_map.get(name_lc)
        if not disease_label:
            continue
        r = user_to_idx[user]
        c = disease_to_idx[disease_label]
        matrix[r][c] += 1

    return JsonResponse({
        'users': users,
        'diseases': disease_names,
        'matrix': matrix,
    })

def get_referral_statistics(request):
    """
    API endpoint to return referral statistics for the current user's facilities.
    Returns monthly and yearly referral data.
    For non-staff users, returns only their own referrals from their assigned facilities.
    Supports date filtering via date_from and date_to parameters.
    """
    year = int(request.GET.get('year', datetime.now().year))    
    view_type = request.GET.get('view_type', 'monthly')
    
    # Get date filters
    date_from_str = request.GET.get('date_from', '')
    date_to_str = request.GET.get('date_to', '')
    date_from = None
    date_to = None
    
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    if request.user.is_staff or request.user.is_superuser:
        # Staff/admin: get all facilities
        facilities = Facility.objects.all()
        # Get referrals from all facilities
        referrals_qs = Referral.objects.all()
    else:
        # Non-staff users: get their assigned facilities
        facilities = request.user.shared_facilities.all()
        # Get only referrals created by this user or from their assigned facilities
        from django.db.models import Q
        referrals_qs = Referral.objects.filter(
            Q(user=request.user) | 
            Q(facility__in=facilities) | 
            Q(patient__facility__in=facilities)
        )

    if view_type == 'monthly':
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        # For non-staff users, show a single dataset with their referrals
        if not request.user.is_staff and not request.user.is_superuser:
            user_data = []
            for month_num in range(1, 13):
                month_filter = referrals_qs.filter(
                    created_at__year=year,
                    created_at__month=month_num,
                )
                
                # Apply date range filter if provided
                if date_from and date_to:
                    # Check if this month falls within the date range
                    month_start = datetime(year, month_num, 1).date()
                    # Get last day of month
                    last_day = calendar.monthrange(year, month_num)[1]
                    month_end = datetime(year, month_num, last_day).date()
                    
                    # Only include month if it overlaps with date range
                    if month_end >= date_from and month_start <= date_to:
                        month_filter = month_filter.filter(
                            created_at__date__gte=date_from,
                            created_at__date__lte=date_to
                        )
                    else:
                        # Month doesn't overlap with date range, set count to 0
                        user_data.append(0)
                        continue
                elif date_from:
                    month_filter = month_filter.filter(created_at__date__gte=date_from)
                elif date_to:
                    month_filter = month_filter.filter(created_at__date__lte=date_to)
                
                count = month_filter.count()
                user_data.append(count)
            
            return JsonResponse({
                'labels': months,
                'datasets': [
                    {
                        'label': 'My Referrals',
                        'data': user_data,
                        'backgroundColor': '#4e73df',
                        'borderColor': '#4e73df',
                        'borderRadius': 10,
                        'barThickness': 20,
                    }
                ]
            })
        else:
            # Staff/admin: show data by facility
            data = {}
            for facility in facilities:
                facility_data = []
                for month_num in range(1, 13):
                    month_filter = Referral.objects.filter(
                        patient__facility=facility,
                        created_at__year=year,
                        created_at__month=month_num,
                    )
                    
                    # Apply date range filter if provided
                    if date_from and date_to:
                        # Check if this month falls within the date range
                        month_start = datetime(year, month_num, 1).date()
                        # Get last day of month
                        last_day = calendar.monthrange(year, month_num)[1]
                        month_end = datetime(year, month_num, last_day).date()
                        
                        # Only include month if it overlaps with date range
                        if month_end >= date_from and month_start <= date_to:
                            month_filter = month_filter.filter(
                                created_at__date__gte=date_from,
                                created_at__date__lte=date_to
                            )
                        else:
                            # Month doesn't overlap with date range, set count to 0
                            facility_data.append(0)
                            continue
                    elif date_from:
                        month_filter = month_filter.filter(created_at__date__gte=date_from)
                    elif date_to:
                        month_filter = month_filter.filter(created_at__date__lte=date_to)
                    
                    count = month_filter.count()
                    facility_data.append(count)
                data[facility.name] = facility_data

            return JsonResponse({
                'labels': months,
                'datasets': [
                    {
                        'label': facility_name,
                        'data': facility_data,
                        'backgroundColor': f'#{hash(facility_name) % 0xFFFFFF:06x}',
                        'borderRadius': 10,
                        'barThickness': 20,
                    }
                    for facility_name, facility_data in data.items()
                ]
            })

    else:  # yearly
        years = [year - 3, year - 2, year - 1, year]
        year_labels = [str(y) for y in years]

        # For non-staff users, show a single dataset with their referrals
        if not request.user.is_staff and not request.user.is_superuser:
            user_data = []
            for year_val in years:
                year_filter = referrals_qs.filter(
                    created_at__year=year_val,
                )
                
                # Apply date range filter if provided
                if date_from and date_to:
                    # Check if this year overlaps with the date range
                    year_start = datetime(year_val, 1, 1).date()
                    year_end = datetime(year_val, 12, 31).date()
                    
                    # Only include year if it overlaps with date range
                    if year_end >= date_from and year_start <= date_to:
                        year_filter = year_filter.filter(
                            created_at__date__gte=date_from,
                            created_at__date__lte=date_to
                        )
                    else:
                        # Year doesn't overlap with date range, set count to 0
                        user_data.append(0)
                        continue
                elif date_from:
                    year_filter = year_filter.filter(created_at__date__gte=date_from)
                elif date_to:
                    year_filter = year_filter.filter(created_at__date__lte=date_to)
                
                count = year_filter.count()
                user_data.append(count)
            
            return JsonResponse({
                'labels': year_labels,
                'datasets': [
                    {
                        'label': 'My Referrals',
                        'data': user_data,
                        'backgroundColor': '#4e73df',
                        'borderColor': '#4e73df',
                        'borderRadius': 10,
                        'barThickness': 20,
                    }
                ]
            })
        else:
            # Staff/admin: show data by facility
            data = {}
            for facility in facilities:
                facility_data = []
                for year_val in years:
                    year_filter = Referral.objects.filter(
                        patient__facility=facility,
                        created_at__year=year_val,
                    )
                    
                    # Apply date range filter if provided
                    if date_from and date_to:
                        # Check if this year overlaps with the date range
                        year_start = datetime(year_val, 1, 1).date()
                        year_end = datetime(year_val, 12, 31).date()
                        
                        # Only include year if it overlaps with date range
                        if year_end >= date_from and year_start <= date_to:
                            year_filter = year_filter.filter(
                                created_at__date__gte=date_from,
                                created_at__date__lte=date_to
                            )
                        else:
                            # Year doesn't overlap with date range, set count to 0
                            facility_data.append(0)
                            continue
                    elif date_from:
                        year_filter = year_filter.filter(created_at__date__gte=date_from)
                    elif date_to:
                        year_filter = year_filter.filter(created_at__date__lte=date_to)
                    
                    count = year_filter.count()
                    facility_data.append(count)
                data[facility.name] = facility_data

            return JsonResponse({
                'labels': year_labels,
                'datasets': [
                    {
                        'label': facility_name,
                        'data': facility_data,
                        'backgroundColor': f'#{hash(facility_name) % 0xFFFFFF:06x}',
                        'borderRadius': 10,
                        'barThickness': 20,
                    }
                    for facility_name, facility_data in data.items()
                ]
            })


def get_barangay_performance(request):
    """
    API endpoint to return barangay performance data.
    Returns referral status overview and completion rates by facility.
    """
    year = request.GET.get('year', datetime.now().year)
    month = request.GET.get('month')
    
    # Filter referrals by date
    referrals = Referral.objects.filter(created_at__year=year)
    if month:
        referrals = referrals.filter(created_at__month=month)
    
    # Get facilities with their referral counts by status
    facilities = Facility.objects.all()
    
    # Status overview data (stacked bar chart)
    status_data = {
        'labels': [],
        'datasets': {
            'completed': [],
            'ongoing': [],
            'cancelled': []
        }
    }
    
    # Completion rate data (grouped bar chart)
    completion_data = {
        'labels': [],
        'datasets': {
            'completed': [],
            'ongoing': []
        }
    }
    
    for facility in facilities:
        facility_referrals = referrals.filter(patient__facility=facility)
        
        # Count by status
        completed = facility_referrals.filter(status='completed').count()
        ongoing = facility_referrals.filter(status__in=['pending', 'in-progress']).count()
        cancelled = facility_referrals.filter(status='cancelled').count()
        
        # Add to status overview
        status_data['labels'].append(facility.name)
        status_data['datasets']['completed'].append(completed)
        status_data['datasets']['ongoing'].append(ongoing)
        status_data['datasets']['cancelled'].append(cancelled)
        
        # Add to completion rate
        completion_data['labels'].append(facility.name)
        completion_data['datasets']['completed'].append(completed)
        completion_data['datasets']['ongoing'].append(ongoing)
    
    return JsonResponse({
        'status_overview': {
            'labels': status_data['labels'],
            'datasets': [
                {
                    'label': 'Completed',
                    'data': status_data['datasets']['completed'],
                    'backgroundColor': '#4e73df'
                },
                {
                    'label': 'Ongoing',
                    'data': status_data['datasets']['ongoing'],
                    'backgroundColor': '#36b9cc'
                },
                {
                    'label': 'Cancelled',
                    'data': status_data['datasets']['cancelled'],
                    'backgroundColor': '#e74a3b'
                }
            ]
        },
        'completion_rate': {
            'labels': completion_data['labels'],
            'datasets': [
                {
                    'label': 'Completed Referrals',
                    'data': completion_data['datasets']['completed'],
                    'backgroundColor': '#4e73df'
                },
                {
                    'label': 'Ongoing Referrals',
                    'data': completion_data['datasets']['ongoing'],
                    'backgroundColor': '#36b9cc'
                }
            ]
        }
    })


def get_user_referral_summary(request):
    """
    API endpoint to return summary statistics for the current user.
    """

    user = request.user
    year = request.GET.get('year', datetime.now().year)
    month = request.GET.get('month')
    
    # Filter referrals by user and date
    referrals = Referral.objects.filter(user=user, created_at__year=year)
    if month:
        referrals = referrals.filter(created_at__month=month)
    
    # Get summary statistics
    total_referrals = referrals.count()
    pending_referrals = referrals.filter(status='pending').count()
    in_progress_referrals = referrals.filter(status='in-progress').count()
    completed_referrals = referrals.filter(status='completed').count()
    cancelled_referrals = referrals.filter(status='cancelled').count()
    
    # Get top diagnoses for this user
    medical_histories = Medical_History.objects.filter(user_id=user, diagnosed_date__year=year)
    if month:
        medical_histories = medical_histories.filter(diagnosed_date__month=month)
    
    # Count illness occurrences
    illness_counts = Counter(medical_histories.values_list('illness_name', flat=True))
    top_diagnoses = dict(illness_counts.most_common(5))
    
    return JsonResponse({
        'referral_summary': {
            'total': total_referrals,
            'pending': pending_referrals,
            'in_progress': in_progress_referrals,
            'completed': completed_referrals,
            'cancelled': cancelled_referrals
        },
        'top_diagnoses': top_diagnoses
    })


def get_system_usage_data(request):
    """
    API endpoint to return system usage data for analytics.
    Tracks logins and reports generated per barangay/facility.
    """
    from django.contrib.auth.models import User
    from django.db.models import Q, Count
    from django.utils import timezone
    from calendar import monthrange
    
    year = int(request.GET.get('year', datetime.now().year))
    month = request.GET.get('month')
    
    # Get all facilities (barangays)
    facilities = Facility.objects.all().order_by('name')
    
    # Prepare months data - show first 6 months or all 12
    if month:
        months = [datetime(year, int(month), 1).strftime('%b')]
        month_nums = [int(month)]
    else:
        # Show first 6 months for the chart (Jan-Jun)
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        month_nums = list(range(1, 7))
    
    # Initialize data structure
    data = {
        'labels': months,
        'datasets': []
    }
    
    # Color scheme matching the original chart
    login_colors = {
        'Carcor': '#4e73df',
        'Mesaoy': '#1cc88a',
        'New Cortez': '#36b9cc',
        'Sta. Cruz': '#f6c23e',
    }
    
    report_colors = {
        'Carcor': '#ff6347',
        'Mesaoy': '#ff4500',
        'New Cortez': '#ff8c00',
        'Sta. Cruz': '#ffb6c1',
    }
    
    # Default colors if facility name doesn't match
    default_login_colors = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#6f42c1', '#fd7e14', '#20c997']
    default_report_colors = ['#ff6347', '#ff4500', '#ff8c00', '#ffb6c1', '#e74a3b', '#6f42c1', '#fd7e14', '#20c997']
    
    for idx, facility in enumerate(facilities):
        facility_name = facility.name
        login_color = login_colors.get(facility_name, default_login_colors[idx % len(default_login_colors)])
        report_color = report_colors.get(facility_name, default_report_colors[idx % len(default_report_colors)])
        
        # Track logins per month
        # Count users associated with this facility who logged in during each month
        login_data = []
        for month_num in month_nums:
            # Get start and end of month (timezone-aware)
            start_date = timezone.make_aware(datetime(year, month_num, 1))
            if month_num == 12:
                end_date = timezone.make_aware(datetime(year + 1, 1, 1))
            else:
                end_date = timezone.make_aware(datetime(year, month_num + 1, 1))
            
            # Count logins from LoginLog model for users associated with this facility
            # Users can be linked via shared_facilities or via BHWRegistration/Doctors/Nurses
            try:
                from accounts.models import LoginLog
                
                # Get users associated with this facility
                facility_users = User.objects.filter(
                    Q(shared_facilities=facility) |
                    Q(bhwregistration__facility=facility) |
                    Q(doctors__facility=facility) |
                    Q(nurses__facility=facility) |
                    Q(midwives__facility=facility)
                ).distinct()
                
                # Count login events from LoginLog model for these users in this month
                login_count = LoginLog.objects.filter(
                    user__in=facility_users,
                    login_time__gte=start_date,
                    login_time__lt=end_date
                ).count()
            except (ImportError, AttributeError) as e:
                # Fallback if LoginLog model doesn't exist or isn't available
                print(f"Warning: Could not load LoginLog: {e}")
                login_count = 0
            
            login_data.append(login_count)
        
        # Track reports generated per month
        # Count accesses to report endpoints (system_usage_scorecard, morbidity_report, etc.)
        # Since we don't have a report log, we'll use referral and medical history creation as proxy
        # for report generation activity
        report_data = []
        for month_num in month_nums:
            # Count referrals created (as proxy for referral reports)
            referral_count = Referral.objects.filter(
                patient__facility=facility,
                created_at__year=year,
                created_at__month=month_num
            ).count()
            
            # Count medical histories created (as proxy for morbidity reports)
            medical_count = Medical_History.objects.filter(
                patient_id__facility=facility,
                diagnosed_date__year=year,
                diagnosed_date__month=month_num
            ).count()
            
            # Reports generated = sum of referrals and medical records (as they generate reports)
            report_count = referral_count + medical_count
            report_data.append(report_count)
        
        # Add login dataset
        data['datasets'].append({
            'label': f'{facility_name} - Logins',
            'data': login_data,
            'borderColor': login_color,
            'fill': False,
            'tension': 0.1,
        })
        
        # Add reports generated dataset
        data['datasets'].append({
            'label': f'{facility_name} - Reports Generated',
            'data': report_data,
            'borderColor': report_color,
            'fill': False,
            'tension': 0.1,
        })
    
    return JsonResponse(data)




@login_required
def system_usage_scorecard_report(request):
    """Printable system usage scorecard by facility and month."""

    now = now_in_singapore()

    def parse_int(value, fallback=None):
        try:
            parsed = int(value)
            return parsed
        except (TypeError, ValueError):
            return fallback

    year = parse_int(request.GET.get('year'), now.year) or now.year
    user_id = parse_int(request.GET.get('user_id'))
    
    # Get date_from and date_to parameters for direct date filtering
    date_from_str = request.GET.get('date_from', '')
    date_to_str = request.GET.get('date_to', '')
    date_from = None
    date_to = None
    
    if date_from_str:
        try:
            from datetime import datetime
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if date_to_str:
        try:
            from datetime import datetime
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Get facilities for the user (handles BHW users)
    facilities_qs = get_user_facilities(request.user, user_id)
    facilities = list(facilities_qs)
    
    # Determine which months to display based on date range
    if date_from and date_to:
        # Calculate months in the date range
        from datetime import datetime
        months_in_range = []
        current_date = date_from.replace(day=1)  # Start from first day of start month
        end_date = date_to
        
        while current_date <= end_date:
            months_in_range.append(current_date.month)
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        # Remove duplicates and sort
        months_in_range = sorted(list(set(months_in_range)))
        month_labels = [calendar.month_abbr[month] for month in months_in_range]
        month_indices = months_in_range
    else:
        # Show all 12 months if no date range
        month_labels = [calendar.month_abbr[i] for i in range(1, 13)]
        month_indices = list(range(1, 13))

    scorecard = []
    summary_referrals = [0] * len(month_indices)
    summary_medical = [0] * len(month_indices)

    for facility in facilities:
        referrals_per_month = []
        medical_per_month = []
        for month_idx in month_indices:
            # Build referral filters - if date range provided, filter by date within that month
            referral_filters = {
                'patient__facility': facility,
            }
            
            if date_from and date_to:
                # Filter by date range, but only count if the month falls within the range
                referral_filters['created_at__date__gte'] = date_from
                referral_filters['created_at__date__lte'] = date_to
                referral_filters['created_at__month'] = month_idx
            else:
                referral_filters['created_at__year'] = year
                referral_filters['created_at__month'] = month_idx
            
            # Filter by user_id if provided
            if user_id:
                referral_filters['user_id'] = user_id
            referral_count = Referral.objects.filter(**referral_filters).count()
            
            # Build medical history filters
            medical_filters = {
                'patient_id__facility': facility,
            }
            
            if date_from and date_to:
                # Filter by date range, but only count if the month falls within the range
                medical_filters['diagnosed_date__gte'] = date_from
                medical_filters['diagnosed_date__lte'] = date_to
                medical_filters['diagnosed_date__month'] = month_idx
            else:
                medical_filters['diagnosed_date__year'] = year
                medical_filters['diagnosed_date__month'] = month_idx
            
            # Filter by user_id if provided
            if user_id:
                medical_filters['user_id'] = user_id
            
            # Only count Medical_History entries from completed referrals
            medical_filters['referral__status'] = 'completed'
            medical_count = Medical_History.objects.filter(**medical_filters).count()
            referrals_per_month.append(referral_count)
            medical_per_month.append(medical_count)
            # Find index in month_indices list (not month_idx - 1)
            month_position = month_indices.index(month_idx)
            summary_referrals[month_position] += referral_count
            summary_medical[month_position] += medical_count

        scorecard.append({
            'facility': facility,
            'referrals': referrals_per_month,
            'medical': medical_per_month,
            'referrals_total': sum(referrals_per_month),
            'medical_total': sum(medical_per_month),
        })

    context = {
        'year': year,
        'month_labels': month_labels,
        'month_indices': month_indices,  # Add month_indices to context
        'scorecard': scorecard,
        'summary_referrals': summary_referrals,
        'summary_medical': summary_medical,
        'report_generated_at': now,
        'date_from': date_from,  # Add date_from to context
        'date_to': date_to,  # Add date_to to context
    }

    return render(request, 'analytics/system_usage_scorecard.html', context)


@login_required
def morbidity_report(request):
    """Printable morbidity report summarizing top diagnoses and trends."""

    now = now_in_singapore()

    def parse_int(value, fallback=None):
        try:
            parsed = int(value)
            return parsed
        except (TypeError, ValueError):
            return fallback

    year = parse_int(request.GET.get('year'), now.year) or now.year
    raw_month = parse_int(request.GET.get('month'))
    month = raw_month if raw_month and 1 <= raw_month <= 12 else None
    month_from = parse_int(request.GET.get('month_from'), None)
    month_to = parse_int(request.GET.get('month_to'), None)
    # If month_from and month_to are provided, use them; otherwise fall back to single month
    if month_from and month_to:
        month_from = month_from if 1 <= month_from <= 12 else None
        month_to = month_to if 1 <= month_to <= 12 else None
    
    # Get date_from and date_to parameters for direct date filtering
    date_from_str = request.GET.get('date_from', '')
    date_to_str = request.GET.get('date_to', '')
    date_from = None
    date_to = None
    
    if date_from_str:
        try:
            from datetime import datetime
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if date_to_str:
        try:
            from datetime import datetime
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    user_id = parse_int(request.GET.get('user_id'))
    facility_id = parse_int(request.GET.get('facility_id'))

    # Check if user is a doctor - if so, auto-filter by referrals examined by this doctor
    is_doctor = is_doctor_user(request.user)
    if is_doctor and not user_id:
        # Get referral IDs for referrals examined by this doctor
        doctor_referral_ids = Referral.objects.filter(
            examined_by=request.user
        ).values_list('referral_id', flat=True)
        # Filter medical histories linked to those referrals
        histories = Medical_History.objects.filter(
            referral_id__in=doctor_referral_ids
        )
    else:
        # Build base queryset
        histories = Medical_History.objects.all()
    
    # Priority: date_from/date_to > month_from/month_to > month > year
    if date_from and date_to:
        histories = histories.filter(diagnosed_date__gte=date_from, diagnosed_date__lte=date_to)
    elif date_from:
        histories = histories.filter(diagnosed_date__gte=date_from)
    elif date_to:
        histories = histories.filter(diagnosed_date__lte=date_to)
    elif month_from and month_to:
        histories = histories.filter(diagnosed_date__year=year, diagnosed_date__month__gte=month_from, diagnosed_date__month__lte=month_to)
    elif month:
        histories = histories.filter(diagnosed_date__year=year, diagnosed_date__month=month)
    else:
        histories = histories.filter(diagnosed_date__year=year)
    
    # For BHW users: filter by facility instead of user_id
    # Check if requesting user is a BHW (not a doctor, not staff/superuser)
    is_bhw = False
    bhw_facility = None
    if not is_doctor and not request.user.is_staff and not request.user.is_superuser:
        try:
            bhw_profile = BHWRegistration.objects.select_related('facility').get(user=request.user)
            if bhw_profile.facility:
                is_bhw = True
                bhw_facility = bhw_profile.facility
        except BHWRegistration.DoesNotExist:
            pass
    
    # Filter by facility_id if provided (explicit filter)
    if facility_id:
        histories = histories.filter(patient_id__facility_id=facility_id)
    # For BHW users without explicit user_id: filter by their facility
    elif is_bhw and bhw_facility and not user_id:
        histories = histories.filter(patient_id__facility=bhw_facility)
    # Filter by user_id if provided (for staff/superuser user-specific reports)
    # But if doctor and no explicit user_id param, we already filtered by examined_by referrals above
    elif user_id and not (is_doctor and not request.GET.get('user_id')):
        histories = histories.filter(user_id=user_id)
    
    # Filter to only include Medical_History records from completed referrals
    # Only show diagnoses from referrals that have been completed (status='completed')
    # Exclude records without a referral link (they're not part of the referral workflow)
    histories = histories.filter(referral__status='completed')

    # Normalize illnesses similar to API logic
    disease_data = Disease.objects.values_list('name', 'icd_code', 'critical_level')
    disease_name_map = {name.lower(): {'name': name, 'icd_code': icd_code, 'critical_level': level} 
                        for name, icd_code, level in disease_data}

    normalized_counts = Counter()
    diagnosis_meta = {}
    raw_entries = []

    for history in histories.select_related('patient_id', 'patient_id__facility').order_by('-diagnosed_date'):
        illness = (history.illness_name or '').strip()
        illness_lc = illness.lower()
        if illness_lc in ['cat bite', 'dog bite']:
            normalized = 'possible rabies'
        elif illness_lc == 'lbm':
            normalized = 'gastrointestinal issue'
        else:
            normalized = illness_lc

        disease_info = disease_name_map.get(normalized, {})
        display_name = disease_info.get('name') or illness.title() or 'Unspecified'
        icd_code = disease_info.get('icd_code', 'N/A')
        critical_level = disease_info.get('critical_level', 'N/A')
        diagnosis_meta.setdefault(display_name, {'icd_code': icd_code, 'critical_level': critical_level})
        normalized_counts[display_name] += 1

        raw_entries.append({
            'patient_name': f"{history.patient_id.first_name} {history.patient_id.last_name}" if history.patient_id else '',
            'facility': history.patient_id.facility.name if history.patient_id and history.patient_id.facility else '',
            'diagnosed_date': history.diagnosed_date,
            'illness_display': display_name,
            'illness_raw': illness,
            'notes': history.notes,
            'advice': history.advice,
        })

    # Determine top diagnoses (e.g., top 10)
    top_diagnoses = normalized_counts.most_common(10)
    total_cases = sum(normalized_counts.values())

    def classify_level(level):
        level_lower = (level or '').lower()
        if level_lower == 'high':
            return 'critical-high', 'danger'
        if level_lower == 'medium':
            return 'critical-medium', 'warning'
        if level_lower == 'low':
            return 'critical-low', 'success'
        return '', 'secondary'

    top_diagnoses_rows = []
    for name, count in top_diagnoses:
        meta = diagnosis_meta.get(name, {})
        if isinstance(meta, dict):
            critical = meta.get('critical_level', 'N/A')
            icd_code = meta.get('icd_code', 'N/A')
        else:
            # Backward compatibility for old format
            critical = meta if meta != 'N/A' else 'N/A'
            icd_code = 'N/A'
        row_class, badge_variant = classify_level(critical)
        percent = round((count / total_cases) * 100, 2) if total_cases else 0
        top_diagnoses_rows.append({
            'name': name,
            'icd_code': icd_code,
            'count': count,
            'critical': critical,
            'row_class': row_class,
            'badge_variant': badge_variant,
            'percent': percent,
        })

    # Build monthly trend data for chart table
    monthly_totals = defaultdict(lambda: Counter())
    for diagnose in histories:
        illness = (diagnose.illness_name or '').strip()
        illness_lc = illness.lower()
        if illness_lc in ['cat bite', 'dog bite']:
            normalized = 'possible rabies'
        elif illness_lc == 'lbm':
            normalized = 'gastrointestinal issue'
        else:
            normalized = illness_lc

        disease_info = disease_name_map.get(normalized, {})
        display_name = disease_info.get('name') or illness.title() or 'Unspecified'
        key = diagnose.diagnosed_date.strftime('%b')
        monthly_totals[key][display_name] += 1

    # Determine which months to show based on date range
    if date_from and date_to:
        # Calculate month range from dates
        start_month = date_from.month
        end_month = date_to.month
        # If dates span multiple years, include all months from start to end
        if date_from.year == date_to.year:
            month_labels = [calendar.month_abbr[i] for i in range(start_month, end_month + 1)]
        else:
            # Cross-year range: include months from start to Dec, then Jan to end
            month_labels = [calendar.month_abbr[i] for i in range(start_month, 13)]
            month_labels.extend([calendar.month_abbr[i] for i in range(1, end_month + 1)])
    elif date_from:
        # Only start date: show from that month to December of the same year
        start_month = date_from.month
        month_labels = [calendar.month_abbr[i] for i in range(start_month, 13)]
    elif date_to:
        # Only end date: show from January to that month
        end_month = date_to.month
        month_labels = [calendar.month_abbr[i] for i in range(1, end_month + 1)]
    elif month_from and month_to:
        # Month range provided
        month_labels = [calendar.month_abbr[i] for i in range(month_from, month_to + 1)]
    elif month:
        # Single month
        month_labels = [calendar.month_abbr[month]]
    else:
        # Build list of months from January to December (default)
        month_labels = [calendar.month_abbr[i] for i in range(1, 13)]

    # Build trend_table for ALL diagnoses (not just top 10)
    # This allows Monthly Trend to show all diagnoses even if there are more than 10
    trend_table = []
    # Use all diagnoses sorted by count (descending), not limited to top 10
    all_diagnoses = normalized_counts.most_common()  # Get all diagnoses sorted by count
    for label, _ in all_diagnoses:
        meta = diagnosis_meta.get(label, {})
        if isinstance(meta, dict):
            icd_code = meta.get('icd_code', 'N/A')
        else:
            icd_code = 'N/A'
        row = {
            'diagnosis': label,
            'icd_code': icd_code,
            'monthly_counts': [monthly_totals[m].get(label, 0) for m in month_labels],
        }
        row['total'] = sum(row['monthly_counts'])
        trend_table.append(row)

    month_name = calendar.month_name[month] if month else 'All Months'

    month_options = [{'value': '', 'label': 'All Months'}]
    month_options.extend({'value': str(idx), 'label': calendar.month_name[idx]} for idx in range(1, 13))

    context = {
        'year': year,
        'month': month,
        'month_name': month_name,
        'selected_month_value': str(month) if month else '',
        'month_options': month_options,
        'report_generated_at': now,
        'top_diagnoses': top_diagnoses_rows,
        'total_cases': total_cases,
        'trend_table': trend_table,
        'month_labels': month_labels,
        'raw_entries': raw_entries[:50],  # limit for print readability
        'diagnosis_meta': diagnosis_meta,
        'active_page': 'morbidity_report',
    }

    return render(request, 'analytics/morbidity_report.html', context)


@login_required
def facility_workforce_masterlist(request):
    """Printable facility & workforce roster report."""

    now = now_in_singapore()

    def parse_int(value, fallback=None):
        try:
            parsed = int(value)
            return parsed
        except (TypeError, ValueError):
            return fallback

    user_id = parse_int(request.GET.get('user_id'))

    # Determine facilities visible to the current user
    facilities_qs = get_user_facilities(request.user, user_id)
    facilities = list(facilities_qs)
    facility_ids = [f.pk for f in facilities]

    roster = []

    # Filter BHWs to only those in accessible facilities
    bhw_map = defaultdict(list)
    bhw_query = BHWRegistration.objects.select_related('facility').filter(status='ACTIVE')
    if facility_ids:
        bhw_query = bhw_query.filter(facility_id__in=facility_ids)
    for bhw in bhw_query.order_by('last_name'):
        if bhw.facility_id:
            bhw_map[bhw.facility_id].append(bhw)

    # Filter doctors to only those in accessible facilities
    doctor_map = defaultdict(list)
    doctor_query = Doctors.objects.select_related('facility').filter(status='ACTIVE')
    if facility_ids:
        doctor_query = doctor_query.filter(facility_id__in=facility_ids)
    for doctor in doctor_query.order_by('last_name'):
        if doctor.facility_id:
            doctor_map[doctor.facility_id].append(doctor)

    for facility in facilities:
        roster.append({
            'facility': facility,
            'bhws': bhw_map.get(facility.pk, []),
            'doctors': doctor_map.get(facility.pk, []),
        })

    # Get all active doctors for MHO table (regardless of facility assignment)
    # But only if user is staff/superuser or if no user_id filter is applied
    if (request.user.is_staff or request.user.is_superuser) and not user_id:
        all_doctors = Doctors.objects.filter(status='ACTIVE').order_by('last_name', 'first_name')
    else:
        # For non-staff users or when filtering by user_id, only show doctors from their facilities
        all_doctors = Doctors.objects.filter(status='ACTIVE', facility_id__in=facility_ids).order_by('last_name', 'first_name') if facility_ids else Doctors.objects.none()

    context = {
        'roster': roster,
        'all_doctors': all_doctors,
        'generated_at': now,
        'is_staff': request.user.is_staff or request.user.is_superuser,
    }

    return render(request, 'analytics/facility_workforce_masterlist.html', context)



@login_required
def barangay_referral_performance_report(request):
    """Render a printable monthly and year-to-date referral performance summary per facility."""

    now = now_in_singapore()

    def parse_int(value, fallback=None):
        try:
            parsed = int(value)
            return parsed
        except (TypeError, ValueError):
            return fallback

    year = parse_int(request.GET.get('year'), now.year) or now.year
    raw_month = parse_int(request.GET.get('month'), None)
    month = raw_month if raw_month and 1 <= raw_month <= 12 else None
    month_from = parse_int(request.GET.get('month_from'), None)
    month_to = parse_int(request.GET.get('month_to'), None)
    # If month_from and month_to are provided, use them; otherwise fall back to single month
    if month_from and month_to:
        month_from = month_from if 1 <= month_from <= 12 else None
        month_to = month_to if 1 <= month_to <= 12 else None
    
    # Get date_from and date_to parameters for direct date filtering
    date_from_str = request.GET.get('date_from', '')
    date_to_str = request.GET.get('date_to', '')
    date_from = None
    date_to = None
    
    if date_from_str:
        try:
            from datetime import datetime
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if date_to_str:
        try:
            from datetime import datetime
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    user_id = parse_int(request.GET.get('user_id'))

    # Determine month_name for display - prioritize date range if provided
    if date_from and date_to:
        month_name = f"{date_from.strftime('%B %d, %Y')} to {date_to.strftime('%B %d, %Y')}"
    elif month_from and month_to:
        if month_from == month_to:
            # If same month, just show the month name
            month_name = calendar.month_name[month_from]
        else:
            month_name = f"{calendar.month_name[month_from]} to {calendar.month_name[month_to]}"
    elif month:
        month_name = calendar.month_name[month]
    else:
        month_name = 'All Months'

    # Determine facilities visible to the current user
    facilities_qs = get_user_facilities(request.user, user_id)
    facilities = list(facilities_qs)

    status_keys = ['pending', 'in-progress', 'completed']
    status_labels = {
        'pending': 'Pending',
        'in-progress': 'In-Progress',
        'completed': 'Completed Referral',
    }

    today = now.date()
    facilities_data = []

    for facility in facilities:
        # Build referral filters - priority: date_from/date_to > month_from/month_to > month > year
        monthly_filters = {
            'patient__facility': facility,
        }
        
        if date_from and date_to:
            monthly_filters['created_at__date__gte'] = date_from
            monthly_filters['created_at__date__lte'] = date_to
        elif date_from:
            monthly_filters['created_at__date__gte'] = date_from
        elif date_to:
            monthly_filters['created_at__date__lte'] = date_to
        elif month_from and month_to:
            monthly_filters['created_at__year'] = year
            monthly_filters['created_at__month__gte'] = month_from
            monthly_filters['created_at__month__lte'] = month_to
        elif month:
            monthly_filters['created_at__year'] = year
            monthly_filters['created_at__month'] = month
        else:
            monthly_filters['created_at__year'] = year
        
        # Filter by user_id if provided
        if user_id:
            monthly_filters['user_id'] = user_id

        monthly_qs = Referral.objects.filter(**monthly_filters)

        monthly_counts = {status: monthly_qs.filter(status=status).count() for status in status_keys}
        monthly_total = sum(monthly_counts.values())

        # Count follow-ups for this facility
        # Get all medical histories with follow-up dates for patients in this facility
        # We count all follow-ups regardless of when they were created, but filter by followup_date
        followup_filters = {
            'patient_id__facility': facility,
            'followup_date__isnull': False,
        }
        
        # Filter by user_id if provided (for user-specific reports)
        if user_id:
            followup_filters['user_id'] = user_id
        
        # Filter follow-ups by their scheduled date (followup_date), not creation date
        # Priority: date_from/date_to > month_from/month_to > month > year
        if date_from and date_to:
            followup_filters['followup_date__gte'] = date_from
            followup_filters['followup_date__lte'] = date_to
        elif date_from:
            followup_filters['followup_date__gte'] = date_from
        elif date_to:
            followup_filters['followup_date__lte'] = date_to
        elif month_from and month_to:
            followup_filters['followup_date__year'] = year
            followup_filters['followup_date__month__gte'] = month_from
            followup_filters['followup_date__month__lte'] = month_to
        elif month:
            followup_filters['followup_date__year'] = year
            followup_filters['followup_date__month'] = month
        else:
            # For all months, count follow-ups scheduled in the selected year
            followup_filters['followup_date__year'] = year

        followups_qs = Medical_History.objects.filter(**followup_filters)
        
        # Get completed follow-up visits to exclude them
        completed_followup_ids = set(
            FollowUpVisit.objects.filter(
                status='completed',
                medical_history__in=followups_qs
            ).values_list('medical_history_id', flat=True)
        )

        # Count overdue and scheduled follow-ups
        overdue_count = 0
        scheduled_count = 0
        
        for followup in followups_qs:
            # Skip if there's a completed visit
            if followup.history_id in completed_followup_ids:
                continue
            
            # Count based on current status (overdue = past due date, scheduled = future)
            if followup.followup_date < today:
                overdue_count += 1
            else:
                scheduled_count += 1

        facilities_data.append({
            'facility': facility,
            'monthly': {
                'counts': monthly_counts,
                'total': monthly_total,
                'overdue_fu': overdue_count,
                'scheduled_fu': scheduled_count,
            },
        })

    facility_ids = [f.pk for f in facilities]

    summary_totals = {
        'monthly': {status: 0 for status in status_keys},
        'overdue_fu': 0,
        'scheduled_fu': 0,
    }

    for entry in facilities_data:
        for status in status_keys:
            summary_totals['monthly'][status] += entry['monthly']['counts'][status]
        summary_totals['overdue_fu'] += entry['monthly']['overdue_fu']
        summary_totals['scheduled_fu'] += entry['monthly']['scheduled_fu']

    summary_totals['monthly']['total'] = sum(summary_totals['monthly'][status] for status in status_keys)

    # Month and year selection helpers
    month_options = [{'value': '', 'label': 'All Months'}]
    month_options.extend({'value': str(idx), 'label': calendar.month_name[idx]} for idx in range(1, 13))

    context = {
        'facilities_data': facilities_data,
        'summary_totals': summary_totals,
        'status_keys': status_keys,
        'status_labels': status_labels,
        'monthly_column_span': len(status_keys) + 3,
        'total_columns': len(status_keys) + 4,
        'selected_year': year,
        'selected_month': month,
        'selected_month_value': str(month) if month else '',
        'month_name': month_name,
        'month_options': month_options,
        'report_generated_at': now,
    }

    return render(request, 'analytics/barangay_referral_performance.html', context)


@login_required
def referral_registry_report(request):
    """Printable referral registry with vital signs and diagnoses."""

    now = now_in_singapore()

    def parse_int(value, fallback=None):
        try:
            parsed = int(value)
            return parsed
        except (TypeError, ValueError):
            return fallback

    year = parse_int(request.GET.get('year'), now.year) or now.year
    raw_month = parse_int(request.GET.get('month'))
    month = raw_month if raw_month and 1 <= raw_month <= 12 else None
    month_from = parse_int(request.GET.get('month_from'), None)
    month_to = parse_int(request.GET.get('month_to'), None)
    # If month_from and month_to are provided, use them; otherwise fall back to single month
    if month_from and month_to:
        month_from = month_from if 1 <= month_from <= 12 else None
        month_to = month_to if 1 <= month_to <= 12 else None
    
    # Get date_from and date_to parameters for direct date filtering
    date_from_str = request.GET.get('date_from', '')
    date_to_str = request.GET.get('date_to', '')
    date_from = None
    date_to = None
    
    if date_from_str:
        try:
            from datetime import datetime
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if date_to_str:
        try:
            from datetime import datetime
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    facility_id = parse_int(request.GET.get('facility_id'))
    status_filter = request.GET.get('status') or ''
    user_id = parse_int(request.GET.get('user_id'))

    # Check if user is a doctor - if so, auto-filter by examined_by
    is_doctor = is_doctor_user(request.user)
    
    # Determine accessible facilities based on user
    facilities_qs = get_user_facilities(request.user, user_id)
    facilities = list(facilities_qs)

    # Build referrals queryset
    if is_doctor and not user_id:
        # For doctors, filter by examined_by (referrals they examined)
        referrals = Referral.objects.select_related('patient', 'patient__facility', 'user').filter(
            examined_by=request.user
        ).order_by('-created_at')
    else:
        referrals = Referral.objects.select_related('patient', 'patient__facility', 'user').order_by('-created_at')

    # Priority: date_from/date_to > month_from/month_to > month > year
    if date_from and date_to:
        referrals = referrals.filter(created_at__date__gte=date_from, created_at__date__lte=date_to)
    elif date_from:
        referrals = referrals.filter(created_at__date__gte=date_from)
    elif date_to:
        referrals = referrals.filter(created_at__date__lte=date_to)
    elif month_from and month_to:
        referrals = referrals.filter(created_at__year=year, created_at__month__gte=month_from, created_at__month__lte=month_to)
    elif month:
        referrals = referrals.filter(created_at__year=year, created_at__month=month)
    else:
        referrals = referrals.filter(created_at__year=year)

    if facility_id:
        referrals = referrals.filter(patient__facility_id=facility_id)

    if status_filter:
        referrals = referrals.filter(status=status_filter)
    
    # Filter by user_id if provided (for user-specific reports)
    # But if doctor and no explicit user_id param, we already filtered by examined_by above
    if user_id and not (is_doctor and not request.GET.get('user_id')):
        referrals = referrals.filter(user_id=user_id)

    # Prepare registry entries
    registry_entries = []
    for referral in referrals:
        registry_entries.append({
            'referral_id': referral.referral_id,
            'created_at': referral.created_at,
            'facility': referral.patient.facility.name if referral.patient and referral.patient.facility else '',
            'patient_name': f"{referral.patient.first_name} {referral.patient.last_name}" if referral.patient else '',
            'patient_id': referral.patient.patients_id if referral.patient else '',
            'chief_complaint': referral.chief_complaint,
            'diagnosis': referral.final_diagnosis or referral.initial_diagnosis,
            'status': referral.status,
            'weight': referral.weight,
            'height': referral.height,
            'bp': f"{referral.bp_systolic}/{referral.bp_diastolic}",
            'pulse_rate': referral.pulse_rate,
            'respiratory_rate': referral.respiratory_rate,
            'temperature': referral.temperature,
            'oxygen_saturation': referral.oxygen_saturation,
            'user': referral.user.get_full_name() if referral.user else '',
        })

    # Determine month_name for display - prioritize date range if provided
    if date_from and date_to:
        month_name = f"{date_from.strftime('%B %d, %Y')} to {date_to.strftime('%B %d, %Y')}"
    elif month_from and month_to:
        if month_from == month_to:
            # If same month, just show the month name
            month_name = calendar.month_name[month_from]
        else:
            month_name = f"{calendar.month_name[month_from]} to {calendar.month_name[month_to]}"
    elif month:
        month_name = calendar.month_name[month]
    else:
        month_name = 'All Months'

    month_options = [{'value': '', 'label': 'All Months'}]
    month_options.extend({'value': str(idx), 'label': calendar.month_name[idx]} for idx in range(1, 13))

    status_options = [
        {'value': '', 'label': 'All Statuses'},
        {'value': 'pending', 'label': _('Pending')},
        {'value': 'in-progress', 'label': _('In-Progress')},
        {'value': 'completed', 'label': _('Completed')},
        {'value': 'cancelled', 'label': _('Cancelled')},
    ]

    context = {
        'entries': registry_entries,
        'facilities': facilities,
        'selected_facility': facility_id,
        'status_options': status_options,
        'selected_status': status_filter,
        'year': year,
        'month': month,
        'month_name': month_name,
        'selected_month_value': str(month) if month else '',
        'month_options': month_options,
        'report_generated_at': now,
        'active_page': 'referral_registry_report',
    }

    return render(request, 'analytics/referral_registry_report.html', context)


@login_required
def get_disease_peak_predictions(request):
    """
    API endpoint to get disease peak predictions for 2025.
    Returns predicted disease peaks for each month.
    Supports month range filtering and disease filtering.
    Uses caching to avoid regenerating predictions.
    
    Query parameters:
        - month: Optional specific month name (e.g., "January")
        - month_from: Start month for range (e.g., "March")
        - month_to: End month for range (e.g., "May")
        - disease: Optional disease code to filter (e.g., "J06.9")
        - samples_per_month: Number of samples to simulate (default: 100)
        - use_db: Use Django database instead of CSV (default: false)
    
    Returns:
        JSON response with predictions for each month or aggregated range
    """
    from django.core.cache import cache
    import hashlib
    
    month = request.GET.get('month', None)
    month_from = request.GET.get('month_from', None)
    month_to = request.GET.get('month_to', None)
    disease_filter = request.GET.get('disease', None)
    samples_per_month = int(request.GET.get('samples_per_month', 100))
    use_db = request.GET.get('use_db', 'false').lower() == 'true'
    
    # Create cache key based on parameters
    cache_key_parts = ['disease_peak_predictions', str(use_db), str(samples_per_month)]
    if month:
        cache_key_parts.append(month)
    elif month_from and month_to:
        cache_key_parts.append(f'{month_from}_{month_to}')
    else:
        cache_key_parts.append('all_months')
    if disease_filter:
        cache_key_parts.append(disease_filter)
    cache_key = hashlib.md5('_'.join(cache_key_parts).encode()).hexdigest()
    
    # Check cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        return JsonResponse({
            **cached_result,
            "cached": True
        })
    
    # NEW: Calculate from barangay predictions to ensure consistency
    # This ensures main predictions match barangay breakdown totals
    from analytics.ml_utils import predict_barangay_disease_peak_2025
    
    barangay_predictions = predict_barangay_disease_peak_2025(use_db=use_db)
    
    if "error" in barangay_predictions:
        # Fallback to original method if barangay predictions fail
        result = predict_disease_peak_for_month(
            month_name=month,
            samples_per_month=samples_per_month,
            use_db=use_db
        )
        if "error" in result:
            return JsonResponse(result, status=400)
    else:
        # Aggregate barangay predictions to get main totals
        # This ensures consistency between main predictions and barangay breakdown
        month_names = {
            "January": 1, "February": 2, "March": 3, "April": 4,
            "May": 5, "June": 6, "July": 7, "August": 8,
            "September": 9, "October": 10, "November": 11, "December": 12
        }
        
        result = {}
        
        for month_name, month_num in month_names.items():
            # Aggregate all diseases across all barangays for this month
            all_diseases = {}
            peak_disease = None
            peak_count = 0
            
            for barangay_name, monthly_data in barangay_predictions.items():
                if month_num in monthly_data:
                    month_data = monthly_data[month_num]
                    for disease, count in month_data.get('all_diseases', {}).items():
                        all_diseases[disease] = all_diseases.get(disease, 0) + count
                        
                        # Track peak disease
                        if all_diseases[disease] > peak_count:
                            peak_count = all_diseases[disease]
                            peak_disease = disease
            
            if all_diseases:
                result[month_name] = {
                    'disease': peak_disease if peak_disease else "Unknown",
                    'count': int(peak_count),
                    'total_samples': sum(all_diseases.values()),
                    'all_diseases': all_diseases
                }
            else:
                result[month_name] = {
                    'disease': "Unknown",
                    'count': 0,
                    'total_samples': 0,
                    'all_diseases': {}
                }
    
    # Filter by disease if specified
    # Note: We keep all_diseases intact so heat index can compare against all diseases
    if disease_filter:
        filtered_result = {}
        for month_name, month_data in result.items():
            if disease_filter in month_data.get('all_diseases', {}):
                filtered_result[month_name] = {
                    'disease': disease_filter,
                    'count': month_data['all_diseases'][disease_filter],
                    'total_samples': month_data['all_diseases'][disease_filter],
                    'all_diseases': month_data.get('all_diseases', {})  # Keep ALL diseases for comparison
                }
        result = filtered_result
    
    # Aggregate month range if specified
    if month_from and month_to:
        month_names = {
            "January": 1, "February": 2, "March": 3, "April": 4,
            "May": 5, "June": 6, "July": 7, "August": 8,
            "September": 9, "October": 10, "November": 11, "December": 12
        }
        
        from_idx = month_names.get(month_from, 1)
        to_idx = month_names.get(month_to, 12)
        
        # Aggregate all diseases across the range
        aggregated_diseases = {}
        total_cases = 0
        peak_disease = None
        peak_count = 0
        
        for month_name, month_num in month_names.items():
            if from_idx <= month_num <= to_idx:
                if month_name in result:
                    month_data = result[month_name]
                    for disease, count in month_data.get('all_diseases', {}).items():
                        aggregated_diseases[disease] = aggregated_diseases.get(disease, 0) + count
                        total_cases += count
                        
                        if aggregated_diseases[disease] > peak_count:
                            peak_count = aggregated_diseases[disease]
                            peak_disease = disease
        
        # Return aggregated result
        aggregated_result = {
            f"{month_from} - {month_to}": {
                'disease': peak_disease if peak_disease else "Unknown",
                'count': peak_count,
                'total_samples': total_cases,
                'all_diseases': aggregated_diseases
            }
        }
        
        cache.set(cache_key, aggregated_result, 3600)
        return JsonResponse(aggregated_result)
    
    # Cache predictions for 1 hour
    cache.set(cache_key, result, 3600)  # 1 hour
    
    return JsonResponse(result)


@login_required
def get_historical_disease_data(request):
    """
    API endpoint to get historical disease data for 2023-2024.
    Returns actual disease cases from database/CSV.
    Supports month range filtering and disease filtering.
    
    Query parameters:
        - year: Year to get data for (2023 or 2024)
        - month: Optional specific month name (e.g., "January")
        - month_from: Start month for range (e.g., "March")
        - month_to: End month for range (e.g., "May")
        - disease: Optional disease code to filter (e.g., "J06.9")
        - use_db: Use Django database instead of CSV (default: true)
    
    Returns:
        JSON response with historical data in same format as predictions
    """
    from django.core.cache import cache
    from django.db.models import Q, Count
    from datetime import datetime
    import hashlib
    import pandas as pd
    
    year = int(request.GET.get('year', 2024))
    month = request.GET.get('month', None)
    month_from = request.GET.get('month_from', None)
    month_to = request.GET.get('month_to', None)
    disease_filter = request.GET.get('disease', None)
    use_db = request.GET.get('use_db', 'true').lower() == 'true'
    
    # Only allow 2023-2024 for historical data
    if year not in [2023, 2024]:
        return JsonResponse({"error": f"Historical data only available for 2023-2024. Year {year} not supported."}, status=400)
    
    # Create cache key
    cache_key_parts = ['historical_disease_data', str(year), str(use_db)]
    if month:
        cache_key_parts.append(month)
    elif month_from and month_to:
        cache_key_parts.append(f'{month_from}_{month_to}')
    else:
        cache_key_parts.append('all_months')
    if disease_filter:
        cache_key_parts.append(disease_filter)
    cache_key = hashlib.md5('_'.join(cache_key_parts).encode()).hexdigest()
    
    # Check cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        return JsonResponse({
            **cached_result,
            "cached": True,
            "data_type": "historical"
        })
    
    # Load historical data
    if use_db:
        from referrals.models import Referral
        from analytics.ml_utils import queryset_to_disease_peak_dataframe
        
        referrals = Referral.objects.filter(
            created_at__year=year
        ).exclude(
            Q(patient__isnull=True) | 
            Q(initial_diagnosis__isnull=True) | 
            Q(initial_diagnosis='')
        ).select_related('patient', 'facility')
        
        if not referrals.exists():
            return JsonResponse({"error": f"No referral data found for year {year}"}, status=400)
        
        df = queryset_to_disease_peak_dataframe(referrals)
    else:
        from analytics.ml_utils import load_disease_peak_csv_data
        try:
            df = load_disease_peak_csv_data(
                csv_2023_path=None,
                csv_2024_path=None
            )
            # Filter by year
            df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
            df = df[df['DATE'].dt.year == year]
        except Exception as e:
            return JsonResponse({"error": f"Error loading CSV data: {str(e)}"}, status=400)
    
    if df.empty:
        return JsonResponse({"error": f"No data available for year {year}"}, status=400)
    
    # Process DATE column
    if 'DATE' not in df.columns:
        if 'CREATED_AT' in df.columns:
            df['DATE'] = pd.to_datetime(df['CREATED_AT'], errors='coerce')
        else:
            return JsonResponse({"error": "No date column found in data"}, status=400)
    
    df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
    df = df.dropna(subset=['DATE'])
    
    # Filter by allowed ICD codes
    allowed_icd = ['T14.1', 'W54.99', 'J06.9', 'Z00', 'I10.1']
    df = df[df['ICD10 CODE'].isin(allowed_icd)]
    
    # Store disease filter but don't apply it yet - we need all diseases for comparison
    selected_disease = disease_filter
    
    if df.empty:
        return JsonResponse({"error": "No data remaining after filtering"}, status=400)
    
    # Aggregate monthly by disease (aggregate ALL diseases first)
    df['MONTH_NAME'] = df['DATE'].dt.strftime('%B')
    monthly_counts = df.groupby(['MONTH_NAME', 'ICD10 CODE']).size().reset_index(name='cases')
    
    # Format results to match prediction format
    month_names = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12
    }
    
    results = {}
    target_months = [month] if month and month in month_names else list(month_names.keys())
    
    for month_name in target_months:
        month_data = monthly_counts[monthly_counts['MONTH_NAME'] == month_name]
        
        all_diseases = {}
        peak_disease = None
        peak_count = 0
        
        for _, row in month_data.iterrows():
            disease_code = str(row['ICD10 CODE'])
            cases = int(row['cases'])
            all_diseases[disease_code] = cases
            
            if cases > peak_count:
                peak_count = cases
                peak_disease = disease_code
        
        if all_diseases:
            # If disease filter is specified, use it as the peak disease for display
            # but keep all_diseases intact for heat index comparison
            display_disease = selected_disease if selected_disease and selected_disease in all_diseases else peak_disease
            display_count = all_diseases.get(display_disease, 0) if display_disease else int(peak_count)
            
            results[month_name] = {
                'disease': display_disease if display_disease else "Unknown",
                'count': int(display_count),
                'total_samples': sum(all_diseases.values()),
                'all_diseases': all_diseases  # Keep ALL diseases for comparison
            }
        else:
            results[month_name] = {
                'disease': "Unknown",
                'count': 0,
                'total_samples': 0,
                'all_diseases': {}
            }
    
    # Aggregate month range if specified
    if month_from and month_to:
        from_idx = month_names.get(month_from, 1)
        to_idx = month_names.get(month_to, 12)
        
        aggregated_diseases = {}
        total_cases = 0
        peak_disease = None
        peak_count = 0
        
        for month_name, month_num in month_names.items():
            if from_idx <= month_num <= to_idx:
                if month_name in results:
                    month_data = results[month_name]
                    for disease, count in month_data.get('all_diseases', {}).items():
                        aggregated_diseases[disease] = aggregated_diseases.get(disease, 0) + count
                        total_cases += count
                        
                        if aggregated_diseases[disease] > peak_count:
                            peak_count = aggregated_diseases[disease]
                            peak_disease = disease
        
        aggregated_result = {
            f"{month_from} - {month_to}": {
                'disease': peak_disease if peak_disease else "Unknown",
                'count': peak_count,
                'total_samples': total_cases,
                'all_diseases': aggregated_diseases
            },
            "data_type": "historical",
            "year": year
        }
        
        cache.set(cache_key, aggregated_result, 3600)
        return JsonResponse(aggregated_result)
    
    # Cache for 1 hour
    cache.set(cache_key, results, 3600)
    
    return JsonResponse({
        **results,
        "data_type": "historical",
        "year": year
    })


@login_required
def train_barangay_disease_peak_model_api(request):
    """
    API endpoint to train barangay-based disease peak prediction model.
    Uses caching to avoid retraining if models already exist.
    
    Query parameters:
        - use_db: Use Django database instead of CSV (default: false)
        - allowed_icd: Comma-separated list of ICD codes (optional)
        - force_retrain: Force retraining even if cached (default: false)
    
    Returns:
        JSON response with training status
    """
    from django.core.cache import cache
    import hashlib
    import os
    
    use_db = request.GET.get('use_db', 'false').lower() == 'true'
    allowed_icd_param = request.GET.get('allowed_icd', None)
    force_retrain = request.GET.get('force_retrain', 'false').lower() == 'true'
    
    allowed_icd = None
    if allowed_icd_param:
        allowed_icd = [code.strip() for code in allowed_icd_param.split(',')]
    
    # Create cache key based on parameters
    cache_key_parts = ['train_barangay_model', str(use_db)]
    if allowed_icd:
        cache_key_parts.append(','.join(sorted(allowed_icd)))
    cache_key = hashlib.md5('_'.join(cache_key_parts).encode()).hexdigest()
    
    # Check if models exist on disk and are cached
    from analytics.ml_utils import get_ml_models_path
    models_dir = get_ml_models_path()
    model_path = os.path.join(models_dir, 'barangay_disease_peak_models.pkl')
    metadata_path = os.path.join(models_dir, 'barangay_disease_peak_metadata.pkl')
    
    # Check cache first (unless force_retrain is True)
    if not force_retrain:
        cached_result = cache.get(cache_key)
        if cached_result:
            # Verify models still exist on disk
            if os.path.exists(model_path) and os.path.exists(metadata_path):
                return JsonResponse({
                    **cached_result,
                    "cached": True,
                    "message": "Using cached training result. Models already exist."
                })
    
    # Check if models exist on disk (even if not in cache)
    if not force_retrain and os.path.exists(model_path) and os.path.exists(metadata_path):
        # Models exist, return success without retraining
        result = {
            "status": "Models already exist",
            "models_saved_to": model_path,
            "metadata_saved_to": metadata_path,
            "message": "Models already trained and saved. Use force_retrain=true to retrain."
        }
        # Cache the result for 24 hours
        cache.set(cache_key, result, 86400)  # 24 hours
        return JsonResponse(result)
    
    # Train the model
    result = train_barangay_disease_peak_model(
        use_db=use_db,
        allowed_icd=allowed_icd
    )
    
    if "error" in result:
        return JsonResponse(result, status=400)
    
    # Cache the result for 24 hours
    cache.set(cache_key, result, 86400)  # 24 hours
    
    # Invalidate prediction caches since models have been retrained
    # Clear all barangay prediction caches
    cache_keys_to_clear = [
        'barangay_predictions',
        'disease_peak_predictions'
    ]
    # Note: We can't easily clear all keys with a pattern in LocMemCache,
    # but the cache will expire naturally. For production with Redis,
    # you could use cache.delete_pattern('barangay_predictions*')
    
    return JsonResponse(result)


@login_required
def get_barangay_disease_peak_predictions(request):
    """
    API endpoint to get barangay-based disease peak predictions for 2025.
    Returns predicted disease peaks for each barangay per month.
    Uses caching to avoid regenerating predictions.
    
    Query parameters:
        - barangays: Comma-separated list of barangay names to filter (optional)
        - use_db: Use Django database instead of CSV (default: false)
    
    Returns:
        JSON response with predictions per barangay per month
    """
    from django.core.cache import cache
    import hashlib
    
    barangays_param = request.GET.get('barangays', None)
    use_db = request.GET.get('use_db', 'false').lower() == 'true'
    
    target_barangays = None
    if barangays_param:
        target_barangays = [b.strip() for b in barangays_param.split(',')]
    
    # Create cache key based on parameters
    cache_key_parts = ['barangay_predictions', str(use_db)]
    if target_barangays:
        cache_key_parts.append(','.join(sorted(target_barangays)))
    else:
        cache_key_parts.append('all')
    cache_key = hashlib.md5('_'.join(cache_key_parts).encode()).hexdigest()
    
    # Check cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        return JsonResponse({
            **cached_result,
            "cached": True
        })
    
    # Generate predictions
    result = predict_barangay_disease_peak_2025(
        target_barangays=target_barangays,
        use_db=use_db
    )
    
    if "error" in result:
        return JsonResponse(result, status=400)
    
    # Cache predictions for 1 hour (predictions don't change unless model is retrained)
    cache.set(cache_key, result, 3600)  # 1 hour
    
    return JsonResponse(result)


@login_required
def get_barangay_heatmap_data(request):
    """
    Get barangay predictions with facility coordinates for heatmap.
    Matches CSV barangay names to facility names/barangay fields.
    
    Query parameters:
        - use_db: Use Django database instead of CSV (default: false)
    
    Returns:
        JSON response with structure:
        {
            "Kauswagan": {
                "1": {  # Month number (1-12)
                    "total_cases": 24,
                    "diseases": {"T14.1": 10, "J06.9": 14},
                    "coordinates": [
                        {"lat": 7.58, "lng": 125.82, "facility_name": "Kauswagan MHO"}
                    ]
                }
            }
        }
    """
    from facilities.models import Facility
    from django.core.cache import cache
    import hashlib
    
    use_db = request.GET.get('use_db', 'false').lower() == 'true'
    
    # Create cache key
    cache_key = hashlib.md5(f'barangay_heatmap_data_{use_db}'.encode()).hexdigest()
    
    # Check cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        return JsonResponse({
            **cached_result,
            "cached": True
        })
    
    # Get barangay predictions (from CSV or database)
    barangay_predictions = predict_barangay_disease_peak_2025(use_db=use_db)
    
    if "error" in barangay_predictions:
        return JsonResponse(barangay_predictions, status=400)
    
    # Get all facilities
    facilities = Facility.objects.all()
    
    # Match barangay to facilities and combine
    results = {}
    for barangay_name, monthly_data in barangay_predictions.items():
        # Find facilities matching this barangay
        # Match if: barangay name is in facility name, or facility.barangay matches
        matching_facilities = []
        for facility in facilities:
            facility_name_upper = (facility.name or '').upper()
            facility_barangay_upper = (facility.barangay or '').upper()
            barangay_upper = barangay_name.upper()
            
            # Match if barangay name appears in facility name or facility.barangay matches
            if (barangay_upper in facility_name_upper or 
                facility_barangay_upper == barangay_upper or
                facility_name_upper == barangay_upper):
                matching_facilities.append({
                    'lat': float(facility.latitude),
                    'lng': float(facility.longitude),
                    'facility_name': facility.name
                })
        
        if not matching_facilities:
            continue  # Skip if no matching facilities
        
        results[barangay_name] = {}
        for month_num, month_data in monthly_data.items():
            # Month is already a number (1-12) from predict_barangay_disease_peak_2025
            if not isinstance(month_num, int) or month_num < 1 or month_num > 12:
                continue
            
            # Extract diseases and total cases
            if isinstance(month_data, dict):
                all_diseases = month_data.get('all_diseases', {})
                # Sum all diseases for this month
                total_cases = sum(all_diseases.values()) if isinstance(all_diseases, dict) else 0
            else:
                all_diseases = {}
                total_cases = 0
            
            results[barangay_name][month_num] = {
                'total_cases': total_cases,
                'diseases': all_diseases,
                'coordinates': matching_facilities
            }
    
    # Cache for 1 hour
    cache.set(cache_key, results, 3600)
    
    return JsonResponse(results)


@login_required
def get_barangay_breakdown(request):
    """
    Get barangay breakdown for a specific month and disease.
    
    Query parameters:
        - year: Year (2023, 2024, or 2025)
        - month: Month name (e.g., "April")
        - disease: Disease code (e.g., "J06.9")
        - use_db: Use database (default: true)
    
    Returns:
        JSON with structure:
        {
            "total_cases": 38,
            "barangays": [
                {"name": "Kauswagan", "cases": 12, "percentage": 31.6},
                {"name": "Poblacion", "cases": 8, "percentage": 21.1},
                ...
            ]
        }
    """
    import pandas as pd
    from django.core.cache import cache
    import hashlib
    
    year = int(request.GET.get('year', 2025))
    month = request.GET.get('month', 'January')
    disease = request.GET.get('disease', 'T14.1')
    use_db = request.GET.get('use_db', 'true').lower() == 'true'
    
    month_map = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12
    }
    month_num = month_map.get(month, 1)
    
    # Create cache key
    cache_key = hashlib.md5(f'barangay_breakdown_{year}_{month}_{disease}_{use_db}'.encode()).hexdigest()
    cached_result = cache.get(cache_key)
    if cached_result:
        return JsonResponse(cached_result)
    
    if year < 2025:
        # Get historical barangay data
        from referrals.models import Referral
        from analytics.ml_utils import queryset_to_disease_peak_dataframe
        
        referrals = Referral.objects.filter(
            created_at__year=year,
            created_at__month=month_num
        ).exclude(
            Q(patient__isnull=True) | 
            Q(initial_diagnosis__isnull=True) | 
            Q(initial_diagnosis='')
        ).select_related('patient', 'facility')
        
        if not referrals.exists():
            return JsonResponse({
                "total_cases": 0,
                "barangays": [],
                "month": month,
                "year": year,
                "disease": disease
            })
        
        df = queryset_to_disease_peak_dataframe(referrals)
        df = df[df['ICD10 CODE'] == disease]
        
        if df.empty:
            return JsonResponse({
                "total_cases": 0,
                "barangays": [],
                "month": month,
                "year": year,
                "disease": disease
            })
        
        # Group by barangay
        if 'SITIO/BARANGAY' in df.columns:
            barangay_counts = df.groupby('SITIO/BARANGAY').size().reset_index(name='cases')
        else:
            return JsonResponse({
                "total_cases": 0,
                "barangays": [],
                "month": month,
                "year": year,
                "disease": disease
            })
        
    else:
        # Get predicted barangay data
        from analytics.ml_utils import predict_barangay_disease_peak_2025
        
        barangay_predictions = predict_barangay_disease_peak_2025(use_db=use_db)
        
        if "error" in barangay_predictions:
            return JsonResponse(barangay_predictions, status=400)
        
        barangay_list = []
        for barangay_name, monthly_data in barangay_predictions.items():
            if month_num in monthly_data:
                month_data = monthly_data[month_num]
                if disease in month_data.get('all_diseases', {}):
                    cases = month_data['all_diseases'][disease]
                    barangay_list.append({
                        'SITIO/BARANGAY': barangay_name,
                        'cases': cases
                    })
        
        if not barangay_list:
            return JsonResponse({
                "total_cases": 0,
                "barangays": [],
                "month": month,
                "year": year,
                "disease": disease
            })
        
        barangay_counts = pd.DataFrame(barangay_list)
    
    if barangay_counts.empty:
        return JsonResponse({
            "total_cases": 0,
            "barangays": [],
            "month": month,
            "year": year,
            "disease": disease
        })
    
    total_cases = int(barangay_counts['cases'].sum())
    
    if total_cases == 0:
        return JsonResponse({
            "total_cases": 0,
            "barangays": [],
            "month": month,
            "year": year,
            "disease": disease
        })
    
    # Calculate percentages and sort
    barangay_counts['percentage'] = (barangay_counts['cases'] / total_cases * 100).round(1)
    barangay_counts = barangay_counts.sort_values('cases', ascending=False)
    
    # Format response
    barangays = []
    for _, row in barangay_counts.iterrows():
        barangays.append({
            "name": str(row['SITIO/BARANGAY']),
            "cases": int(row['cases']),
            "percentage": float(row['percentage'])
        })
    
    result = {
        "total_cases": total_cases,
        "barangays": barangays,
        "month": month,
        "year": year,
        "disease": disease
    }
    
    # Cache for 1 hour
    cache.set(cache_key, result, 3600)
    
    return JsonResponse(result)


@login_required
def new_heatmap_view(request):
    """
    View for the new heat index map page using time-series forecasting.
    Displays disease heat index based on the new best-model forecasting approach.
    """
    context = {
        'active_page': 'new_heatmap'
    }
    return render(request, 'analytics/new_heatmap.html', context)


@login_required
def doctor_report(request):
    """
    Doctor-specific report page for generating and previewing reports.
    Similar to user_report but tailored for doctors with only relevant reports.
    """
    # Check if user is a doctor
    if not is_doctor_user(request.user):
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, "Access denied. This page is for doctors only.")
        return redirect('home')
    
    # Get doctor's referral statistics for context
    from datetime import datetime
    current_year = datetime.now().year
    
    # Get doctor's referrals (examined by this doctor)
    doctor_referrals = Referral.objects.filter(examined_by=request.user, created_at__year=current_year)
    total_referrals = doctor_referrals.count()
    completed_referrals = doctor_referrals.filter(status='completed').count()
    
    context = {
        'active_page': 'doctor_report',
        'total_referrals': total_referrals,
        'completed_referrals': completed_referrals,
        'current_year': current_year,
    }
    
    return render(request, 'analytics/doctor_report.html', context)



