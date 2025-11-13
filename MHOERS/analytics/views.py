from django.shortcuts import render
from django.http import JsonResponse
from analytics.models import Disease
from patients.models import Medical_History, Patient
from referrals.models import Referral
from facilities.models import Facility
from accounts.models import BHWRegistration, Doctors, Nurses
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
    """
    year = int(request.GET.get('year', datetime.now().year))    
    view_type = request.GET.get('view_type', 'monthly')

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
                count = referrals_qs.filter(
                    created_at__year=year,
                    created_at__month=month_num,
                ).count()
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
                    count = Referral.objects.filter(
                        patient__facility=facility,
                        created_at__year=year,
                        created_at__month=month_num,
                    ).count()
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
                count = referrals_qs.filter(
                    created_at__year=year_val,
                ).count()
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
                    count = Referral.objects.filter(
                        patient__facility=facility,
                        created_at__year=year_val,
                    ).count()
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
                    Q(nurses__facility=facility)
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

    if request.user.is_staff or request.user.is_superuser:
        # If user_id is provided, filter facilities to those associated with that user
        if user_id:
            facilities_qs = Facility.objects.filter(users__id=user_id).distinct().order_by('name')
        else:
            facilities_qs = Facility.objects.all().order_by('name')
    else:
        facilities_qs = request.user.shared_facilities.all().order_by('name')

    facilities = list(facilities_qs)
    month_labels = [calendar.month_abbr[i] for i in range(1, 13)]

    scorecard = []
    summary_referrals = [0] * 12
    summary_medical = [0] * 12

    for facility in facilities:
        referrals_per_month = []
        medical_per_month = []
        for month_idx in range(1, 13):
            referral_filters = {
                'patient__facility': facility,
                'created_at__year': year,
                'created_at__month': month_idx
            }
            # Filter by user_id if provided
            if user_id:
                referral_filters['user_id'] = user_id
            referral_count = Referral.objects.filter(**referral_filters).count()
            
            medical_filters = {
                'patient_id__facility': facility,
                'diagnosed_date__year': year,
                'diagnosed_date__month': month_idx
            }
            # Filter by user_id if provided
            if user_id:
                medical_filters['user_id'] = user_id
            medical_count = Medical_History.objects.filter(**medical_filters).count()
            referrals_per_month.append(referral_count)
            medical_per_month.append(medical_count)
            summary_referrals[month_idx - 1] += referral_count
            summary_medical[month_idx - 1] += medical_count

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
        'scorecard': scorecard,
        'summary_referrals': summary_referrals,
        'summary_medical': summary_medical,
        'report_generated_at': now,
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
    user_id = parse_int(request.GET.get('user_id'))

    # Build base queryset
    histories = Medical_History.objects.filter(diagnosed_date__year=year)
    if month:
        histories = histories.filter(diagnosed_date__month=month)
    # Filter by user_id if provided (for user-specific reports)
    if user_id:
        histories = histories.filter(user_id=user_id)

    # Normalize illnesses similar to API logic
    disease_names = list(Disease.objects.values_list('name', 'critical_level'))
    disease_name_map = {name.lower(): {'name': name, 'critical_level': level} for name, level in disease_names}

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
        critical_level = disease_info.get('critical_level', 'N/A')
        diagnosis_meta.setdefault(display_name, critical_level)
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
        critical = diagnosis_meta.get(name, 'N/A')
        row_class, badge_variant = classify_level(critical)
        percent = round((count / total_cases) * 100, 2) if total_cases else 0
        top_diagnoses_rows.append({
            'name': name,
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

    # Build list of months from January to December
    month_labels = [calendar.month_abbr[i] for i in range(1, 13)]

    # Ensure each month has counts for top diagnosis entries
    trend_table = []
    for label, _ in top_diagnoses:
        row = {
            'diagnosis': label,
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
    }

    return render(request, 'analytics/morbidity_report.html', context)


@login_required
def facility_workforce_masterlist(request):
    """Printable facility & workforce roster report."""

    now = now_in_singapore()

    facilities = Facility.objects.all().order_by('name')

    roster = []

    bhw_map = defaultdict(list)
    for bhw in BHWRegistration.objects.select_related('facility').all().order_by('last_name'):
        if bhw.facility_id:
            bhw_map[bhw.facility_id].append(bhw)

    doctor_map = defaultdict(list)
    for doctor in Doctors.objects.select_related('facility').all().order_by('last_name'):
        if doctor.facility_id:
            doctor_map[doctor.facility_id].append(doctor)

    nurse_map = defaultdict(list)
    for nurse in Nurses.objects.select_related('facility').all().order_by('last_name'):
        if nurse.facility_id:
            nurse_map[nurse.facility_id].append(nurse)

    for facility in facilities:
        roster.append({
            'facility': facility,
            'bhws': bhw_map.get(facility.pk, []),
            'doctors': doctor_map.get(facility.pk, []),
            'nurses': nurse_map.get(facility.pk, []),
        })

    context = {
        'roster': roster,
        'generated_at': now,
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
    user_id = parse_int(request.GET.get('user_id'))

    month_name = calendar.month_name[month] if month else 'All Months'

    # Determine facilities visible to the current user
    if request.user.is_staff or request.user.is_superuser:
        # If user_id is provided, filter facilities to those associated with that user
        if user_id:
            facilities_qs = Facility.objects.filter(users__id=user_id).distinct().order_by('name')
        else:
            facilities_qs = Facility.objects.all().order_by('name')
    else:
        if hasattr(request.user, 'shared_facilities'):
            facilities_qs = request.user.shared_facilities.all().order_by('name')
        else:
            facilities_qs = Facility.objects.filter(users=request.user).order_by('name')

    facilities = list(facilities_qs)

    status_keys = ['pending', 'in-progress', 'completed', 'cancelled']
    status_labels = {
        'pending': 'Pending',
        'in-progress': 'In-Progress',
        'completed': 'Completed',
        'cancelled': 'Cancelled',
    }
    duration_expr = ExpressionWrapper(F('completed_at') - F('created_at'), output_field=DurationField())

    def duration_to_days(value):
        if not value:
            return None
        return round(value.total_seconds() / 86400, 2)

    facilities_data = []

    for facility in facilities:
        monthly_filters = {
            'patient__facility': facility,
            'created_at__year': year,
        }
        if month:
            monthly_filters['created_at__month'] = month
        # Filter by user_id if provided
        if user_id:
            monthly_filters['user_id'] = user_id

        monthly_qs = Referral.objects.filter(**monthly_filters)

        ytd_filters = {
            'patient__facility': facility,
            'created_at__year': year,
        }
        # Filter by user_id if provided
        if user_id:
            ytd_filters['user_id'] = user_id
        
        ytd_qs = Referral.objects.filter(**ytd_filters)

        monthly_counts = {status: monthly_qs.filter(status=status).count() for status in status_keys}
        ytd_counts = {status: ytd_qs.filter(status=status).count() for status in status_keys}

        monthly_total = sum(monthly_counts.values())
        ytd_total = sum(ytd_counts.values())

        monthly_avg_duration = monthly_qs.filter(status='completed', completed_at__isnull=False).aggregate(
            avg_duration=Avg(duration_expr)
        )['avg_duration']

        ytd_avg_duration = ytd_qs.filter(status='completed', completed_at__isnull=False).aggregate(
            avg_duration=Avg(duration_expr)
        )['avg_duration']

        facilities_data.append({
            'facility': facility,
            'monthly': {
                'counts': monthly_counts,
                'total': monthly_total,
                'avg_days_to_close': duration_to_days(monthly_avg_duration),
            },
            'ytd': {
                'counts': ytd_counts,
                'total': ytd_total,
                'avg_days_to_close': duration_to_days(ytd_avg_duration),
            },
        })

    facility_ids = [f.pk for f in facilities]

    summary_totals = {
        'monthly': {status: 0 for status in status_keys},
        'ytd': {status: 0 for status in status_keys},
    }

    for entry in facilities_data:
        for status in status_keys:
            summary_totals['monthly'][status] += entry['monthly']['counts'][status]
            summary_totals['ytd'][status] += entry['ytd']['counts'][status]

    summary_totals['monthly']['total'] = sum(summary_totals['monthly'][status] for status in status_keys)
    summary_totals['ytd']['total'] = sum(summary_totals['ytd'][status] for status in status_keys)

    # Compute overall averages using combined querysets
    all_monthly_filters = {
        'patient__facility__in': facility_ids,
        'created_at__year': year,
    }
    if month:
        all_monthly_filters['created_at__month'] = month
    # Filter by user_id if provided
    if user_id:
        all_monthly_filters['user_id'] = user_id

    all_monthly_qs = Referral.objects.filter(**all_monthly_filters) if facility_ids else Referral.objects.none()

    all_ytd_filters = {
        'patient__facility__in': facility_ids,
        'created_at__year': year,
    }
    # Filter by user_id if provided
    if user_id:
        all_ytd_filters['user_id'] = user_id
    
    all_ytd_qs = Referral.objects.filter(**all_ytd_filters) if facility_ids else Referral.objects.none()

    summary_totals['monthly']['avg_days_to_close'] = duration_to_days(
        all_monthly_qs.filter(status='completed', completed_at__isnull=False).aggregate(
            avg_duration=Avg(duration_expr)
        )['avg_duration']
    )

    summary_totals['ytd']['avg_days_to_close'] = duration_to_days(
        all_ytd_qs.filter(status='completed', completed_at__isnull=False).aggregate(
            avg_duration=Avg(duration_expr)
        )['avg_duration']
    )

    # Month and year selection helpers
    month_options = [{'value': '', 'label': 'All Months'}]
    month_options.extend({'value': str(idx), 'label': calendar.month_name[idx]} for idx in range(1, 13))

    context = {
        'facilities_data': facilities_data,
        'summary_totals': summary_totals,
        'status_keys': status_keys,
        'status_labels': status_labels,
        'monthly_column_span': len(status_keys) + 2,
        'total_columns': ((len(status_keys) + 2) * 2) + 1,
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
    facility_id = parse_int(request.GET.get('facility_id'))
    status_filter = request.GET.get('status') or ''
    user_id = parse_int(request.GET.get('user_id'))

    # Determine accessible facilities based on user
    if request.user.is_staff or request.user.is_superuser:
        # If user_id is provided, filter facilities to those associated with that user
        if user_id:
            facilities_qs = Facility.objects.filter(users__id=user_id).distinct().order_by('name')
        else:
            facilities_qs = Facility.objects.all().order_by('name')
    else:
        facilities_qs = request.user.shared_facilities.all().order_by('name')

    facilities = list(facilities_qs)

    referrals = Referral.objects.select_related('patient', 'patient__facility', 'user').filter(
        created_at__year=year
    ).order_by('-created_at')

    if month:
        referrals = referrals.filter(created_at__month=month)

    if facility_id:
        referrals = referrals.filter(patient__facility_id=facility_id)

    if status_filter:
        referrals = referrals.filter(status=status_filter)
    
    # Filter by user_id if provided (for user-specific reports)
    if user_id:
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

    month_name = calendar.month_name[month] if month else 'All Months'

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
    }

    return render(request, 'analytics/referral_registry_report.html', context)


@login_required
def get_disease_peak_predictions(request):
    """
    API endpoint to get disease peak predictions for 2025.
    Returns predicted disease peaks for each month.
    Uses caching to avoid regenerating predictions.
    
    Query parameters:
        - month: Optional specific month name (e.g., "January")
        - samples_per_month: Number of samples to simulate (default: 100)
        - use_db: Use Django database instead of CSV (default: false)
    
    Returns:
        JSON response with predictions for each month or error message
    """
    from django.core.cache import cache
    import hashlib
    
    month = request.GET.get('month', None)  # Optional: specific month
    samples_per_month = int(request.GET.get('samples_per_month', 100))
    use_db = request.GET.get('use_db', 'false').lower() == 'true'
    
    # Create cache key based on parameters
    cache_key_parts = ['disease_peak_predictions', str(use_db), str(samples_per_month)]
    if month:
        cache_key_parts.append(month)
    else:
        cache_key_parts.append('all_months')
    cache_key = hashlib.md5('_'.join(cache_key_parts).encode()).hexdigest()
    
    # Check cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        return JsonResponse({
            **cached_result,
            "cached": True
        })
    
    # Generate predictions
    result = predict_disease_peak_for_month(
        month_name=month,
        samples_per_month=samples_per_month,
        use_db=use_db
    )
    
    if "error" in result:
        return JsonResponse(result, status=400)
    
    # Cache predictions for 1 hour
    cache.set(cache_key, result, 3600)  # 1 hour
    
    return JsonResponse(result)


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



