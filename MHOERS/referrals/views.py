from django.utils import timezone
from .forms import ReferralForm
from .models import * 
from datetime import datetime
import joblib
from notifications.models import Notification
from facilities.models import Facility
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from patients.models import Patient, Medical_History
from django.http import JsonResponse
from django.http import HttpResponse
from django.utils.text import slugify
from analytics.ml_utils import predict_disease_for_referral, random_forest_regression_train_model, random_forest_regression_prediction_time,  train_random_forest_model_classification
from analytics.model_manager import MLModelManager
from analytics.batch_predictor import BatchPredictor
from .query_optimizer import ReferralQueryOptimizer
from django.db.models import Count
from django.contrib.auth.models import Group, User
from django.db.models.functions import TruncMonth
from django.utils.dateformat import DateFormat
from django.utils.translation import gettext as _
import pandas as pd



@login_required
def get_disease_prediction(request, referral_id):
    prediction = predict_disease_for_referral(referral_id)
    if prediction:
        return JsonResponse({'prediction': prediction})
    else:
        return JsonResponse({'error': 'Referral not found'}, status=404)

@login_required
@never_cache
def assessment(request):
    user = request.user
    patient_id = None  
    selected_patient = None

    # If POST, get patient_id securely
    if request.method == "POST":
        patient_id = request.POST.get("patient_id")

    # If we have a patient_id, try to fetch the patient to preselect in the dropdown
    if patient_id:
        try:
            selected_patient = Patient.objects.get(patients_id=patient_id)
        except Patient.DoesNotExist:
            selected_patient = None

    # Base queryset depending on role
    if user.is_superuser or user.is_staff:
        patients = Patient.objects.all()
    else:
        patients = Patient.objects.filter(user=user)

    return render(request, "assessment/assessment.html", {
        "active_page": "assessment",
        "patients": patients,
        "patient_id": patient_id,  # send selected patient to template
        "selected_patient": selected_patient,
    })

@login_required
@never_cache
def create_referral(request):
    if request.method == 'POST':
        form = ReferralForm(request.POST)
        if form.is_valid():
            patient = form.cleaned_data.get('patient')

            # Prevent duplicate active referrals
            existing_pending = Referral.objects.filter(
                patient=patient,
                status='in-progress'
            ).exists()
            if existing_pending and not request.user.is_staff:
                messages.error(request, "Cannot create new referral. This patient already has an active referral.")
                return redirect('referrals:assessment')

            referral = form.save(commit=False)
            referral.user = request.user  

            # ✅ Different status depending on role
            if request.user.is_staff or request.user.is_superuser:
                referral.status = 'completed'  # Admin auto-completes
            else:
                referral.status = 'in-progress'  # BHW just starts the process

            referral.save()

            # ✅ Notifications
            if request.user.is_staff or request.user.is_superuser:
                # Notify BHW that follow-up is done
                Notification.objects.create(
                    recipient=patient.user,  # assuming patient has a related BHW user
                    title="Follow-up Completed",
                    message=f"Follow up check up for {patient.first_name} {patient.last_name} has been completed by MHO.",
                    referral=referral,
                    is_read=False
                )
            else:
                # Notify all staff that referral is submitted
                staff_users = User.objects.filter(is_staff=True)
                for staff_user in staff_users:
                    Notification.objects.create(
                        recipient=staff_user,
                        title=f'New Referral from {request.user.username}',
                        message=f'Chief Complaint: {referral.chief_complaint}',
                        referral=referral,
                        is_read=False
                    )

            # ✅ Success messages
            if request.user.is_staff or request.user.is_superuser:
                messages.success(request, "Referral completed successfully! The BHW has been notified.")
            else:
                messages.success(request, "Referral submitted successfully! MHO will be notified.")

            return redirect('referrals:assessment')
        else:
            messages.error(request, "Form is invalid.")
    else:   
        form = ReferralForm()

    return render(request, 'assessment/assessment.html', {
        'active_page': 'assessment',
        'form': form
    })


@login_required
def update_referral_status(request):
    referral_id = request.POST.get('referral_id')
    referral = get_object_or_404(Referral, referral_id=referral_id)

    # ✅ Update referral status
    referral.status = 'in-progress'
    referral.save()

    # ✅ Send notification to user (BHW) - they receive referral accepted notifications
    Notification.objects.create(
        recipient=referral.user,
        title='Referral Accepted',
        message=f'Your referral for {referral.patient.first_name} {referral.patient.last_name} is being sent to the MHO.',
        notification_type='referral_accepted',
        referral=referral,
        is_read=False
    )

    # ✅ Use optimized queries
    referrals = list(ReferralQueryOptimizer.get_all_referrals())
    patients = ReferralQueryOptimizer.get_patients_with_referral_count()
    facilities = Facility.objects.all()

    # ✅ Use batch predictions
    predictions = BatchPredictor.predict_all_batch(referrals)

    # ✅ Separate active and completed referrals
    active_referrals = [r for r in referrals if r.status in ['pending', 'in-progress']]
    referred_referrals = [r for r in referrals if r.status == 'completed']

    return render(request, 'patients/admin/patient_list.html', {
        'active_page': 'patient_list',
        'active_tab': 'tab2',
        'facility': facilities,
        'patients': patients,
        'active_referrals': active_referrals,
        'referred_referrals': referred_referrals,
        'predictions': predictions,
    })
    
@login_required
def referred_referral_status(request):  
    if request.method == 'POST':
        referral_id = request.POST.get('referral_id_r')
        mho_note = request.POST.get('editMhoNote')
        mho_advice = request.POST.get('editMhoAdvice')
        mho_findings = request.POST.get('editMhoFindings')
        followup_date_str = request.POST.get('editFollowup')

        # Convert followup date string to datetime object if provided
        followup_date = None
        if followup_date_str:
            try:
                # Convert date string to datetime object (set time to 00:00:00)
                followup_date = datetime.strptime(followup_date_str, '%Y-%m-%d')
            except ValueError:
                followup_date = None

        referral = get_object_or_404(Referral, referral_id=referral_id)
        referral.status = 'completed'
        referral.followup_date = followup_date
        referral.final_diagnosis = mho_findings  # Save findings to final_diagnosis field
        referral.completed_at = timezone.now()
        referral.save()

        # ✅ Send notification to user (BHW) - they receive referral completed notifications
        Notification.objects.create(
            recipient=referral.user,
            title='Referral Completed',
            message=f'Your referral for {referral.patient.first_name} {referral.patient.last_name} has been completed by MHO.',
            notification_type='referral_completed',
            referral=referral,
            is_read=False
        )

        if mho_note:
            Medical_History.objects.create(
                user_id=referral.patient.user,
                patient_id=referral.patient,
                illness_name=mho_findings,
                diagnosed_date=timezone.now().date(),
                notes=mho_note,
                advice=mho_advice,
                followup_date=followup_date
            )

    # Use optimized queries
    referrals = list(ReferralQueryOptimizer.get_all_referrals())
    patients = ReferralQueryOptimizer.get_patients_with_referral_count()
    facilities = Facility.objects.all()

    # Use batch predictions
    predictions = BatchPredictor.predict_all_batch(referrals)

    # Separate active and completed referrals
    active_referrals = [r for r in referrals if r.status in ['pending', 'in-progress']]
    referred_referrals = [r for r in referrals if r.status == 'completed']

    return render(request, 'patients/admin/patient_list.html', {
        'active_page': 'patient_list',
        'active_tab': 'tab3',
        'facility': facilities,
        'patients': patients,
        'active_referrals': active_referrals,
        'referred_referrals': referred_referrals,
        'predictions': predictions,
    })

@login_required
def reject_referral(request):
        return render()

@login_required
def delete_referral(request):
    if request.method == 'POST':
        referral_id = request.POST.get('referral_del')
        # Retrieve the referral to be deleted
        referral = get_object_or_404(Referral, referral_id=referral_id)
        
        # Delete the referral
        referral.delete()

        # After deletion, retrieve the updated lists
        active_referrals = Referral.objects.filter(status='in-progress')
        referred_referrals = Referral.objects.filter(status='completed')
        patients = Patient.objects.all()
        messages.success(request, "Referral deleted successfully!")

        # Render the updated list in the template
        return render(request, 'patients/admin/patient_list.html', {
            'active_referrals': active_referrals,
            'referred_referrals': referred_referrals,
            'patients': patients,
            'active_page': 'patient_list',
        })    

@login_required
@never_cache
def referral_list(request):
    user = request.user
    # Get patients associated with the current user
    patients = Patient.objects.filter(user=user)

    # Filter referrals by patient user and status with optimized queries
    active_referrals = Referral.objects.filter(patient__user=user, status='in-progress').select_related('patient', 'patient__facility')
    referred_referrals = Referral.objects.filter(patient__user=user, status='completed').select_related('patient', 'patient__facility')

    # Combine referrals for batch prediction
    all_referrals = list(active_referrals) + list(referred_referrals)
    
    # Use batch predictions
    predictions = BatchPredictor.predict_all_batch(all_referrals)

    return render(request, 'patients/user/referral_list.html', {
        'active_page': 'referral_list',
        'patients': patients,
        'active_referrals': active_referrals,
        'referred_referrals': referred_referrals,
        'predictions': predictions,
    })

@login_required 
@never_cache
def admin_patient_list(request):
    # Step 1: Ensure models are loaded (only once)
    MLModelManager.train_models_if_needed()
    
    # Step 2: Use optimized queries
    referrals = list(ReferralQueryOptimizer.get_all_referrals())
    patients = ReferralQueryOptimizer.get_patients_with_referral_count()
    facilities = Facility.objects.all()
    
    # Step 3: Batch predictions (cached)
    predictions = BatchPredictor.predict_all_batch(referrals)
    
    # Step 4: Separate active and completed referrals
    active_referrals = [r for r in referrals if r.status in ['pending', 'in-progress']]
    referred_referrals = [r for r in referrals if r.status == 'completed']
    
    return render(request, 'patients/admin/patient_list.html', {
        'active_page': 'patient_list',
        'active_tab': 'tab1',
        'facility': facilities,
        'patients': patients,
        'active_referrals': active_referrals,
        'referred_referrals': referred_referrals,
        'predictions': predictions,
        'training_result': {"status": "Models loaded from cache"},
    })
    
    
@login_required
def get_patient_referral_history(request, patient_id):
    try:
        print(f"🔍 Fetching referral history for patient ID: {patient_id}")
        print(f"🔍 Patient ID type: {type(patient_id)}")
        
        # Get all referrals for the patient, ordered by most recent first
        referrals = Referral.objects.filter(patient_id=patient_id).order_by('-created_at')
        print(f"🔍 Found {referrals.count()} referrals for patient {patient_id}")
        
        # Get ALL medical history records for this patient
        from patients.models import Medical_History
        all_medical_history = Medical_History.objects.filter(patient_id=patient_id).order_by('-diagnosed_date')
        print(f"🔍 Found {all_medical_history.count()} medical history records for patient {patient_id}")
        
        # Convert to list of dictionaries for JSON response
        referral_list = []
        for referral in referrals:
            referral_data = {
                'referral_id': referral.referral_id,
                'status': referral.status,
                'created_at': referral.created_at.isoformat(),
                'chief_complaint': referral.chief_complaint,
                'symptoms': referral.symptoms,
                'work_up_details': referral.work_up_details,
                'bp_systolic': referral.bp_systolic,
                'bp_diastolic': referral.bp_diastolic,
                'pulse_rate': referral.pulse_rate,
                'respiratory_rate': referral.respiratory_rate,
                'temperature': float(referral.temperature),
                'oxygen_saturation': referral.oxygen_saturation,
                'weight': float(referral.weight),
                'height': float(referral.height)
            }
            
            # Find the most relevant medical history for THIS specific referral
            # Get medical history that is directly linked to this referral
            relevant_medical_history = Medical_History.objects.filter(
                referral=referral
            ).first()
            
            # If no direct link, fall back to date-based matching
            if not relevant_medical_history:
                relevant_medical_history = all_medical_history.filter(
                    diagnosed_date__lte=referral.created_at.date()
                ).first()
            
            # Add medical history data if available
            if relevant_medical_history:
                referral_data['illness_name'] = relevant_medical_history.illness_name
                referral_data['diagnosed_date'] = relevant_medical_history.diagnosed_date.isoformat()
                referral_data['notes'] = relevant_medical_history.notes
                referral_data['advice'] = relevant_medical_history.advice
                print(f"🔍 Referral #{referral.referral_id} matched with illness: {relevant_medical_history.illness_name}")
            else:
                referral_data['illness_name'] = None
                referral_data['diagnosed_date'] = None
                referral_data['notes'] = None
                referral_data['advice'] = None
                print(f"🔍 Referral #{referral.referral_id} has no matching medical history")
            
            referral_list.append(referral_data)
        
        print(f"🔍 Returning {len(referral_list)} referrals with matched medical history")
        return JsonResponse({'referrals': referral_list})
    except Exception as e:
        print(f"❌ Error in get_patient_referral_history: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def test_view(request):
    """Simple test view to verify routing"""
    return JsonResponse({'message': 'Test view working!', 'timestamp': 'now'})

@login_required
@never_cache
def referral_counts_by_user(request):
    # Aggregate referral counts grouped by user.username
    referral_stats = (
        Referral.objects.values('user__username')
        .annotate(count=Count('referral_id'))
        .order_by('-count')
    )
    labels = [entry['user__username'] for entry in referral_stats]
    data = [entry['count'] for entry in referral_stats]
    return JsonResponse({'labels': labels, 'data': data})

@login_required
@never_cache
def monthly_referral_counts_by_user(request):
    import calendar
    from django.db.models.functions import TruncMonth
    from django.utils.dateformat import DateFormat

    year_param = request.GET.get('year')
    qs = Referral.objects.all()

    # Default to current year if year is not given
    from datetime import datetime
    year_int = datetime.now().year
    if year_param:
        try:
            year_int = int(year_param)
            qs = qs.filter(created_at__year=year_int)
        except ValueError:
            qs = qs.filter(created_at__year=year_int)
    else:
        qs = qs.filter(created_at__year=year_int)

    # Full list of 12 months (Jan–Dec)
    all_months = list(range(1, 13))
    month_labels = [calendar.month_abbr[m] for m in all_months]  # ['Jan','Feb',...]

    # Get all users with at least one referral in this year
    users = qs.values_list('user__username', flat=True).distinct()

    # Colors for datasets
    palette = [
        '#5c3dff', '#ff918e', '#ff57d1', '#ffb457', 
        '#4bc0c0', '#36a2eb', '#9966ff', '#ff6384', '#c9cbcf'
    ]

    datasets = []
    for idx, username in enumerate(users):
        # Count referrals for each month (fill 0 if none)
        counts = [
            qs.filter(user__username=username, created_at__month=m).count()
            for m in all_months
        ]
        datasets.append({
            'label': username,
            'data': counts,
            'backgroundColor': palette[idx % len(palette)],
            'borderColor': palette[idx % len(palette)],
            'fill': False,
            'tension': 0.3,   # smooth line if line chart
            'pointRadius': 4,
            'pointHoverRadius': 6,
        })

    return JsonResponse({'labels': month_labels, 'datasets': datasets})

@login_required
@never_cache
def yearly_referral_counts_by_user(request):
    import datetime
    from django.db.models.functions import TruncYear
    from django.utils.dateformat import DateFormat

    current_year = datetime.date.today().year
    # Last 4 years (including current)
    all_years = list(range(current_year - 3, current_year + 1))
    year_labels = [str(y) for y in all_years]

    qs = Referral.objects.all()

    # Get all users with at least one referral across these years
    users = qs.values_list('user__username', flat=True).distinct()

    palette = [
        '#5c3dff', '#ff918e', '#ff57d1', '#ffb457',
        '#4bc0c0', '#36a2eb', '#9966ff', '#ff6384', '#c9cbcf'
    ]

    datasets = []
    for idx, username in enumerate(users):
        # Count referrals for each year (fill with 0 if none)
        counts = [
            qs.filter(user__username=username, created_at__year=y).count()
            for y in all_years
        ]
        datasets.append({
            'label': username,
            'data': counts,
            'backgroundColor': palette[idx % len(palette)],
            'borderColor': palette[idx % len(palette)],
            'fill': False,
            'tension': 0.3,
            'pointRadius': 4,
            'pointHoverRadius': 6,
        })

    return JsonResponse({'labels': year_labels, 'datasets': datasets})

    datasets = []
    for idx, username in enumerate(users):
        counts = [
            qs.filter(user__username=username, created_at__year=y.year).count()
            for y in years
        ]
        datasets.append({
            'label': username,
            'data': counts,
            'backgroundColor': palette[idx % len(palette)],
            'borderRadius': 10,
            'barThickness': 20,
            'stack': 'Stack 0',
        })
    return JsonResponse({'labels': year_labels, 'datasets': datasets})


@login_required
@never_cache
def export_referrals_csv(request):
    """Export referrals as CSV filtered by optional year, month, facility_id, or user_id.

    Query params:
      - year: int (e.g., 2025)
      - month: int (1-12)
      - facility_id: int (maps to Facility.user_id for referrals.user)
      - user_id: int (referrals.user id)
    """
    # Base queryset
    qs = Referral.objects.select_related('user', 'patient').all()

    # Filters from query params
    year = request.GET.get('year')
    month = request.GET.get('month')
    facility_id = request.GET.get('facility_id')
    user_id = request.GET.get('user_id')

    # Apply temporal filters
    if year and year.isdigit():
        qs = qs.filter(created_at__year=int(year))
    if month and month.isdigit():
        qs = qs.filter(created_at__month=int(month))

    # Apply facility filter by mapping to user
    if facility_id and facility_id.isdigit():
        try:
            facility = Facility.objects.get(facility_id=int(facility_id))
            qs = qs.filter(user_id=facility.user_id_id)
        except Facility.DoesNotExist:
            qs = qs.none()

    # Apply user filter directly
    if user_id and user_id.isdigit():
        qs = qs.filter(user_id=int(user_id))

    # Prepare CSV response
    response = HttpResponse(content_type='text/csv')

    # Build a friendly filename based on filters
    friendly_suffix = None
    if facility_id and facility_id.isdigit():
        try:
            fobj = Facility.objects.get(facility_id=int(facility_id))
            # Prefer facility name; fall back to assigned_bhw
            base_name = fobj.name or fobj.assigned_bhw or f"facility_{facility_id}"
            friendly_suffix = slugify(base_name)
        except Facility.DoesNotExist:
            pass
    elif user_id and user_id.isdigit():
        try:
            from django.contrib.auth.models import User
            uobj = User.objects.get(id=int(user_id))
            base_name = uobj.username or f"user_{user_id}"
            friendly_suffix = slugify(base_name)
        except User.DoesNotExist:
            pass

    # Include year/month if specified
    date_suffix = None
    if year and year.isdigit():
        if month and month.isdigit():
            date_suffix = f"{year}-{int(month):02d}"
        else:
            date_suffix = f"{year}"

    parts = ["referrals", friendly_suffix, date_suffix]
    filename = '_'.join([p for p in parts if p]) or 'referrals'
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'

    import csv
    writer = csv.writer(response)
    # Header
    writer.writerow([
        'referral_id', 'created_at', 'status',
        'user_id', 'username',
        'patient_id', 'patient_name',
        'chief_complaint', 'initial_diagnosis', 'final_diagnosis',
        'bp_systolic', 'bp_diastolic', 'pulse_rate', 'respiratory_rate',
        'temperature', 'oxygen_saturation', 'weight', 'height'
    ])

    # Rows
    for r in qs.order_by('created_at'):
        patient_name = f"{r.patient.first_name} {r.patient.last_name}" if hasattr(r.patient, 'first_name') else str(r.patient_id)
        writer.writerow([
            r.referral_id,
            r.created_at.isoformat(),
            r.status,
            r.user_id,
            r.user.username if r.user_id else '',
            r.patient_id,
            patient_name,
            r.chief_complaint,
            r.initial_diagnosis,
            r.final_diagnosis or '',
            r.bp_systolic,
            r.bp_diastolic,
            r.pulse_rate,
            r.respiratory_rate,
            float(r.temperature),
            r.oxygen_saturation,
            float(r.weight),
            float(r.height),
        ])

    return response


@login_required
@never_cache
def api_referrals(request):
    """Return referrals as JSON filtered by optional year, month, and user_id.
    """
    qs = Referral.objects.select_related('user', 'patient').all()
    year = request.GET.get('year')
    month = request.GET.get('month')
    user_id = request.GET.get('user_id')

    if year and year.isdigit():
        qs = qs.filter(created_at__year=int(year))
    if month and month.isdigit():
        qs = qs.filter(created_at__month=int(month))
    if user_id and user_id.isdigit():
        qs = qs.filter(user_id=int(user_id))

    # Build facility name map for users present in queryset
    user_ids = list(qs.values_list('user_id', flat=True).distinct())
    facility_map = {
        f.user_id_id: f.name
        for f in Facility.objects.filter(user_id_id__in=user_ids)
    }

    data = []
    for r in qs.order_by('-created_at'):
        data.append({
            'referral_id': r.referral_id,
            'created_at': r.created_at.isoformat(),
            'status': r.status,
            'user_id': r.user_id,
            'username': r.user.username if r.user_id else '',
            'facility_name': facility_map.get(r.user_id, ''),
            'patient_id': r.patient_id,
            'patient': f"{getattr(r.patient, 'first_name', '')} {getattr(r.patient, 'last_name', '')}".strip(),
            'chief_complaint': r.chief_complaint,
            'initial_diagnosis': r.initial_diagnosis,
        })
    return JsonResponse({'results': data})

