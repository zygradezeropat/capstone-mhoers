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
from analytics.ml_utils import predict_disease_peak_for_month


SINGAPORE_TZ = ZoneInfo('Asia/Singapore')


def now_in_singapore():
    return timezone.now().astimezone(SINGAPORE_TZ)

def get_disease_diagnosis_counts(request):
    """
    API endpoint to return disease diagnosis counts for charting.
    - X-axis: Disease names (from Disease model)
    - Y-axis: Number of diagnoses (from Medical_History.illness_name)
    - Non-matching illness_name are grouped as 'Others'
    - All comparisons are case-insensitive (e.g., 'Flu' = 'fLu')
    - 'cat bite' and 'dog bite' (case-insensitive) are counted as 'Possible Rabies'
    - 'LBM' (case-insensitive) is counted as 'Gastrointestinal Issue'
    """
    
    year = request.GET.get('year')
    month = request.GET.get('month')
    illness_qs = Medical_History.objects.all()
    if year:
        illness_qs = illness_qs.filter(diagnosed_date__year=year)
    if month:
        illness_qs = illness_qs.filter(diagnosed_date__month=month)
    # Get all Disease names (case-insensitive mapping)
    disease_names = list(Disease.objects.values_list('name', flat=True))
    disease_name_map = {name.lower(): name for name in disease_names}
    # Get all illness_name counts
    illness_names = list(illness_qs.values_list('illness_name', flat=True))
    
    # Normalize illness names: map 'cat bite'/'dog bite' to 'Possible Rabies', 'LBM' to 'Gastrointestinal Issue', all lowercased
    normalized = []
    for name in illness_names:
        if name and name.strip().lower() in ["cat bite", "dog bite"]:
            normalized.append("possible rabies")
        elif name and name.strip().lower() == "lbm":
            normalized.append("gastrointestinal issue")
        elif name:
            normalized.append(name.strip().lower())
    illness_counts = Counter(normalized)

    # Prepare data (case-insensitive)
    data = {disease_name_map[k]: 0 for k in disease_name_map}
    possible_rabies_count = 0
    gastrointestinal_issue_count = 0
    others_count = 0
    for illness, count in illness_counts.items():
        if illness == "possible rabies":
            possible_rabies_count += count
        elif illness == "gastrointestinal issue":
            gastrointestinal_issue_count += count
        elif illness in disease_name_map:
            data[disease_name_map[illness]] += count
        else:
            others_count += count
    if possible_rabies_count > 0:
        if "possible rabies" in disease_name_map:
            data[disease_name_map["possible rabies"]] += possible_rabies_count
        else:
            data["Possible Rabies"] = possible_rabies_count
    if gastrointestinal_issue_count > 0:
        if "gastrointestinal issue" in disease_name_map:
            data[disease_name_map["gastrointestinal issue"]] += gastrointestinal_issue_count
        else:
            data["Gastrointestinal Issue"] = gastrointestinal_issue_count
    if others_count > 0:
        data['Others'] = others_count

    # Prepare response
    labels = list(data.keys())
    counts = list(data.values())
    return JsonResponse({
        'labels': labels,
        'counts': counts
    })

def get_monthly_diagnosis_trends(request):
    """
    API endpoint to return monthly diagnosis trends for each disease.
    Returns a dict with:
      - months: list of YYYY-MM (always Jan to Jun of current year)
      - diseases: list of disease names
      - data: {disease_name: [count_per_month, ...]}
    """
    year = request.GET.get('year')
    month = request.GET.get('month')
    now = datetime.now()
    year = int(year) if year else now.year
    if month:
        months = [f"{year}-{'%02d' % int(month)}"]
    else:
        months = [f"{year}-{'%02d' % m}" for m in range(1, 13)]
    # Get all Disease names (case-insensitive mapping)
    disease_names = list(Disease.objects.values_list('name', flat=True))
    disease_name_map = {name.lower(): name for name in disease_names}
    illness_records = Medical_History.objects.all()
    illness_records = illness_records.filter(diagnosed_date__year=year)
    if month:
        illness_records = illness_records.filter(diagnosed_date__month=month)
    illness_records = illness_records.values_list('illness_name', 'diagnosed_date')

    # Prepare data structure
    data = defaultdict(lambda: [0] * len(months))
    for illness, date in illness_records:
        if not illness or not date:
            continue
        # Normalize illness name
        illness_lc = illness.strip().lower()
        if illness_lc in ["cat bite", "dog bite"]:
            illness_lc = "possible rabies"
        elif illness_lc == "lbm":
            illness_lc = "gastrointestinal issue"
        # Get month string
        month_str = date.strftime("%Y-%m")
        if month_str not in months:
            continue  # Only count Jan-Jun of current year
        if illness_lc in disease_name_map:
            disease_label = disease_name_map[illness_lc]
        elif illness_lc == "possible rabies":
            disease_label = disease_name_map.get("possible rabies", "Possible Rabies")
        elif illness_lc == "gastrointestinal issue":
            disease_label = disease_name_map.get("gastrointestinal issue", "Gastrointestinal Issue")
        else:
            disease_label = "Others"
        month_idx = months.index(month_str)
        data[disease_label][month_idx] += 1

    # Ensure all diseases in disease_names are present
    for d in disease_names:
        if d not in data:
            data[d] = [0] * len(months)
    # Ensure 'Possible Rabies', 'Gastrointestinal Issue', 'Others' are present if needed
    for extra in ["Possible Rabies", "Gastrointestinal Issue", "Others"]:
        if extra in data:
            continue
        data[extra] = [0] * len(months)

    return JsonResponse({
        'months': months,
        'diseases': list(data.keys()),
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
    """
    year = int(request.GET.get('year', datetime.now().year))    
    view_type = request.GET.get('view_type', 'monthly')

    if request.user.is_staff:  # or request.user.role == 'MHO'
        facilities = Facility.objects.all()   # compare ALL barangays
    else:
        facilities = request.user.facilities.all()  # only user's barangays


    if not facilities.exists():
        return JsonResponse({'error': 'No facilities linked to this user'}, status=400)

    if view_type == 'monthly':
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

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

    else:  # yearly
        years = [year - 3, year - 2, year - 1, year]
        months = [str(y) for y in years]

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

    # ✅ Return only the current user’s facilities in chart format
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
    Tracks user activity through referrals, medical histories, and other system interactions.
    """
    year = int(request.GET.get('year', datetime.now().year))
    month = request.GET.get('month')
    
    # Get all facilities
    facilities = Facility.objects.all()
    
    # Prepare months data
    if month:
        months = [datetime(year, int(month), 1).strftime('%b')]
        month_nums = [int(month)]
    else:
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        month_nums = list(range(1, 13))
    
    # Initialize data structure
    data = {
        'labels': months,
        'datasets': []
    }
    
    # Colors for different facility types
    colors = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#6f42c1', '#fd7e14', '#20c997']
    
    for idx, facility in enumerate(facilities):
        facility_name = facility.name
        color = colors[idx % len(colors)]
        
        # Track referrals created per month
        referral_data = []
        for month_num in month_nums:
            count = Referral.objects.filter(
                patient__facility=facility,
                created_at__year=year,
                created_at__month=month_num
            ).count()
            referral_data.append(count)
        
        # Track medical histories created per month
        medical_data = []
        for month_num in month_nums:
            count = Medical_History.objects.filter(
                patient__facility=facility,
                diagnosed_date__year=year,
                diagnosed_date__month=month_num
            ).count()
            medical_data.append(count)
        
        # Add referral dataset
        data['datasets'].append({
            'label': f'{facility_name} - Referrals',
            'data': referral_data,
            'borderColor': color,
            'backgroundColor': color + '20',  # Add transparency
            'fill': False,
            'tension': 0.1,
        })
        
        # Add medical history dataset
        data['datasets'].append({
            'label': f'{facility_name} - Medical Records',
            'data': medical_data,
            'borderColor': color,
            'backgroundColor': color + '40',  # Add more transparency
            'fill': False,
            'tension': 0.1,
            'borderDash': [5, 5],  # Dashed line to differentiate
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

    if request.user.is_staff or request.user.is_superuser:
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
            referral_count = Referral.objects.filter(
                patient__facility=facility,
                created_at__year=year,
                created_at__month=month_idx
            ).count()
            medical_count = Medical_History.objects.filter(
                patient_id__facility=facility,
                diagnosed_date__year=year,
                diagnosed_date__month=month_idx
            ).count()
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

    # Build base queryset
    histories = Medical_History.objects.filter(diagnosed_date__year=year)
    if month:
        histories = histories.filter(diagnosed_date__month=month)

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

    month_name = calendar.month_name[month] if month else 'All Months'

    # Determine facilities visible to the current user
    if request.user.is_staff or request.user.is_superuser:
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

        monthly_qs = Referral.objects.filter(**monthly_filters)

        ytd_qs = Referral.objects.filter(
            patient__facility=facility,
            created_at__year=year,
        )

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

    all_monthly_qs = Referral.objects.filter(**all_monthly_filters) if facility_ids else Referral.objects.none()

    all_ytd_qs = Referral.objects.filter(
        patient__facility__in=facility_ids,
        created_at__year=year,
    ) if facility_ids else Referral.objects.none()

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

    # Determine accessible facilities based on user
    if request.user.is_staff or request.user.is_superuser:
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
    
    Query parameters:
        - month: Optional specific month name (e.g., "January")
        - samples_per_month: Number of samples to simulate (default: 100)
        - use_db: Use Django database instead of CSV (default: false)
    
    Returns:
        JSON response with predictions for each month or error message
    """
    month = request.GET.get('month', None)  # Optional: specific month
    samples_per_month = int(request.GET.get('samples_per_month', 100))
    use_db = request.GET.get('use_db', 'false').lower() == 'true'
    
    result = predict_disease_peak_for_month(
        month_name=month,
        samples_per_month=samples_per_month,
        use_db=use_db
    )
    
    if "error" in result:
        return JsonResponse(result, status=400)
    
    return JsonResponse(result)



