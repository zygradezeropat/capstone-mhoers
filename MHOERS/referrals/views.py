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

    # ✅ Re-query updated data
    active_referrals = Referral.objects.filter(status='in-progress')
    referred_referrals = Referral.objects.filter(status='completed')
    patients = Patient.objects.all()
    facilities = Facility.objects.all()

    # ✅ Load model/vectorizer once
    try:
        model = joblib.load('ml_models/time_rf_model.pkl')
        vectorizer = joblib.load('ml_models/symptom_vectorizer.pkl')
    except Exception as e:
        model = None
        vectorizer = None

    # ✅ Generate predictions
    predictions = {}
    for r in active_referrals | referred_referrals:
        try:
            disease_pred = predict_disease_for_referral(r.referral_id)
            time_pred = random_forest_regression_prediction_time(r, model=model, vectorizer=vectorizer)
        except Exception as e:
            disease_pred = "Error"
            time_pred = "Error"
        predictions[r.referral_id] = (disease_pred, time_pred)

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

    # Re-query updated data
    active_referrals = Referral.objects.filter(status='in-progress')
    referred_referrals = Referral.objects.filter(status='completed')
    patients = Patient.objects.all()
    facilities = Facility.objects.all()

    # Load trained model/vectorizer once
    try:
        model = joblib.load('ml_models/time_rf_model.pkl')
        vectorizer = joblib.load('ml_models/symptom_vectorizer.pkl')
    except Exception as e:
        model, vectorizer = None, None

    # Predict disease and time
    predictions = {}
    for r in active_referrals | referred_referrals :
        try:
            disease_pred = predict_disease_for_referral(r.referral_id)
            time_pred = random_forest_regression_prediction_time(r, model=model, vectorizer=vectorizer)
        except Exception as e:
            disease_pred = "Error"
            time_pred = "Error"
        predictions[r.referral_id] = (disease_pred, time_pred)

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

    # Filter referrals by patient user and status
    active_referrals = Referral.objects.filter(patient__user=user, status='in-progress')
    referred_referrals = Referral.objects.filter(patient__user=user, status='completed')

    # Load trained model and vectorizer (once)
    try:
        model = joblib.load('ml_models/time_rf_model.pkl')
        vectorizer = joblib.load('ml_models/symptom_vectorizer.pkl')
    except Exception as e:
        model = None
        vectorizer = None

    # Run predictions
    predictions = {}
    for r in active_referrals | referred_referrals:
        try:
            disease_pred = predict_disease_for_referral(r.referral_id)
            time_pred = random_forest_regression_prediction_time(r, model=model, vectorizer=vectorizer)
        except Exception as e:
            disease_pred = "Error"
            time_pred = "Error"
        predictions[r.referral_id] = (disease_pred, time_pred)

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
    # Optional retrain
    train_random_forest_model_classification()
    training_result = random_forest_regression_train_model()
    if "error" in training_result:
        training_result = {"status": "Model already trained"}

    # Load models once
    disease_model = joblib.load('ml_models/disease_rf_model.pkl')
    disease_vectorizer = joblib.load('ml_models/disease_vectorizer.pkl')
    time_model = joblib.load('ml_models/time_rf_model.pkl')
    time_vectorizer = joblib.load('ml_models/symptom_vectorizer.pkl')

    # Get referrals
    referrals = list(Referral.objects.filter(
        status__in=['pending', 'in-progress', 'completed', 'rejected']
    ).select_related('patient'))

    # Predict diseases
    symptom_texts = [r.symptoms or "" for r in referrals]
    disease_vectors = disease_vectorizer.transform(symptom_texts)
    disease_preds = disease_model.predict(disease_vectors)

    # Prepare data for time prediction
    numeric_data = []
    text_data = []
    for r in referrals:
        try:
            numeric_data.append({
                'weight': float(r.weight),
                'height': float(r.height),
                'bp_systolic': r.bp_systolic,
                'bp_diastolic': r.bp_diastolic,
                'pulse_rate': r.pulse_rate,
                'respiratory_rate': r.respiratory_rate,
                'temperature': float(r.temperature),
                'oxygen_saturation': r.oxygen_saturation
            })
            text_data.append(r.symptoms or '')
        except:
            numeric_data.append(None)
            text_data.append("")

    valid_indexes = [i for i, data in enumerate(numeric_data) if data]
    X_numeric = pd.DataFrame([numeric_data[i] for i in valid_indexes])
    X_text = time_vectorizer.transform([text_data[i] for i in valid_indexes]).toarray()
    X_combined = pd.concat([X_numeric.reset_index(drop=True), pd.DataFrame(X_text)], axis=1)
    X_combined.columns = X_combined.columns.astype(str)
    time_preds = time_model.predict(X_combined)

    # Combine predictions
    predictions = {}
    time_idx = 0
    for i, r in enumerate(referrals):
        disease = disease_preds[i]
        if i in valid_indexes:
            time_pred = round(float(time_preds[time_idx]), 2)
            time_idx += 1
        else:
            time_pred = "N/A"
        predictions[r.referral_id] = (disease, time_pred)

    # Patients and other data
    patients = Patient.objects.annotate(referral_count=Count('referral'))
    patientsFat = Patient.objects.select_related('facility').all()
    facility = Facility.objects.all()

    return render(request, 'patients/admin/patient_list.html', {
        'active_page': 'patient_list',
        'active_tab': 'tab1',
        'facility': facility,
        'patients': patients,
        'active_referrals': [r for r in referrals if r.status == 'in-progress'],
        'referred_referrals': [r for r in referrals if r.status == 'completed'],
        'patientFat': patientsFat,
        'predictions': predictions,
        'training_result': training_result,
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


