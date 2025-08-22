from django.shortcuts import render
from django.http import JsonResponse
from analytics.models import Disease
from patients.models import Medical_History
from collections import Counter, defaultdict
from datetime import datetime
from .models import *

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




