from django.shortcuts import render
from django.http import JsonResponse
from analytics.models import Disease
from patients.models import Medical_History, Patient
from referrals.models import Referral
from facilities.models import Facility
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from django.db.models import Count, Q
from .models import *
from django.contrib.auth.models import User

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




