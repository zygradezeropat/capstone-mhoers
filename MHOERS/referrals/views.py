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
from analytics.ml_utils import predict_disease_for_referral, random_forest_regression_train_model, random_forest_regression_prediction_time,  train_random_forest_model_classification
from analytics.model_manager import MLModelManager
from analytics.batch_predictor import BatchPredictor
from .query_optimizer import ReferralQueryOptimizer
from django.db.models import Count
from django.contrib.auth.models import Group
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
    # Get the logged-in user
    user = request.user
    
    # Filter the patients by the logged-in user's ID
    patients = Patient.objects.filter(user=user)
    
    # Pass the filtered patients to the template
    return render(request, 'assessment/assessment.html', {
        'active_page': 'assessment', 
        'patients': patients
    })

@login_required
@never_cache
def create_referral(request):
    if request.method == 'POST':
        form = ReferralForm(request.POST)
        if form.is_valid():
            # Check if there's already a pending referral for this patient
            patient = form.cleaned_data.get('patient')
            existing_pending = Referral.objects.filter(
                patient=patient,
                status='in-progress'
            ).exists()
            
            if existing_pending:
                messages.error(request, "Cannot create new referral. This patient already has a active referral.")
                return redirect('referrals:assessment')
                
            referral = form.save(commit=False)
            referral.user = request.user  # Set the user (BHW) who is creating the referral
            referral.status = 'in-progress'  # Set status to in-progress instead of pending
            referral.save()

            # Get all MHO users
            mho_group = Group.objects.get(name='MHO')
            mho_users = mho_group.user_set.all()

            # Create notifications for all MHO users
            Notification.objects.create(
                recipient=request.user,
                title=f'New Referral from {request.user.username}',
                message=f'Chief Complaint: {referral.chief_complaint}',
                referral=referral,
                is_read=False
                )

            # Display success message and redirect to the assessment page
            messages.success(request, "Referral submitted successfully! MHO will be notified.")
            return redirect('referrals:assessment')
        else:
            messages.error(request, "Form is invalid.")
            print("❌ Form is invalid")
            print(form.errors)
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

    # ✅ Send notification
    Notification.objects.create(
        recipient=referral.user,
        title='Referral Accepted',
        message=f'Your referral for {referral.patient.first_name} {referral.patient.last_name} is being sent to the MHO.',
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
        referral.completed_at = timezone.now()
        referral.save()

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
        # Get all referrals for the patient, ordered by most recent first
        referrals = Referral.objects.filter(patient_id=patient_id).order_by('-created_at')
        
        # Convert to list of dictionaries for JSON response
        referral_list = []
        for referral in referrals:
            referral_list.append({
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
            })
        
        return JsonResponse({'referrals': referral_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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
    # Get all months present in the data
    from collections import OrderedDict
    import calendar
    # Get all months in the year with at least one referral
    months = (
        Referral.objects.annotate(month=TruncMonth('created_at'))
        .values_list('month', flat=True)
        .distinct()
        .order_by('month')
    )
    # Format months as 'Jan', 'Feb', ...
    month_labels = [DateFormat(m).format('M') for m in months]
    # Get all users with at least one referral
    users = Referral.objects.values_list('user__username', flat=True).distinct()
    # Assign a color for each user (fallback to a default palette)
    palette = [
        '#5c3dff', '#ff918e', '#ff57d1', '#ffb457', '#4bc0c0', '#36a2eb', '#9966ff', '#ff6384', '#c9cbcf'
    ]
    datasets = []
    for idx, username in enumerate(users):
        # Get referral counts for this user per month
        counts = [
            Referral.objects.filter(user__username=username, created_at__month=m.month, created_at__year=m.year).count()
            for m in months
        ]
        datasets.append({
            'label': username,
            'data': counts,
            'backgroundColor': palette[idx % len(palette)],
            'borderRadius': 10,
            'barThickness': 20,
            'stack': 'Stack 0',
        })
    return JsonResponse({'labels': month_labels, 'datasets': datasets})


