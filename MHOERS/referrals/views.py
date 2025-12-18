from django.utils import timezone
from .forms import ReferralForm
from .models import * 
from datetime import datetime, timedelta
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
from django.core.paginator import Paginator
from analytics.ml_utils import predict_disease_for_referral, random_forest_regression_train_model, random_forest_regression_prediction_time,  train_random_forest_model_classification, predict_time_to_cater_advanced, train_time_prediction_model_advanced, train_time_prediction_model_advanced_from_csv
from analytics.model_manager import MLModelManager
from analytics.batch_predictor import BatchPredictor
from .query_optimizer import ReferralQueryOptimizer
from django.db.models import Count, Q, OuterRef, Subquery
from django.contrib.auth.models import Group, User
from django.db.models.functions import TruncMonth
from django.utils.dateformat import DateFormat
from django.utils.translation import gettext as _
import pandas as pd
from accounts.models import Doctors
from analytics.models import Disease


def get_severity_order(referral_id, predictions_dict):
    """
    Get severity order value for sorting (lower = higher priority).
    Returns: 0=High, 1=Medium, 2=Low, 3=Unspecified
    """
    if not referral_id or referral_id not in predictions_dict:
        return 3  # Unspecified
    
    prediction = predictions_dict[referral_id]
    disease_code = prediction[0] if isinstance(prediction, tuple) else prediction
    
    if not disease_code or (isinstance(disease_code, str) and ('No prediction' in disease_code or 'Unspecified' in disease_code)):
        return 3  # Unspecified
    
    # Try to get Disease from database
    try:
        disease = Disease.objects.get(icd_code=str(disease_code).strip())
        severity = disease.critical_level.lower()
        if severity == 'high':
            return 0
        elif severity == 'medium':
            return 1
        elif severity == 'low':
            return 2
    except Disease.DoesNotExist:
        # Try alternative formats
        try:
            alt_code = str(disease_code).strip().replace('.', '-')
            if alt_code != str(disease_code).strip():
                disease = Disease.objects.get(icd_code=alt_code)
                severity = disease.critical_level.lower()
                if severity == 'high':
                    return 0
                elif severity == 'medium':
                    return 1
                elif severity == 'low':
                    return 2
        except Disease.DoesNotExist:
            try:
                alt_code = str(disease_code).strip().replace('-', '.')
                if alt_code != str(disease_code).strip():
                    disease = Disease.objects.get(icd_code=alt_code)
                    severity = disease.critical_level.lower()
                    if severity == 'high':
                        return 0
                    elif severity == 'medium':
                        return 1
                    elif severity == 'low':
                        return 2
            except Disease.DoesNotExist:
                pass
    
    return 3  # Unspecified


@login_required
def search_diseases(request):
    """API endpoint to search diseases by ICD code or name"""
    query = request.GET.get('q', '').strip()
    
    # If no query, return all diseases (limited to 50 for performance)
    if not query:
        diseases = Disease.objects.all().order_by('name')[:50]
    else:
        # Search by ICD code or name
        diseases = Disease.objects.filter(
            Q(icd_code__icontains=query) | Q(name__icontains=query)
        ).order_by('name')[:10]  # Limit to 10 results for search
    
    results = [{
        'id': d.id,
        'name': d.name,
        'icd_code': d.icd_code,
        'description': d.description,
        'common_symptoms': d.common_symptoms or 'Not specified',
        'treatment_protocol': d.treatment_protocol or 'Not specified',
        'critical_level': d.critical_level,
    } for d in diseases]
    
    return JsonResponse({'diseases': results})


@login_required
def get_disease_details(request, disease_id):
    """Get full disease details for verification"""
    try:
        disease = Disease.objects.get(id=disease_id)
        return JsonResponse({
            'id': disease.id,
            'name': disease.name,
            'icd_code': disease.icd_code,
            'description': disease.description,
            'common_symptoms': disease.common_symptoms or 'Not specified',
            'treatment_protocol': disease.treatment_protocol or 'Not specified',
            'treatment_guidelines': disease.treatment_guidelines or 'Not specified',
            'critical_level': disease.critical_level,
            'verified_by': disease.verified_by.get_full_name() if disease.verified_by else 'Not verified',
            'verified_at': disease.verified_at.strftime('%Y-%m-%d') if disease.verified_at else None,
        })
    except Disease.DoesNotExist:
        return JsonResponse({'error': 'Disease not found'}, status=404)


@login_required
def get_disease_prediction(request, referral_id):
    prediction = predict_disease_for_referral(referral_id)
    if prediction:
        return JsonResponse({'prediction': prediction})
    else:
        return JsonResponse({'error': 'Referral not found'}, status=404)

@login_required
def get_time_prediction_advanced(request, referral_id):
    """API endpoint for advanced time-to-cater prediction"""
    prediction = predict_time_to_cater_advanced(referral_id)
    if isinstance(prediction, (int, float)):
        return JsonResponse({
            'prediction': prediction, 
            'unit': 'hours',
            'prediction_minutes': round(prediction * 60, 1)
        })
    else:
        return JsonResponse({'error': prediction}, status=400)

@login_required
def train_time_model_advanced(request):
    """API endpoint to train advanced time prediction model"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    result = train_time_prediction_model_advanced()
    return JsonResponse(result)

@login_required
@never_cache
def assessment(request):
    facility = request.user.shared_facilities.first()
    user = request.user
    patient_id = None  
    selected_patient = None
    latest_referral = None
    medical_history_id = None
    is_followup = False
    previous_medical_history = None

    # Get patient_id from either POST (form submission) or GET (redirect from add patient)
    if request.method == "POST":
        patient_id = request.POST.get("patient_id")
        medical_history_id = request.POST.get("medical_history_id")
        is_followup = request.POST.get("is_followup") == "true"
    else:
        # GET request - check for patient_id in query parameters (from redirect after adding patient)
        patient_id = request.GET.get("patient_id")
        medical_history_id = request.GET.get("medical_history_id")
        is_followup = request.GET.get("is_followup") == "true"

    # If we have a patient_id, try to fetch the patient to preselect in the dropdown
    if patient_id:
        try:
            selected_patient = Patient.objects.get(patients_id=patient_id)
            # Get the latest referral for this patient to populate form fields
            latest_referral = Referral.objects.filter(
                patient=selected_patient
            ).order_by('-created_at').first()
            
            # If it's a follow-up referral, get the previous medical history
            if is_followup and medical_history_id:
                try:
                    previous_medical_history = Medical_History.objects.get(history_id=medical_history_id)
                except Medical_History.DoesNotExist:
                    previous_medical_history = None
        except Patient.DoesNotExist:
            selected_patient = None

    # Base queryset depending on role - show patients from shared facilities
    if user.is_superuser or user.is_staff:
        patients = Patient.objects.all()
    else:
        # Get patients from facilities shared by the user
        user_facilities = user.shared_facilities.all()
        patients = Patient.objects.filter(facility__in=user_facilities)
    
    # Load barangays for dropdown in add patient modal
    from facilities.models import Barangay
    barangays = Barangay.objects.filter(is_active=True).order_by('name')

    return render(request, "assessment/assessment.html", {
        "active_page": "assessment",
        "patients": patients,
        "patient_id": patient_id,  # send selected patient to template
        "selected_patient": selected_patient,
        "latest_referral": latest_referral,  # send latest referral data
        "medical_history_id": medical_history_id,
        "is_followup": is_followup,
        "previous_medical_history": previous_medical_history,
        "facility": facility,
        "barangays": barangays,
    })

@login_required
def get_latest_referral(request, patient_id):
    """Get the latest referral data for a patient to populate form fields"""
    try:
        patient = get_object_or_404(Patient, patients_id=patient_id)
        latest_referral = Referral.objects.filter(
            patient=patient
        ).order_by('-created_at').first()
        
        if latest_referral:
            return JsonResponse({
                'success': True,
                'referral': {
                    'is_smoker': latest_referral.is_smoker,
                    'smoking_sticks_per_day': latest_referral.smoking_sticks_per_day,
                    'is_alcoholic': latest_referral.is_alcoholic,
                    'alcohol_bottles_per_year': latest_referral.alcohol_bottles_per_year,
                    'family_planning': latest_referral.family_planning,
                    'family_planning_type': latest_referral.family_planning_type,
                    'examined_by': latest_referral.examined_by.id if latest_referral.examined_by else None,
                    'menarche': latest_referral.menarche,
                    'sexually_active': latest_referral.sexually_active,
                    'number_of_partners': latest_referral.number_of_partners,
                    'is_menopause': latest_referral.is_menopause,
                    'menopause_age': latest_referral.menopause_age,
                    'last_menstrual_period': latest_referral.last_menstrual_period.strftime('%Y-%m-%d') if latest_referral.last_menstrual_period else None,
                    'period_duration': latest_referral.period_duration,
                    'period_interval': latest_referral.period_interval,
                    'pads_per_day': latest_referral.pads_per_day,
                    # Pregnancy History fields
                    'is_pregnant': latest_referral.is_pregnant,
                    'gravidity': latest_referral.gravidity,
                    'parity': latest_referral.parity,
                    'delivery_type': latest_referral.delivery_type,
                    'full_term_births': latest_referral.full_term_births,
                    'premature_births': latest_referral.premature_births,
                    'abortions': latest_referral.abortions,
                    'living_children': latest_referral.living_children,
                }
            })
        else:
            return JsonResponse({
                'success': True,
                'referral': None
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def check_pending_referral(request, patient_id):
    """Check if a patient has a pending or in-progress referral"""
    try:
        patient = get_object_or_404(Patient, patients_id=patient_id)
        
        # Check for pending or in-progress referrals
        pending_referral = Referral.objects.filter(
            patient=patient,
            status__in=['pending', 'in-progress']
        ).first()
        
        if pending_referral:
            return JsonResponse({
                'success': True,
                'has_pending': True,
                'referral_id': pending_referral.referral_id,
                'status': pending_referral.status,
                'created_at': pending_referral.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            return JsonResponse({
                'success': True,
                'has_pending': False
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def create_referral(request):
    if request.method == 'POST':
        from django.core.cache import cache
        from django.db import transaction
        
        # Get submission ID FIRST and check cache immediately
        submission_id = request.POST.get('submission_id')
        if submission_id:
            cache_key = f'referral_submission_{submission_id}'
            # Use add() which is atomic - only sets if key doesn't exist
            # Returns True if key was added, False if it already existed
            cache_added = cache.add(cache_key, True, 10)  # Cache for 10 seconds
            if not cache_added:
                # Key already exists - this is a duplicate
                print(f"⚠️ Duplicate submission ID detected: {submission_id}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Duplicate submission detected'}, status=400)
                messages.warning(request, "This referral was already submitted.")
                return redirect('referrals:assessment')
            print(f"✅ Marked submission {submission_id} as processing")
        
        # Get patient ID from POST data to check for duplicates
        patient_id = request.POST.get('patient')
        
        # CRITICAL: Check for duplicate submissions using database lock
        if patient_id:
            try:
                with transaction.atomic():
                    # Use select_for_update to lock and check for very recent referral (within last 2 seconds)
                    recent_referral = Referral.objects.filter(
                        patient_id=patient_id,
                        user=request.user,
                        created_at__gte=timezone.now() - timedelta(seconds=2)
                    ).select_for_update().first()
                    
                    if recent_referral:
                        print(f"⚠️ Duplicate submission blocked: Patient {patient_id}, User {request.user.username}, Recent Referral ID: {recent_referral.referral_id}")
                        # Remove from cache since we're rejecting it
                        if submission_id:
                            cache.delete(cache_key)
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'success': False, 'error': 'Duplicate submission detected. Please wait a moment.'}, status=400)
                        messages.warning(request, "This referral was just submitted. Please wait a moment.")
                        return redirect('referrals:assessment')
            except Exception as e:
                print(f"Error checking for duplicates: {e}")
                # Remove from cache on error
                if submission_id:
                    cache.delete(cache_key)
        
        form = ReferralForm(request.POST)
        if form.is_valid():
            patient = form.cleaned_data.get('patient')

            # 🔍 Check for duplicate active referrals
            existing_pending = Referral.objects.filter(
                patient=patient,
                status__in=['pending', 'in-progress']
            ).exists()

            if existing_pending and not request.user.is_staff:
                messages.error(request, "Cannot create new referral. This patient already has an active referral.")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Patient already has an active referral'}, status=400)
                return redirect('referrals:assessment')
            
            # 🔍 Additional check: Prevent rapid duplicate submissions (within last 5 seconds)
            recent_referral = Referral.objects.filter(
                patient=patient,
                user=request.user,
                created_at__gte=timezone.now() - timedelta(seconds=5)
            ).exists()
            
            if recent_referral:
                messages.warning(request, "A referral was just created. Please wait a moment before creating another.")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'A referral was just created. Please wait a moment.'}, status=400)
                return redirect('referrals:assessment')

            # CRITICAL: Final duplicate check RIGHT BEFORE saving with database lock
            # Use a database transaction with proper locking to prevent race conditions
            try:
                with transaction.atomic():
                    # Get the patient object and lock it to prevent concurrent modifications
                    locked_patient = Patient.objects.select_for_update().get(pk=patient.pk)
                    
                    # Check for very recent referral (within last 1 second) - most aggressive check
                    final_check = Referral.objects.filter(
                        patient=locked_patient,
                        user=request.user,
                        created_at__gte=timezone.now() - timedelta(seconds=1)
                    ).first()
                    
                    if final_check:
                        print(f"🚫 BLOCKED: Duplicate detected right before save - Referral ID: {final_check.referral_id}")
                        # Remove from cache since we're rejecting
                        if submission_id:
                            cache.delete(cache_key)
                        
                        return redirect('referrals:assessment')
                    
                    referral = form.save(commit=False)
                    referral.user = request.user  
                    
                    # Save examined_by if provided (doctor who performed the check-up)
                    examined_by_id = request.POST.get('examined_by', '')
                    if examined_by_id:
                        try:
                            # Try to get User by ID first (if doctor has user linked)
                            examined_by_user = User.objects.filter(id=int(examined_by_id)).first()
                            if examined_by_user:
                                referral.examined_by = examined_by_user
                            else:
                                # If not found as User, try to get doctor and use their user
                                from accounts.models import Doctors
                                doctor = Doctors.objects.filter(doctor_id=int(examined_by_id)).first()
                                if doctor and doctor.user:
                                    referral.examined_by = doctor.user
                        except (ValueError, TypeError):
                            pass

                    # ✅ Automatically assign the facility
                    # Check both shared_facilities and BHWRegistration for facility assignment
                    user_facility = request.user.shared_facilities.first()  # gets the first linked facility
                    
                    # If no facility from shared_facilities, check if user is BHW and get facility from BHWRegistration
                    if not user_facility:
                        try:
                            from accounts.models import BHWRegistration
                            bhw_profile = BHWRegistration.objects.select_related('facility').get(user=request.user)
                            if bhw_profile.facility:
                                user_facility = bhw_profile.facility
                        except BHWRegistration.DoesNotExist:
                            pass
                    
                    if user_facility:
                        referral.facility = user_facility
                    else:
                        messages.error(request, "You are not assigned to any facility. Contact admin.")
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'success': False, 'error': 'You are not assigned to any facility'}, status=400)
                        return redirect('referrals:assessment')

                    # ✅ Set referral status based on user role
                    if request.user.is_staff or request.user.is_superuser:
                        referral.status = 'completed'
                    else:
                        referral.status = 'pending'  # BHW referrals start as pending, doctors can choose to accept them
                    
                    # ✅ If this is a follow-up referral, set referral type
                    medical_history_id = request.POST.get('medical_history_id')
                    is_followup = request.POST.get('is_followup') == 'true'
                    if is_followup:
                        referral.referral_type = 'Follow-up'
                        # Link to previous medical history if provided
                        if medical_history_id:
                            try:
                                previous_medical_history = Medical_History.objects.get(history_id=medical_history_id)
                                # You can add additional logic here if needed
                            except Medical_History.DoesNotExist:
                                pass

                    # Save within the transaction - this is atomic
                    referral.save()
            except Exception as e:
                print(f"❌ Error in transaction: {e}")
                # Remove from cache on error
                if submission_id:
                    cache.delete(cache_key)
                raise

            # ✅ Save to Medical History
            # Determine illness name - prioritize: disease name > initial_diagnosis > chief complaint
            illness_name = referral.chief_complaint
            if referral.disease:
                illness_name = referral.disease.name
            elif referral.initial_diagnosis and referral.initial_diagnosis.strip():
                illness_name = referral.initial_diagnosis
            # Truncate if too long for the field
            if len(illness_name) > 255:
                illness_name = illness_name[:252] + "..."
            
            # Combine symptoms and work_up_details for notes
            notes_parts = []
            if referral.symptoms:
                notes_parts.append(f"Symptoms: {referral.symptoms}")
            if referral.work_up_details:
                notes_parts.append(f"Work-up Details: {referral.work_up_details}")
            if referral.chief_complaint and not referral.disease:
                notes_parts.append(f"Chief Complaint: {referral.chief_complaint}")
            notes = "\n\n".join(notes_parts) if notes_parts else "Referral created."
            
            # Combine remarks and treatments for advice
            advice_parts = []
            if referral.treatments:
                advice_parts.append(f"Treatments: {referral.treatments}")
            if referral.remarks:
                advice_parts.append(f"Remarks: {referral.remarks}")
            advice = "\n\n".join(advice_parts) if advice_parts else "Follow referral instructions."
            
            # Create Medical History entry
            Medical_History.objects.create(
                user_id=referral.user,
                patient_id=referral.patient,
                illness_name=illness_name,
                diagnosed_date=referral.created_at.date(),
                notes=notes,
                advice=advice,
                followup_date=referral.followup_date,
                referral=referral
            )

            # ✅ Notifications
            if request.user.is_staff or request.user.is_superuser:
                # Notify the BHW assigned to that facility
                assigned_bhw_username = referral.facility.assigned_bhw
                bhw_user = User.objects.filter(username=assigned_bhw_username).first()
                if bhw_user:
                    Notification.objects.create(
                        recipient=bhw_user,
                        title="Follow-up Completed",
                        message=f"Follow-up for {patient.first_name} {patient.last_name} has been completed by MHO.",
                        referral=referral,
                        is_read=False
                    )
            else:
                # Notify MHO staff users
                staff_users = User.objects.filter(is_staff=True)
                facility_name = referral.facility.name if referral.facility and referral.facility.name else 'Facility'
                for staff_user in staff_users:
                    # Prevent duplicate notifications
                    Notification.objects.get_or_create(
                        recipient=staff_user,
                        referral=referral,
                        notification_type='referral_sent',
                        defaults={
                            'title': f'New Referral from {request.user.username}',
                            'message': f'Chief Complaint: {referral.chief_complaint}',
                            'is_read': False
                        }
                    )
                
                # Also notify all active doctors
                from accounts.models import Doctors
                active_doctors = Doctors.objects.filter(
                    status='ACTIVE',
                    user__isnull=False
                ).select_related('user')
                for doctor in active_doctors:
                    if doctor.user:  # Ensure user exists
                        # Prevent duplicate notifications and use correct message format
                        Notification.objects.get_or_create(
                            recipient=doctor.user,
                            referral=referral,
                            notification_type='referral_sent',
                            defaults={
                                'title': f'From "{facility_name}"',
                                'message': referral.chief_complaint,
                                'is_read': False
                            }
                        )

            # Mark submission ID as processed AFTER successful save (prevent duplicates)
            if submission_id:
                from django.core.cache import cache
                cache_key = f'referral_submission_{submission_id}'
                cache.set(cache_key, True, 10)  # Cache for 10 seconds
            
            # ✅ Feedback
            if request.user.is_staff or request.user.is_superuser:
                messages.success(request, "Referral completed successfully! The BHW has been notified.")
            else:
                messages.success(request, "Referral submitted successfully! MHO will be notified.")

            # Return JSON response for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Referral submitted successfully!',
                    'referral_id': referral.referral_id
                })
            
            return redirect('referrals:assessment')
        else:
            messages.error(request, "Form is invalid.")
    else:
        form = ReferralForm()

    # Get all doctors for dropdown (will filter in template to only show those with users)
    approved_doctors = Doctors.objects.all().order_by('last_name', 'first_name')
    
    return render(request, 'assessment/assessment.html', {
        'active_page': 'assessment',
        'form': form,
        'doctors': approved_doctors,
    })


@login_required
def update_referral_status(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    referral_id = request.POST.get('referral_id')
    if not referral_id:
        return JsonResponse({'success': False, 'error': 'Referral ID is required'}, status=400)
    
    referral = get_object_or_404(Referral, referral_id=referral_id)
    
    # ✅ Check if referral is already accepted by another doctor
    if referral.status == 'in-progress' and referral.examined_by:
        if referral.examined_by != request.user:
            return JsonResponse({
                'success': False, 
                'error': 'This referral has already been accepted by another doctor.'
            }, status=400)
        else:
            # Already accepted by this user, return success without doing anything
            return JsonResponse({
                'success': True,
                'message': 'Referral already accepted by you.',
                'referral_id': referral.referral_id,
                'patient_name': f"{referral.patient.first_name} {referral.patient.last_name}"
            })
    
    # ✅ Check if referral is already completed
    if referral.status == 'completed':
        return JsonResponse({
            'success': False, 
            'error': 'This referral has already been completed.'
        }, status=400)

    # ✅ Update referral status
    referral.status = 'in-progress'
    
    # ✅ If user is a doctor, set them as the examiner
    from accounts.models import Doctors
    try:
        doctor_profile = Doctors.objects.get(user=request.user)
        if doctor_profile.status == 'ACTIVE':
            referral.examined_by = request.user
    except Doctors.DoesNotExist:
        pass  # Not a doctor, keep existing examined_by or leave as None
    
    referral.save()

    # ✅ Send notification to user (BHW) - they receive referral accepted notifications
    Notification.objects.create(
        recipient=referral.user,
        title='Referral Accepted',
        message=f'Your referral for {referral.patient.first_name} {referral.patient.last_name} has been accepted by Dr. {request.user.get_full_name() or request.user.username}.',
        notification_type='referral_accepted',
        referral=referral,
        is_read=False
    )

    # ✅ Always return JSON response for AJAX requests
    # Check multiple ways to detect AJAX requests
    is_ajax = (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
        'application/json' in request.headers.get('Accept', '') or
        request.content_type == 'application/json' or
        request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    )
    
    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': 'Referral accepted successfully!',
            'referral_id': referral.referral_id,
            'patient_name': f"{referral.patient.first_name} {referral.patient.last_name}"
        })
    
    # ✅ For non-AJAX requests (fallback), redirect appropriately
    from django.contrib import messages
    messages.success(request, 'Referral accepted successfully!')
    
    try:
        doctor_profile = Doctors.objects.get(user=request.user)
        if doctor_profile.status == 'ACTIVE':
            return redirect('doctor_dashboard')
    except Doctors.DoesNotExist:
        pass  # Not a doctor, redirect to patient list
    
    # Default redirect to patient list
    return redirect('referrals:patient_list')
    
@login_required
def referred_referral_status(request):  
    if request.method == 'POST':
        try:
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
            
            # NEW: Handle findings from merged dropdown
            # Check for new findings_select field (merged Findings dropdown)
            findings_select = request.POST.get('findings_select')
            if findings_select:
                if findings_select == 'other':
                    # "Other" option selected - use findings_other input
                    findings_other = request.POST.get('findings_other', '').strip()
                    if findings_other:
                        referral.final_diagnosis = findings_other
                        # No disease or ICD code for "Other"
                        referral.disease = None
                        referral.ICD_code = ''
                        referral.disease_verified = False
                else:
                    # Disease selected from dropdown
                    try:
                        disease = Disease.objects.get(id=findings_select)
                        referral.disease = disease
                        referral.ICD_code = disease.icd_code  # Auto-fill ICD code from disease
                        referral.disease_verified = request.POST.get('disease_verified') == 'on'
                        # Use disease name as findings if mho_findings is empty
                        if not mho_findings:
                            referral.final_diagnosis = disease.name
                    except Disease.DoesNotExist:
                        # If disease not found, use findings text
                        referral.disease = None
                        referral.ICD_code = ''
                        referral.disease_verified = False
            else:
                # Fallback to old method for backward compatibility
                disease_id = request.POST.get('disease')
                if disease_id:
                    try:
                        disease = Disease.objects.get(id=disease_id)
                        referral.disease = disease
                        referral.ICD_code = disease.icd_code  # Auto-fill ICD code from disease
                        referral.disease_verified = request.POST.get('disease_verified') == 'on'
                    except Disease.DoesNotExist:
                        # If disease not found, just save manual ICD code
                        referral.ICD_code = request.POST.get('editIcdCode', '')
                else:
                    # Manual ICD code entry (old method)
                    referral.ICD_code = request.POST.get('editIcdCode', '')
                    referral.disease_verified = False
            
            # Save Lifestyle/Social History fields
            referral.is_smoker = request.POST.get('editIsSmoker') == 'on'
            smoking_sticks = request.POST.get('editSmokingSticks', '')
            referral.smoking_sticks_per_day = int(smoking_sticks) if smoking_sticks else None
            referral.is_alcoholic = request.POST.get('editIsAlcoholic') == 'on'
            alcohol_bottles = request.POST.get('editAlcoholBottles', '')
            referral.alcohol_bottles_per_year = int(alcohol_bottles) if alcohol_bottles else None
            referral.family_planning = request.POST.get('editFamilyPlanning') == 'on'
            referral.family_planning_type = request.POST.get('editFamilyPlanningType', '')
            
            # Save examined_by (doctor who performed the check-up)
            examined_by_id = request.POST.get('examined_by', '')
            if examined_by_id:
                try:
                    # Try to get User by ID first (if doctor has user linked)
                    examined_by_user = User.objects.filter(id=int(examined_by_id)).first()
                    if examined_by_user:
                        referral.examined_by = examined_by_user
                    else:
                        # If not found as User, try to get doctor and use their user
                        doctor = Doctors.objects.filter(doctor_id=int(examined_by_id)).first()
                        if doctor and doctor.user:
                            referral.examined_by = doctor.user
                except (ValueError, TypeError):
                    pass
            
            # Save Menstrual History fields
            menarche_val = request.POST.get('editMenarche', '')
            referral.menarche = int(menarche_val) if menarche_val else None
            referral.sexually_active = request.POST.get('editSexuallyActive') == 'on'
            partners_val = request.POST.get('editNumberOfPartners', '')
            referral.number_of_partners = int(partners_val) if partners_val else None
            referral.is_menopause = request.POST.get('editIsMenopause') == 'on'
            menopause_age_val = request.POST.get('editMenopauseAge', '')
            referral.menopause_age = int(menopause_age_val) if menopause_age_val else None
            lmp_str = request.POST.get('editLastMenstrualPeriod', '')
            if lmp_str:
                try:
                    referral.last_menstrual_period = datetime.strptime(lmp_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
            period_duration_val = request.POST.get('editPeriodDuration', '')
            referral.period_duration = int(period_duration_val) if period_duration_val else None
            period_interval_val = request.POST.get('editPeriodInterval', '')
            referral.period_interval = int(period_interval_val) if period_interval_val else None
            pads_val = request.POST.get('editPadsPerDay', '')
            referral.pads_per_day = int(pads_val) if pads_val else None
            
            # Save Pregnancy History fields
            referral.is_pregnant = request.POST.get('editIsPregnant') == 'on'
            gravidity_val = request.POST.get('editGravidity', '')
            referral.gravidity = int(gravidity_val) if gravidity_val else None
            parity_val = request.POST.get('editParity', '')
            referral.parity = int(parity_val) if parity_val else None
            referral.delivery_type = request.POST.get('editDeliveryType', '')
            full_term_val = request.POST.get('editFullTermBirths', '')
            referral.full_term_births = int(full_term_val) if full_term_val else None
            premature_val = request.POST.get('editPrematureBirths', '')
            referral.premature_births = int(premature_val) if premature_val else None
            abortions_val = request.POST.get('editAbortions', '')
            referral.abortions = int(abortions_val) if abortions_val else None
            living_children_val = request.POST.get('editLivingChildren', '')
            referral.living_children = int(living_children_val) if living_children_val else None
            
            referral.save()

            # ✅ Send notification to user (BHW) - they receive referral completed notifications
            # Get doctor name from examined_by
            doctor_name = 'MHO'
            if referral.examined_by:
                doctor_name = referral.examined_by.get_full_name() or referral.examined_by.username
                # Try to get doctor title if available
                try:
                    from accounts.models import Doctors
                    doctor_profile = Doctors.objects.get(user=referral.examined_by)
                    if doctor_profile:
                        doctor_name = f"Dr. {doctor_profile.first_name} {doctor_profile.last_name}".strip() or doctor_name
                except Doctors.DoesNotExist:
                    pass
            
            patient_full_name = f"{referral.patient.first_name} {referral.patient.last_name}"
            
            # Prevent duplicate notifications
            Notification.objects.get_or_create(
                recipient=referral.user,
                referral=referral,
                notification_type='referral_completed',
                defaults={
                    'title': 'Referral Completed',
                    'message': f'Referral Completed: Your Referral Request for "{patient_full_name}" has been completed by "{doctor_name}"',
                    'is_read': False
                }
            )

            # Check if Medical_History already exists for this referral
            existing_medical_history = Medical_History.objects.filter(referral=referral).first()
            
            if mho_note:
                if existing_medical_history:
                    # Update existing Medical_History record instead of creating a duplicate
                    existing_medical_history.illness_name = mho_findings or existing_medical_history.illness_name
                    existing_medical_history.notes = mho_note
                    existing_medical_history.advice = mho_advice or existing_medical_history.advice
                    if followup_date:
                        existing_medical_history.followup_date = followup_date
                    existing_medical_history.save()
                else:
                    # Create new Medical_History only if it doesn't exist
                    Medical_History.objects.create(
                        user_id=referral.user,  # Changed from referral.patient.user
                        patient_id=referral.patient,
                        illness_name=mho_findings,
                        diagnosed_date=timezone.now().date(),
                        notes=mho_note,
                        advice=mho_advice,
                        followup_date=followup_date,
                        referral=referral  # Link to the referral to prevent duplicates
                    )
            elif followup_date:
                if existing_medical_history:
                    # If only followup_date is set (no mho_note), update the existing record's followup_date
                    existing_medical_history.followup_date = followup_date
                    existing_medical_history.save()
                else:
                    # If no existing Medical_History, create one with just the follow-up date
                    # This ensures the follow-up date is properly tracked
                    Medical_History.objects.create(
                        user_id=referral.user,
                        patient_id=referral.patient,
                        illness_name=referral.final_diagnosis or referral.initial_diagnosis or referral.chief_complaint or 'Follow-up',
                        diagnosed_date=timezone.now().date(),
                        notes='',
                        advice='',
                        followup_date=followup_date,
                        referral=referral
                    )

            # Return JSON response for AJAX requests
            return JsonResponse({'success': True, 'message': 'Referral completed successfully'})
            
        except Exception as e:
            # Log the error for debugging
            import traceback
            print(f"Error in referred_referral_status: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    # If not POST or if there's an issue, return error
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

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
        active_referrals = Referral.objects.filter(status__in=['pending', 'in-progress'])
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
    # Get user's assigned facilities - check both shared_facilities and BHWRegistration
    user_facilities = list(request.user.shared_facilities.all())
    
    # Also check if user is a BHW and get facility from BHWRegistration
    try:
        from accounts.models import BHWRegistration
        bhw_profile = BHWRegistration.objects.select_related('facility').get(user=request.user)
        if bhw_profile.facility and bhw_profile.facility not in user_facilities:
            user_facilities.append(bhw_profile.facility)
    except BHWRegistration.DoesNotExist:
        pass
    
    has_facilities = len(user_facilities) > 0
    
    # Get facility IDs for filtering (empty list if no facilities)
    facility_ids = [f.facility_id for f in user_facilities] if has_facilities else []
    
    # Build query to include:
    # 1. Referrals from user's assigned facilities (facility or patient facility match)
    # 2. Referrals created by the current user (so users can see their own referrals)
    # Priority: Always show referrals created by the user, regardless of facility matching
    user_created_filter = Q(user=request.user)
    
    if has_facilities:
        facility_filter = Q(facility_id__in=facility_ids) | Q(patient__facility_id__in=facility_ids)
        # Include referrals created by current user OR matching facilities
        # Using distinct() to avoid duplicates if a referral matches both conditions
        combined_filter = facility_filter | user_created_filter
    else:
        # If no facilities assigned, only show referrals created by the user
        combined_filter = user_created_filter
    
    # Filter pending referrals - always include user's own referrals
    # Prefetch medical_history to get notes for Doctor Notes/Actions
    pending_qs = Referral.objects.filter(
        combined_filter,
        status='pending'
    ).select_related('patient', 'patient__facility', 'patient__user').prefetch_related('medical_history').distinct().order_by('-created_at')

    # Filter active referrals (in-progress) - always include user's own referrals
    # Prefetch medical_history to get notes for Doctor Notes/Actions
    active_qs = Referral.objects.filter(
        combined_filter,
        status='in-progress'
    ).select_related('patient', 'patient__facility', 'patient__user').prefetch_related('medical_history').distinct().order_by('-created_at')

    # Filter referred/completed referrals - always include user's own referrals
    # Prefetch medical_history to get notes for Doctor Notes/Actions
    referred_qs = Referral.objects.filter(
        combined_filter,
        status='completed'
    ).select_related('patient', 'patient__facility', 'patient__user').prefetch_related('medical_history').distinct().order_by('-completed_at', '-created_at')
    
    # Debug: Log query results for troubleshooting
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"User: {request.user.username}, Has facilities: {has_facilities}")
    logger.debug(f"Active referrals count: {active_qs.count()}")
    logger.debug(f"Referred referrals count: {referred_qs.count()}")
    # Also check all referrals created by this user
    all_user_referrals = Referral.objects.filter(user=request.user)
    logger.debug(f"Total referrals created by user: {all_user_referrals.count()}")
    for ref in all_user_referrals[:5]:  # Log first 5
        logger.debug(f"  - Referral {ref.referral_id}: status={ref.status}, facility={ref.facility}, patient_facility={ref.patient.facility if ref.patient else None}")
    
    # Filter patients to only show those handled by the current user
    # A patient is "handled" if:
    # 1. User created a referral for them (Referral.user = request.user), OR
    # 2. User examined them (Referral.examined_by = request.user), OR
    # 3. User recorded a follow-up visit for them (FollowUpVisit.user = request.user), OR
    # 4. User created medical history for them (Medical_History.user_id = request.user)
    from referrals.models import FollowUpVisit
    
    # Get patient IDs from referrals created by user
    patients_from_user_referrals = Referral.objects.filter(
        user=request.user
    ).values_list('patient_id', flat=True).distinct()
    
    # Get patient IDs from referrals examined by user
    patients_from_user_examinations = Referral.objects.filter(
        examined_by=request.user
    ).values_list('patient_id', flat=True).distinct()
    
    # Get patient IDs from follow-up visits recorded by user
    patients_from_user_followups = FollowUpVisit.objects.filter(
        user=request.user
    ).values_list('patient_id', flat=True).distinct()
    
    # Get patient IDs from medical history created by user
    patients_from_user_medical_history = Medical_History.objects.filter(
        user_id=request.user
    ).values_list('patient_id', flat=True).distinct()
    
    # Combine all patient IDs
    handled_patient_ids = set(patients_from_user_referrals) | set(patients_from_user_examinations) | set(patients_from_user_followups) | set(patients_from_user_medical_history)
    
    if handled_patient_ids:
        # Get all patients handled by the user
        latest_referral_subquery = Referral.objects.filter(
            patient=OuterRef('pk')
        ).order_by('-created_at')
        
        patients_qs = Patient.objects.filter(
            patients_id__in=handled_patient_ids
        ).annotate(
            referral_count=Count('referral'),
            latest_referral_id=Subquery(latest_referral_subquery.values('referral_id')[:1]),
            latest_referral_date=Subquery(latest_referral_subquery.values('created_at')[:1]),
        ).order_by('first_name', 'last_name')
        
        # Filter medical history to only patients handled by user
        medical_history_qs = Medical_History.objects.filter(
            patient_id__in=handled_patient_ids
        )
    else:
        patients_qs = Patient.objects.none()
        medical_history_qs = Medical_History.objects.none()

    # Get total counts for badges
    pending_count = pending_qs.count()
    active_count = active_qs.count()
    referred_count = referred_qs.count()
    patients_count = patients_qs.count()
    medical_history_count = medical_history_qs.count()

    # Prepare follow-ups data similar to admin dashboard
    # Filter to only show follow-ups for patients handled by the user
    followups_list = []
    followups_count = 0
    
    # Check if user is a doctor
    is_doctor = False
    try:
        from accounts.models import Doctors
        doctor_profile = Doctors.objects.get(user=request.user)
        if doctor_profile.status == 'ACTIVE':
            is_doctor = True
    except Doctors.DoesNotExist:
        pass
    
    if handled_patient_ids:
        followups_qs = medical_history_qs.filter(
            followup_date__isnull=False
        ).select_related('patient_id', 'patient_id__facility', 'user_id', 'referral', 'referral__examined_by').order_by('-followup_date')
        
        # Doctors can see all follow-ups (no filter needed)

        today = datetime.now().date()
        completed_medical_history_ids = set(
            FollowUpVisit.objects.filter(
                status='completed',
                medical_history__in=followups_qs
            ).values_list('medical_history_id', flat=True)
        )

        for followup in followups_qs:
            has_completed_visit = followup.history_id in completed_medical_history_ids

            if followup.followup_date < today:
                status = 'overdue'
            elif followup.followup_date == today:
                status = 'today'
            else:
                status = 'upcoming'

            if has_completed_visit:
                status = 'completed'
            else:
                followups_count += 1

            followups_list.append({
                'medical_history': followup,
                'status': status,
                'patient_name': f"{followup.patient_id.first_name} {followup.patient_id.last_name}",
                'patient_id': followup.patient_id.patients_id,
                'followup_date': followup.followup_date,
                'illness_name': followup.illness_name,
                'notes': followup.notes,
                'advice': followup.advice,
            })

    # Get predictions for all referrals before pagination to sort by severity
    all_pending = list(pending_qs)
    all_active = list(active_qs)
    all_referred = list(referred_qs)
    
    all_referrals_for_prediction = all_pending + all_active + all_referred
    predictions = BatchPredictor.predict_all_batch(all_referrals_for_prediction) if all_referrals_for_prediction else {}
    
    # Sort by severity: High (0) -> Medium (1) -> Low (2) -> Unspecified (3), then by created_at descending
    def sort_key(referral):
        severity_order = get_severity_order(referral.referral_id, predictions)
        return (severity_order, -referral.created_at.timestamp() if referral.created_at else 0)
    
    all_pending.sort(key=sort_key)
    all_active.sort(key=sort_key)
    
    # For referred, keep original sorting (by completed_at/created_at)
    # but we can optionally sort by severity too if needed
    
    pending_page_number = request.GET.get('pending_page') or 1
    active_page_number = request.GET.get('active_page') or 1
    referred_page_number = request.GET.get('referred_page') or 1

    pending_page = Paginator(all_pending, 10).get_page(pending_page_number)
    active_page = Paginator(all_active, 10).get_page(active_page_number)
    referred_page = Paginator(referred_qs, 10).get_page(referred_page_number)

    # Add medical_history notes and advice to each referral for template access
    # Use direct database queries with referral_id instead of referral object to ensure data is retrieved
    import logging
    logger = logging.getLogger(__name__)
    
    for referral in pending_page.object_list:
        # STEP 1: Get referral_id from referrals_referral table (Referral model)
        referral_id_from_referrals = referral.referral_id
        
        # STEP 2: Query patients_medical_history table to find matching referral_id
        # This compares: Medical_History.referral_id == Referral.referral_id
        matching_medical_history = Medical_History.objects.filter(
            referral_id=referral_id_from_referrals  # Compare with referral_id from referrals_referral
        ).order_by('-diagnosed_date').first()
        
        # STEP 3: Verify if the comparison found a match (legit)
        if matching_medical_history:
            # STEP 3a: Get referral_id from patients_medical_history table to verify
            referral_id_from_medical_history = matching_medical_history.referral_id if hasattr(matching_medical_history, 'referral_id') else (
                matching_medical_history.referral.referral_id if matching_medical_history.referral else None
            )
            
            # STEP 3b: Compare both referral_ids
            if referral_id_from_medical_history == referral_id_from_referrals:
                # STEP 4: Pull notes and advice from patients_medical_history
                notes_from_db = matching_medical_history.notes
                advice_from_db = matching_medical_history.advice
                
                # STEP 5: Populate the form (set on referral object for template)
                referral.medical_history_notes = notes_from_db if (notes_from_db and notes_from_db.strip()) else None
                referral.medical_history_advice = advice_from_db if (advice_from_db and advice_from_db.strip()) else None
                
                logger.debug(f"  ✅ Pending Referral {referral.referral_id}: Found and populated medical_history")
            else:
                referral.medical_history_notes = None
                referral.medical_history_advice = None
                logger.debug(f"  ❌ Pending Referral {referral.referral_id}: referral_id mismatch")
        else:
            referral.medical_history_notes = None
            referral.medical_history_advice = None
            logger.debug(f"  ❌ Pending Referral {referral.referral_id}: No medical_history found")
    
    for referral in active_page.object_list:
        # STEP 1: Get referral_id from referrals_referral table (Referral model)
        referral_id_from_referrals = referral.referral_id
        
        # STEP 2: Query patients_medical_history table to find matching referral_id
        matching_medical_history = Medical_History.objects.filter(
            referral_id=referral_id_from_referrals
        ).order_by('-diagnosed_date').first()
        
        # STEP 3: Verify if the comparison found a match (legit)
        if matching_medical_history:
            referral_id_from_medical_history = matching_medical_history.referral_id if hasattr(matching_medical_history, 'referral_id') else (
                matching_medical_history.referral.referral_id if matching_medical_history.referral else None
            )
            
            if referral_id_from_medical_history == referral_id_from_referrals:
                # STEP 4-5: Pull and populate
                notes_from_db = matching_medical_history.notes
                advice_from_db = matching_medical_history.advice
                
                referral.medical_history_notes = notes_from_db if (notes_from_db and notes_from_db.strip()) else None
                referral.medical_history_advice = advice_from_db if (advice_from_db and advice_from_db.strip()) else None
                
                logger.debug(f"  ✅ Active Referral {referral.referral_id}: Found and populated medical_history")
            else:
                referral.medical_history_notes = None
                referral.medical_history_advice = None
        else:
            referral.medical_history_notes = None
            referral.medical_history_advice = None
            logger.debug(f"  ❌ Active Referral {referral.referral_id}: No medical_history found")
    
    for referral in referred_page.object_list:
        # STEP 1: Get referral_id from referrals_referral table (Referral model)
        referral_id_from_referrals = referral.referral_id
        print(f"🔍 STEP 1: Got referral_id from referrals_referral table: {referral_id_from_referrals}")
        
        # STEP 2: Query patients_medical_history table to find matching referral_id
        # This compares: Medical_History.referral_id == Referral.referral_id
        matching_medical_history = Medical_History.objects.filter(
            referral_id=referral_id_from_referrals  # Compare with referral_id from referrals_referral
        ).order_by('-diagnosed_date').first()
        
        # STEP 3: Verify if the comparison found a match (legit)
        if matching_medical_history:
            # STEP 3a: Get referral_id from patients_medical_history table to verify
            referral_id_from_medical_history = matching_medical_history.referral_id if hasattr(matching_medical_history, 'referral_id') else (
                matching_medical_history.referral.referral_id if matching_medical_history.referral else None
            )
            
            # STEP 3b: Compare both referral_ids
            if referral_id_from_medical_history == referral_id_from_referrals:
                print(f"✅ STEP 3: Comparison LEGIT!")
                print(f"   referrals_referral.referral_id = {referral_id_from_referrals}")
                print(f"   patients_medical_history.referral_id = {referral_id_from_medical_history}")
                print(f"   Match: ✅")
                
                # STEP 4: Pull notes and advice from patients_medical_history
                notes_from_db = matching_medical_history.notes
                advice_from_db = matching_medical_history.advice
                
                # STEP 5: Populate the form (set on referral object for template)
                # Convert empty strings to None so template can properly check
                referral.medical_history_notes = notes_from_db if (notes_from_db and notes_from_db.strip()) else None
                referral.medical_history_advice = advice_from_db if (advice_from_db and advice_from_db.strip()) else None
                
                print(f"✅ STEP 4-5: Pulled and populated:")
                print(f"   notes = '{referral.medical_history_notes[:100] if referral.medical_history_notes else None}...'")
                print(f"   advice = '{referral.medical_history_advice[:100] if referral.medical_history_advice else None}...'")
                
                logger.debug(f"  ✅ Found medical_history: notes='{matching_medical_history.notes[:50] if matching_medical_history.notes else None}...', advice='{matching_medical_history.advice[:50] if matching_medical_history.advice else None}...'")
            else:
                print(f"❌ STEP 3: Comparison FAILED - IDs don't match!")
                print(f"   referrals_referral.referral_id = {referral_id_from_referrals}")
                print(f"   patients_medical_history.referral_id = {referral_id_from_medical_history}")
                referral.medical_history_notes = None
                referral.medical_history_advice = None
        else:
            # STEP 3: No match found in patients_medical_history
            print(f"❌ STEP 3: No matching record found in patients_medical_history")
            print(f"   Looking for referral_id = {referral_id_from_referrals}")
            print(f"   But no Medical_History record has this referral_id")
            
            referral.medical_history_notes = None
            referral.medical_history_advice = None
            
            # Debug: Show what referral_ids exist in patients_medical_history for this patient
            all_medical_history_for_patient = Medical_History.objects.filter(patient_id=referral.patient)
            print(f"   Debug: Patient {referral.patient.patients_id} has {all_medical_history_for_patient.count()} medical_history records:")
            for mh in all_medical_history_for_patient[:5]:
                mh_ref_id = mh.referral_id if hasattr(mh, 'referral_id') else (mh.referral.referral_id if mh.referral else 'NULL')
                print(f"     - Medical_History {mh.history_id}: referral_id = {mh_ref_id}")
            
            logger.debug(f"  ❌ No medical_history found for referral {referral.referral_id}")

    # Predictions already generated above, no need to regenerate

    active_tab = request.GET.get('tab')
    if not active_tab:
        if request.GET.get('referred_page'):
            active_tab = 'tab3'
        elif request.GET.get('active_page'):
            active_tab = 'tab2'
        elif request.GET.get('pending_page'):
            active_tab = 'tab1'
        elif request.GET.get('patients_page'):
            active_tab = 'tab4'
        else:
            active_tab = 'tab1'

    return render(request, 'patients/user/referral_list.html', {
        'active_page': 'referral_list',
        'pending_referrals': pending_page,
        'active_referrals': active_page,
        'referred_referrals': referred_page,
        'patients': patients_qs,  # All patients from all facilities
        'predictions': predictions,
        'active_tab': active_tab,
        # Count badges for tabs
        'pending_count': pending_count,
        'active_count': active_count,
        'referred_count': referred_count,
        'patients_count': patients_count,
        'medical_history_count': medical_history_count,
        'followups': followups_list,
        'followups_count': followups_count,
    })

@login_required 
@never_cache
def admin_patient_list(request):
    MLModelManager.train_models_if_needed()
    
    # Import Medical_History early since it's used in multiple places
    from patients.models import Medical_History
    from referrals.models import FollowUpVisit

    base_qs = Referral.objects.select_related('patient', 'patient__facility', 'user', 'examined_by').order_by('-created_at')
    pending_qs = base_qs.filter(status='pending')
    
    # For active referrals: if user is a doctor, only show referrals they accepted (examined_by = current user)
    # Staff/admin can see all active referrals
    active_qs = base_qs.filter(status='in-progress')
    try:
        from accounts.models import Doctors
        doctor_profile = Doctors.objects.get(user=request.user)
        if doctor_profile.status == 'ACTIVE' and not request.user.is_staff:
            # Doctor view: only show referrals they accepted
            active_qs = active_qs.filter(examined_by=request.user)
    except Doctors.DoesNotExist:
        pass  # Not a doctor, show all active referrals (for staff/admin)
    
    # For referred (completed) referrals: if user is a doctor, only show referrals they examined (examined_by = current user)
    # Staff/admin can see all referred referrals
    # Sort by completed_at descending (latest first), then by created_at as fallback
    referred_qs = base_qs.filter(status='completed').order_by('-completed_at', '-created_at')
    try:
        from accounts.models import Doctors
        doctor_profile = Doctors.objects.get(user=request.user)
        if doctor_profile.status == 'ACTIVE' and not request.user.is_staff:
            # Doctor view: only show referrals they examined
            referred_qs = referred_qs.filter(examined_by=request.user)
    except Doctors.DoesNotExist:
        pass  # Not a doctor, show all referred referrals (for staff/admin)

    # Check view mode: 'assessment' (shows Active Referral + Referred) or 'patients' (shows All Patients only)
    view_mode = request.GET.get('mode', 'assessment')  # Default to 'assessment' for backward compatibility

    # Filter patients based on view_mode
    if view_mode == 'patients':
        # When view_mode is 'patients', only show patients that the user has handled
        from django.db.models import OuterRef, Subquery
        
        # Get patient IDs from referrals created by user
        patients_from_user_referrals = Referral.objects.filter(
            user=request.user
        ).values_list('patient_id', flat=True).distinct()
        
        # Get patient IDs from referrals examined by user
        patients_from_user_examinations = Referral.objects.filter(
            examined_by=request.user
        ).values_list('patient_id', flat=True).distinct()
        
        # Get patient IDs from follow-up visits recorded by user
        patients_from_user_followups = FollowUpVisit.objects.filter(
            user=request.user
        ).values_list('patient_id', flat=True).distinct()
        
        # Get patient IDs from medical history created by user
        patients_from_user_medical_history = Medical_History.objects.filter(
            user_id=request.user
        ).values_list('patient_id', flat=True).distinct()
        
        # Combine all patient IDs
        handled_patient_ids = set(patients_from_user_referrals) | set(patients_from_user_examinations) | set(patients_from_user_followups) | set(patients_from_user_medical_history)
        
        if handled_patient_ids:
            # Get all patients handled by the user
            latest_referral_subquery = Referral.objects.filter(
                patient=OuterRef('pk')
            ).order_by('-created_at')
            
            patients_qs = Patient.objects.filter(
                patients_id__in=handled_patient_ids
            ).select_related('facility').annotate(
                referral_count=Count('referral'),
                latest_referral_id=Subquery(latest_referral_subquery.values('referral_id')[:1]),
                latest_referral_date=Subquery(latest_referral_subquery.values('created_at')[:1]),
            ).order_by('first_name', 'last_name')
        else:
            patients_qs = Patient.objects.none()
    else:
        # For assessment mode, show all patients
        patients_qs = ReferralQueryOptimizer.get_patients_with_referral_count().order_by('first_name', 'last_name')
    
    facilities = Facility.objects.all()

    # Get total counts for badges (use the filtered querysets)
    pending_count = pending_qs.count()
    active_count = active_qs.count()  # This will be filtered for doctors
    referred_count = referred_qs.count()
    patients_count = patients_qs.count()
    medical_history_count = Medical_History.objects.count()
    
    # Get follow-ups for the Follow-ups tab
    # Filter by facility unless user is admin
    followups_qs = Medical_History.objects.filter(
        followup_date__isnull=False
    ).select_related('patient_id', 'patient_id__facility', 'user_id', 'referral', 'referral__examined_by').order_by('-followup_date')
    
    # Check if user is a doctor
    is_doctor = False
    try:
        from accounts.models import Doctors
        doctor_profile = Doctors.objects.get(user=request.user)
        if doctor_profile.status == 'ACTIVE':
            is_doctor = True
    except Doctors.DoesNotExist:
        pass
    
    if not request.user.is_staff:
        # If user is a doctor, only show follow-ups where they set the follow-up date
        # (i.e., where referral.examined_by == current user)
        if is_doctor:
            followups_qs = followups_qs.filter(
                referral__examined_by=request.user,
                referral__isnull=False
            )
        else:
            # For non-doctor users (BHW), filter by facility
            user_facilities = request.user.shared_facilities.all()
            if user_facilities.exists():
                followups_qs = followups_qs.filter(patient_id__facility__in=user_facilities)
            else:
                followups_qs = followups_qs.none()
    
    # Calculate status for each follow-up
    today = datetime.now().date()
    followups_list = []
    followups_count = 0  # Initialize count
    
    # Get all completed follow-up visit medical_history IDs for efficient lookup
    completed_medical_history_ids = set(
        FollowUpVisit.objects.filter(
            status='completed',
            medical_history__in=followups_qs
        ).values_list('medical_history_id', flat=True)
    )
    
    for followup in followups_qs:
        # Check if there's a completed follow-up visit
        has_completed_visit = followup.history_id in completed_medical_history_ids
        
        if followup.followup_date < today:
            status = 'overdue'
        elif followup.followup_date == today:
            status = 'today'
        else:
            status = 'upcoming'
        
        if has_completed_visit:
            status = 'completed'
        else:
            # Count non-completed follow-ups for the badge
            followups_count += 1
        
        followups_list.append({
            'medical_history': followup,
            'status': status,
            'patient_name': f"{followup.patient_id.first_name} {followup.patient_id.last_name}",
            'patient_id': followup.patient_id.patients_id,
            'followup_date': followup.followup_date,
            'illness_name': followup.illness_name,
            'notes': followup.notes,
            'advice': followup.advice,
        })
    
    # Ensure it's always an integer for template display
    followups_count = int(followups_count) if followups_count else 0

    # Get predictions for all referrals before pagination to sort by severity
    all_pending = list(pending_qs)
    all_active = list(active_qs)
    all_referred = list(referred_qs)
    
    all_referrals_for_prediction = all_pending + all_active + all_referred
    predictions = BatchPredictor.predict_all_batch(all_referrals_for_prediction) if all_referrals_for_prediction else {}
    
    # Sort by severity: High (0) -> Medium (1) -> Low (2) -> Unspecified (3), then by created_at descending
    def sort_key(referral):
        severity_order = get_severity_order(referral.referral_id, predictions)
        return (severity_order, -referral.created_at.timestamp() if referral.created_at else 0)
    
    all_pending.sort(key=sort_key)
    all_active.sort(key=sort_key)
    
    pending_page = Paginator(all_pending, 10).get_page(request.GET.get('pending_page') or 1)
    active_page = Paginator(all_active, 10).get_page(request.GET.get('active_page') or 1)
    referred_page = Paginator(referred_qs, 10).get_page(request.GET.get('referred_page') or 1)
    patients_page = Paginator(patients_qs, 10).get_page(request.GET.get('patients_page') or 1)

    # Add medical_history notes and advice to each referral for template access
    # Use direct database queries with referral_id instead of referral object to ensure data is retrieved
    import logging
    logger = logging.getLogger(__name__)

    for referral in pending_page.object_list:
        # STEP 1: Get referral_id from referrals_referral table (Referral model)
        referral_id_from_referrals = referral.referral_id
        
        # STEP 2: Query patients_medical_history table to find matching referral_id
        matching_medical_history = Medical_History.objects.filter(
            referral_id=referral_id_from_referrals
        ).order_by('-diagnosed_date').first()
        
        # STEP 3: Verify if the comparison found a match (legit)
        if matching_medical_history:
            referral_id_from_medical_history = matching_medical_history.referral_id if hasattr(matching_medical_history, 'referral_id') else (
                matching_medical_history.referral.referral_id if matching_medical_history.referral else None
            )
            
            if referral_id_from_medical_history == referral_id_from_referrals:
                # STEP 4-5: Pull and populate
                notes_from_db = matching_medical_history.notes
                advice_from_db = matching_medical_history.advice
                
                referral.medical_history_notes = notes_from_db if (notes_from_db and notes_from_db.strip()) else None
                referral.medical_history_advice = advice_from_db if (advice_from_db and advice_from_db.strip()) else None
            else:
                referral.medical_history_notes = None
                referral.medical_history_advice = None
        else:
            referral.medical_history_notes = None
            referral.medical_history_advice = None

    for referral in active_page.object_list:
        # STEP 1: Get referral_id from referrals_referral table (Referral model)
        referral_id_from_referrals = referral.referral_id
        
        # STEP 2: Query patients_medical_history table to find matching referral_id
        matching_medical_history = Medical_History.objects.filter(
            referral_id=referral_id_from_referrals
        ).order_by('-diagnosed_date').first()
        
        # STEP 3: Verify if the comparison found a match (legit)
        if matching_medical_history:
            referral_id_from_medical_history = matching_medical_history.referral_id if hasattr(matching_medical_history, 'referral_id') else (
                matching_medical_history.referral.referral_id if matching_medical_history.referral else None
            )
            
            if referral_id_from_medical_history == referral_id_from_referrals:
                # STEP 4-5: Pull and populate
                notes_from_db = matching_medical_history.notes
                advice_from_db = matching_medical_history.advice
                
                referral.medical_history_notes = notes_from_db if (notes_from_db and notes_from_db.strip()) else None
                referral.medical_history_advice = advice_from_db if (advice_from_db and advice_from_db.strip()) else None
            else:
                referral.medical_history_notes = None
                referral.medical_history_advice = None
        else:
            referral.medical_history_notes = None
            referral.medical_history_advice = None

    for referral in referred_page.object_list:
        # STEP 1: Get referral_id from referrals_referral table (Referral model)
        referral_id_from_referrals = referral.referral_id
        
        # STEP 2: Query patients_medical_history table to find matching referral_id
        matching_medical_history = Medical_History.objects.filter(
            referral_id=referral_id_from_referrals
        ).order_by('-diagnosed_date').first()
        
        # STEP 3: Verify if the comparison found a match (legit)
        if matching_medical_history:
            referral_id_from_medical_history = matching_medical_history.referral_id if hasattr(matching_medical_history, 'referral_id') else (
                matching_medical_history.referral.referral_id if matching_medical_history.referral else None
            )
            
            if referral_id_from_medical_history == referral_id_from_referrals:
                # STEP 4: Pull notes and advice from patients_medical_history
                notes_from_db = matching_medical_history.notes
                advice_from_db = matching_medical_history.advice
                
                # STEP 5: Populate the form (set on referral object for template)
                referral.medical_history_notes = notes_from_db if (notes_from_db and notes_from_db.strip()) else None
                referral.medical_history_advice = advice_from_db if (advice_from_db and advice_from_db.strip()) else None
            else:
                referral.medical_history_notes = None
                referral.medical_history_advice = None
        else:
            referral.medical_history_notes = None
            referral.medical_history_advice = None

    # Predictions already generated above, no need to regenerate

    # Get all doctors for dropdown (will filter in template to only show those with users)
    doctors = Doctors.objects.all().order_by('last_name', 'first_name')
    
    # Get all diseases for the disease dropdown
    diseases = Disease.objects.all().order_by('name')

    # Determine active tab based on mode and request parameters
    active_tab = request.GET.get('tab')
    if not active_tab:
        if view_mode == 'patients':
            # For patients mode, default to All Patients tab (tab3)
            if request.GET.get('patients_page'):
                active_tab = 'tab3'
            elif request.GET.get('medical_history_page'):
                active_tab = 'tab4'
            elif request.GET.get('followups_page'):
                active_tab = 'tab5'
            else:
                active_tab = 'tab3'  # Default to All Patients
        else:
            # For assessment mode, default to Pending tab (tab1)
            if request.GET.get('referred_page'):
                active_tab = 'tab3'
            elif request.GET.get('active_page'):
                active_tab = 'tab2'
            elif request.GET.get('pending_page'):
                active_tab = 'tab1'
            else:
                active_tab = 'tab1'  # Default to Pending

    return render(request, 'patients/admin/patient_list.html', {
        'active_page': 'patient_list',
        'active_tab': active_tab,
        'view_mode': view_mode,  # Pass view_mode to template
        'facility': facilities,
        'patients': patients_page,
        'pending_referrals': pending_page,
        'active_referrals': active_page,
        'referred_referrals': referred_page,
        'predictions': predictions,
        'doctors': doctors,
        'followups': followups_list,
        'followups_count': followups_count,
        'diseases': diseases,
        'training_result': {"status": "Models loaded from cache"},
        # Count badges for tabs
        'pending_count': pending_count,
        'active_count': active_count,
        'referred_count': referred_count,
        'patients_count': patients_count,
        'medical_history_count': medical_history_count,
        # Also pass to context processor variable for sidebar consistency
        'active_referrals_count': active_count,
    })
    
    
@login_required
def get_referral_details(request, referral_id):
    """Get full referral details by referral_id for populating view modal"""
    try:
        print(f"🔍 get_referral_details called with referral_id: {referral_id} (type: {type(referral_id)})")
        print(f"🔍 User: {request.user.username}")
        
        # Try to get the referral
        try:
            referral = Referral.objects.select_related('patient', 'user', 'examined_by', 'facility').get(
                referral_id=referral_id
            )
            print(f"✅ Found referral: {referral.referral_id}")
            print(f"✅ Patient: {referral.patient.first_name if referral.patient else 'No patient'}")
            print(f"✅ Status: {referral.status}")
            print(f"✅ Height: {referral.height}, Weight: {referral.weight}")
            print(f"✅ BP: {referral.bp_systolic}/{referral.bp_diastolic}")
            print(f"✅ Temperature: {referral.temperature}")
            print(f"✅ Chief Complaint: {referral.chief_complaint}")
        except Referral.DoesNotExist:
            print(f"❌ Referral with ID {referral_id} not found in database")
            # Try to see if there are any referrals at all
            all_referrals = Referral.objects.all()[:5]
            print(f"📋 Sample referral IDs in database: {[r.referral_id for r in all_referrals]}")
            return JsonResponse({'success': False, 'error': f'Referral {referral_id} not found'}, status=404)
        
        # Get related medical history if exists
        from patients.models import Medical_History
        medical_history = Medical_History.objects.filter(
            referral_id=referral_id
        ).order_by('-diagnosed_date').first()
        if medical_history:
            print(f"✅ Found medical history: {medical_history.illness_name}")
        else:
            print(f"⚠️ No medical history found for referral {referral_id}")
        
        # Build referral data
        referral_data = {
            'referral_id': referral.referral_id,
            'status': referral.status,
            'created_at': referral.created_at.isoformat() if referral.created_at else None,
            'completed_at': referral.completed_at.isoformat() if referral.completed_at else None,
            'followup_date': referral.followup_date.isoformat() if referral.followup_date else None,
            
            # Patient Information
            'patient_name': f"{referral.patient.first_name} {referral.patient.middle_name or ''} {referral.patient.last_name}".strip() if referral.patient else 'N/A',
            'patient_sex': referral.patient.sex if referral.patient else '',
            'patient_address': referral.patient.p_address if referral.patient else '',
            'refer_from': referral.facility.name if referral.facility else '',
            
            # Vital Signs
            'height': str(referral.height) if referral.height is not None else '',
            'weight': str(referral.weight) if referral.weight is not None else '',
            'bp_systolic': referral.bp_systolic if referral.bp_systolic is not None else '',
            'bp_diastolic': referral.bp_diastolic if referral.bp_diastolic is not None else '',
            'pulse_rate': referral.pulse_rate if referral.pulse_rate is not None else '',
            'respiratory_rate': referral.respiratory_rate if referral.respiratory_rate is not None else '',
            'temperature': str(referral.temperature) if referral.temperature is not None else '',
            'oxygen_saturation': referral.oxygen_saturation if referral.oxygen_saturation is not None else '',
            
            # Clinical Notes
            'chief_complaint': referral.chief_complaint or '',
            'symptoms': referral.symptoms or '',
            'work_up_details': referral.work_up_details or '',
            
            # Diagnosis - trim whitespace
            'ICD_code': (referral.ICD_code or '').strip(),
            'initial_diagnosis': (referral.initial_diagnosis or '').strip(),
            'final_diagnosis': (referral.final_diagnosis or '').strip(),
            
            # Examined By
            'examined_by': f"Dr. {referral.examined_by.get_full_name()}" if referral.examined_by else '',
            'examined_by_id': referral.examined_by.id if referral.examined_by else None,
            
            # Medical History (if exists) - trim whitespace
            'illness_name': (medical_history.illness_name or '').strip() if medical_history else '',
            'notes': (medical_history.notes or '').strip() if medical_history else (referral.remarks or '').strip() if referral.remarks else '',
            'advice': (medical_history.advice or '').strip() if medical_history else '',
            
            # Lifestyle & Social History
            'is_smoker': bool(referral.is_smoker) if referral.is_smoker is not None else False,
            'smoking_sticks_per_day': str(referral.smoking_sticks_per_day) if referral.smoking_sticks_per_day is not None else '',
            'is_alcoholic': bool(referral.is_alcoholic) if referral.is_alcoholic is not None else False,
            'alcohol_bottles_per_year': str(referral.alcohol_bottles_per_year) if referral.alcohol_bottles_per_year is not None else '',
            'family_planning': bool(referral.family_planning) if referral.family_planning is not None else False,
            'family_planning_type': str(referral.family_planning_type) if referral.family_planning_type else '',
            
            # Menstrual History
            'menarche': str(referral.menarche) if referral.menarche is not None else '',
            'sexually_active': bool(referral.sexually_active) if referral.sexually_active is not None else False,
            'number_of_partners': str(referral.number_of_partners) if referral.number_of_partners is not None else '',
            'is_menopause': bool(referral.is_menopause) if referral.is_menopause is not None else False,
            'menopause_age': str(referral.menopause_age) if referral.menopause_age is not None else '',
            'last_menstrual_period': referral.last_menstrual_period.isoformat() if referral.last_menstrual_period else '',
            'period_duration': str(referral.period_duration) if referral.period_duration is not None else '',
            'period_interval': str(referral.period_interval) if referral.period_interval is not None else '',
            'pads_per_day': str(referral.pads_per_day) if referral.pads_per_day is not None else '',
            
            # Pregnancy History
            'is_pregnant': bool(referral.is_pregnant) if referral.is_pregnant is not None else False,
            'gravidity': str(referral.gravidity) if referral.gravidity is not None else '',
            'parity': str(referral.parity) if referral.parity is not None else '',
            'delivery_type': str(referral.delivery_type) if referral.delivery_type else '',
            'full_term_births': str(referral.full_term_births) if referral.full_term_births is not None else '',
            'premature_births': str(referral.premature_births) if referral.premature_births is not None else '',
            'abortions': str(referral.abortions) if referral.abortions is not None else '',
            'living_children': str(referral.living_children) if referral.living_children is not None else '',
        }
        
        print(f"✅ Built referral_data with {len(referral_data)} fields")
        print(f"✅ Sample data - Height: {referral_data['height']}, Weight: {referral_data['weight']}")
        print(f"✅ Sample data - BP: {referral_data['bp_systolic']}/{referral_data['bp_diastolic']}")
        print(f"✅ Sample data - Temperature: {referral_data['temperature']}")
        print(f"✅ Sample data - Chief Complaint: {referral_data['chief_complaint']}")
        print(f"✅ Sample data - Is Smoker: {referral_data['is_smoker']}")
        
        return JsonResponse({'success': True, 'referral': referral_data})
    except Referral.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Referral not found'}, status=404)
    except Exception as e:
        print(f"❌ Error in get_referral_details: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def get_patient_referral_history(request, patient_id):
    try:
        print(f"Fetching referral history for patient ID: {patient_id} for user: {request.user.username}")
        print(f"Patient ID type: {type(patient_id)}")
        
        # Filter referrals to only show those handled by the current user
        # A referral is "handled" if user created it OR examined it
        referrals = Referral.objects.filter(
            patient_id=patient_id
        ).filter(
            Q(user=request.user) | Q(examined_by=request.user)
        ).order_by('-created_at')
        print(f"Found {referrals.count()} referrals for patient {patient_id} handled by user {request.user.username}")
        
        # Get medical history records created by the user OR linked to referrals handled by the user
        from patients.models import Medical_History
        referral_ids = list(referrals.values_list('referral_id', flat=True))
        if referral_ids:
            # If there are referrals, include medical history linked to them OR created by user
            all_medical_history = Medical_History.objects.filter(
                patient_id=patient_id
            ).filter(
                Q(user_id=request.user) | Q(referral_id__in=referral_ids)
            ).order_by('-diagnosed_date')
        else:
            # If no referrals, only show medical history created by the user
            all_medical_history = Medical_History.objects.filter(
                patient_id=patient_id,
                user_id=request.user
            ).order_by('-diagnosed_date')
        print(f"Found {all_medical_history.count()} medical history records for patient {patient_id} created by or linked to user's referrals")
        
        # Filter follow-up visits to only show those recorded by the current user
        followup_visits = FollowUpVisit.objects.filter(
            patient_id=patient_id,
            user=request.user
        ).select_related('medical_history', 'user').order_by('-visit_date')
        print(f"Found {followup_visits.count()} follow-up visits for patient {patient_id} recorded by user {request.user.username}")
        
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
                'height': float(referral.height),
                # Add referral model fields for diagnosis and ICD code
                'ICD_code': referral.ICD_code or '',
                'initial_diagnosis': referral.initial_diagnosis or '',
                'final_diagnosis': referral.final_diagnosis or '',
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
        
        # Add follow-up visits to the list
        for visit in followup_visits:
            visit_data = {
                'type': 'followup_visit',  # Identifier to distinguish from regular referrals
                'visit_id': visit.followup_id,
                'visit_date': visit.visit_date.isoformat(),
                'status': visit.status,
                'created_at': visit.created_at.isoformat(),
                'recorded_by': visit.user.get_full_name() or visit.user.username,
                
                # Vital signs
                'weight': float(visit.weight) if visit.weight else None,
                'height': float(visit.height) if visit.height else None,
                'bp_systolic': visit.bp_systolic,
                'bp_diastolic': visit.bp_diastolic,
                'pulse_rate': visit.pulse_rate,
                'respiratory_rate': visit.respiratory_rate,
                'temperature': float(visit.temperature) if visit.temperature else None,
                'oxygen_saturation': visit.oxygen_saturation,
                
                # Visit information
                'current_symptoms': visit.current_symptoms,
                'treatment_response': visit.treatment_response,
                'new_medications': visit.new_medications,
                'visit_notes': visit.visit_notes,
                'next_followup_date': visit.next_followup_date.isoformat() if visit.next_followup_date else None,
                
                # Related medical history info
                'illness_name': visit.medical_history.illness_name if visit.medical_history else None,
                'notes': visit.medical_history.notes if visit.medical_history else None,
                'advice': visit.medical_history.advice if visit.medical_history else None,
            }
            referral_list.append(visit_data)
        
        # Sort by date (most recent first) - combining referrals and follow-up visits
        referral_list.sort(key=lambda x: x.get('created_at') or x.get('visit_date'), reverse=True)
        
        print(f"🔍 Returning {len(referral_list)} items (referrals + follow-up visits) with matched medical history")
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
    # Base queryset - include facility for CSV export
    qs = Referral.objects.select_related('user', 'patient', 'facility').all()

    # Filters from query params
    year = request.GET.get('year')
    month = request.GET.get('month')
    date_from_str = request.GET.get('date_from', '')
    date_to_str = request.GET.get('date_to', '')
    facility_id = request.GET.get('facility_id')
    user_id = request.GET.get('user_id')

    # Apply temporal filters - prioritize date_from/date_to over year/month
    if date_from_str or date_to_str:
        if date_from_str:
            try:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
                qs = qs.filter(created_at__date__gte=date_from)
            except ValueError:
                pass
        if date_to_str:
            try:
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
                qs = qs.filter(created_at__date__lte=date_to)
            except ValueError:
                pass
    else:
        # Fallback to year/month if date_from/date_to not provided
        if year and year.isdigit():
            qs = qs.filter(created_at__year=int(year))
        if month and month.isdigit():
            qs = qs.filter(created_at__month=int(month))

    # Apply facility filter by mapping to users (ManyToMany relationship)
    if facility_id and facility_id.isdigit():
        try:
            facility = Facility.objects.get(facility_id=int(facility_id))
            # Get all user IDs associated with this facility
            user_ids = facility.users.values_list('id', flat=True)
            if user_ids:
                qs = qs.filter(user_id__in=user_ids)
            else:
                # If facility has no users, return empty queryset
                qs = qs.none()
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

    # Include date range or year/month if specified
    date_suffix = None
    if date_from_str or date_to_str:
        try:
            if date_from_str and date_to_str:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
                if date_from == date_to:
                    date_suffix = date_from.strftime('%Y-%m-%d')
                else:
                    date_suffix = f"{date_from.strftime('%Y-%m-%d')}_to_{date_to.strftime('%Y-%m-%d')}"
            elif date_from_str:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
                date_suffix = f"from_{date_from.strftime('%Y-%m-%d')}"
            elif date_to_str:
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
                date_suffix = f"to_{date_to.strftime('%Y-%m-%d')}"
        except ValueError:
            pass
    
    # Fallback to year/month if date_from/date_to not provided
    if not date_suffix:
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
    # Header - All fields from Referral model
    writer.writerow([
        # Basic Information
        'referral_id', 'facility_name', 'username',
        'patient_name', 'created_at', 'completed_at', 'status', 'followup_date',
        # Referral Details
        'referral_type', 'chief_complaint', 'symptoms', 'work_up_details', 'ICD_code',
        'initial_diagnosis', 'final_diagnosis', 'cause', 'treatments', 'remarks',
        # Vital Signs
        'weight', 'height', 'bp_systolic', 'bp_diastolic', 'pulse_rate',
        'respiratory_rate', 'temperature', 'oxygen_saturation',
        # Lifestyle/Social History
        'is_smoker', 'smoking_sticks_per_day', 'is_alcoholic', 'alcohol_bottles_per_year',
        'family_planning', 'family_planning_type',
        # Menstrual History
        'menarche', 'sexually_active', 'number_of_partners', 'is_menopause', 'menopause_age',
        'last_menstrual_period', 'period_duration', 'period_interval', 'pads_per_day',
        # Pregnancy History
        'is_pregnant', 'gravidity', 'parity', 'delivery_type', 'full_term_births',
        'premature_births', 'abortions', 'living_children'
    ])

    # Rows
    for r in qs.order_by('created_at'):
        patient_name = f"{r.patient.first_name} {r.patient.last_name}" if hasattr(r.patient, 'first_name') else str(r.patient_id)
        facility_name = r.facility.name if r.facility else ''
        
        writer.writerow([
            # Basic Information
            r.referral_id,
            facility_name,
            r.user.username if r.user_id else '',
            patient_name,
            r.created_at.isoformat() if r.created_at else '',
            r.completed_at.isoformat() if r.completed_at else '',
            r.status,
            r.followup_date.isoformat() if r.followup_date else '',
            # Referral Details
            r.referral_type or '',
            r.chief_complaint or '',
            r.symptoms or '',
            r.work_up_details or '',
            r.ICD_code or '',
            r.initial_diagnosis or '',
            r.final_diagnosis or '',
            r.cause or '',
            r.treatments or '',
            r.remarks or '',
            # Vital Signs
            float(r.weight) if r.weight else '',
            float(r.height) if r.height else '',
            r.bp_systolic,
            r.bp_diastolic,
            r.pulse_rate,
            r.respiratory_rate,
            float(r.temperature) if r.temperature else '',
            r.oxygen_saturation,
            # Lifestyle/Social History
            r.is_smoker,
            r.smoking_sticks_per_day or '',
            r.is_alcoholic,
            r.alcohol_bottles_per_year or '',
            r.family_planning,
            r.family_planning_type or '',
            # Menstrual History
            r.menarche or '',
            r.sexually_active if r.sexually_active is not None else '',
            r.number_of_partners or '',
            r.is_menopause if r.is_menopause is not None else '',
            r.menopause_age or '',
            r.last_menstrual_period.isoformat() if r.last_menstrual_period else '',
            r.period_duration or '',
            r.period_interval or '',
            r.pads_per_day or '',
            # Pregnancy History
            r.is_pregnant if r.is_pregnant is not None else '',
            r.gravidity or '',
            r.parity or '',
            r.delivery_type or '',
            r.full_term_births or '',
            r.premature_births or '',
            r.abortions or '',
            r.living_children or '',
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
    facility_map = {}
    for facility in Facility.objects.filter(users__in=user_ids):
        for user in facility.users.all():
            if user.id in user_ids:
                facility_map[user.id] = facility.name

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

@login_required
def train_time_model_from_csv(request):
    """API endpoint to train advanced time prediction model from CSV"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Optional: get CSV path from request
    csv_path = request.GET.get('csv_path', None)
    
    from analytics.ml_utils import train_time_prediction_model_advanced_from_csv
    result = train_time_prediction_model_advanced_from_csv(csv_path=csv_path)
    return JsonResponse(result)

