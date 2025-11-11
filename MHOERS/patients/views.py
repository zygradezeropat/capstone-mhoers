from django.shortcuts import render
from patients.models import Patient
from referrals.models import Referral
from facilities.models import Facility
from .forms import PatientForm
from django.contrib import messages
from django.shortcuts import render, redirect 
from django.contrib.auth.decorators import login_required
from django.db.models import Count, OuterRef, Subquery
from django.http import JsonResponse
from django.db.models import Q
import logging
from datetime import datetime, timedelta
from .models import Medical_History
from analytics.models import Disease
from django.views.decorators.csrf import csrf_exempt
from analytics.views import get_disease_diagnosis_counts, get_monthly_diagnosis_trends
from referrals.views import monthly_referral_counts_by_user
from referrals.utils import send_sms_iprog

logger = logging.getLogger(__name__)

def addPatient(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            middle_name = form.cleaned_data['middle_name'] 
            last_name = form.cleaned_data['last_name']

            # Check if patient with same name exists for this user
            existing_patient = Patient.objects.filter(
                first_name=first_name,
                middle_name=middle_name, 
                last_name=last_name,
                user=request.user
            ).exists()

            if existing_patient:
                messages.error(request, "Patient with this name already exists.")
                return redirect('patients:barangayPatients')

            # Get the facility associated with the current user
            facility = Facility.objects.filter(users=request.user).first()
            if facility:
                patient = form.save(commit=False)
                patient.user = request.user
                patient.facility = facility
                patient.save()
                messages.success(request, "Patient added successfully!")
                return redirect('patients:barangayPatients')
            else:
                messages.error(request, "No facility found for this user.")
                return redirect('patients:barangayPatients')
        else:
            messages.error(request, "Form is invalid.")
            print("❌ Form is invalid")
            print(form.errors)
    else:
        form = PatientForm()

    return render(request, 'patients/user/patient_list.html', {'active_page': 'barangayPatients','form': form})

@login_required
def barangayPatients(request):
    facility = request.user.shared_facilities.first() 
    user = request.user
    latest_referral_subquery = Referral.objects.filter(
        patient=OuterRef('pk')
    ).order_by('-created_at')

    # Filter patients by facility instead of individual user
    try:
        facility = Facility.objects.get(users=user)
        patients = Patient.objects.filter(facility=facility).annotate(
            referral_count=Count('referral'),
            latest_referral_id=Subquery(latest_referral_subquery.values('referral_id')[:1]), 
            latest_referral_date=Subquery(latest_referral_subquery.values('created_at')[:1]),
        )
    except Facility.DoesNotExist:
        # If user has no facility, return empty queryset
        patients = Patient.objects.none().annotate(
            referral_count=Count('referral'),
            latest_referral_id=Subquery(latest_referral_subquery.values('referral_id')[:1]),
            latest_referral_date=Subquery(latest_referral_subquery.values('created_at')[:1]),
        )

    return render(request, 'patients/user/patient_list.html', {'active_page': 'barangayPatients', 'patients': patients, 'facility': facility})

@login_required
def editPatients(request):
    
    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        user = request.user
        
        latest_referral_subquery = Referral.objects.filter(patient=OuterRef('pk')).order_by('-created_at')
        
        # Filter patients by facility instead of individual user
        try:
            facility = Facility.objects.get(users=user)
            patients = Patient.objects.filter(facility=facility).annotate(
                referral_count=Count('referral'),
                latest_referral_id=Subquery(latest_referral_subquery.values('referral_id')[:1]),
                latest_referral_date=Subquery(latest_referral_subquery.values('created_at')[:1]),
            )
        except Facility.DoesNotExist:
            # If user has no facility, return empty queryset
            patients = Patient.objects.none().annotate(
                referral_count=Count('referral'),
                latest_referral_id=Subquery(latest_referral_subquery.values('referral_id')[:1]),
                latest_referral_date=Subquery(latest_referral_subquery.values('created_at')[:1]),
            )

        try:
            # Update the patient lookup to also check facility
            facility = Facility.objects.get(users=user)
            patient = Patient.objects.get(patients_id=patient_id, facility=facility)
            
            # Update patient information - Basic Info
            patient.first_name = request.POST.get('editFname')
            patient.middle_name = request.POST.get('editMname') or None
            patient.last_name = request.POST.get('editLname')
            # Handle address - check if manual entry was used
            address = request.POST.get('editAddress')
            if not address or address == '__manual__':
                address = request.POST.get('editAddressManual', '')
            patient.p_address = address
            patient.p_number = request.POST.get('ePhone')
            patient.date_of_birth = request.POST.get('editBday')
            patient.sex = request.POST.get('eSex')
            
            # Additional Information
            patient.civil_status = request.POST.get('editCivilStatus') or None
            patient.phic_status = request.POST.get('editPhicStatus') or None
            patient.cct_beneficiary = request.POST.get('editCctBeneficiary') == 'on'
            patient.is_pwd = request.POST.get('editIsPwd') == 'on'
            
            # PhilHealth Information
            if request.POST.get('editIsPhilhealthMember') == 'on':
                patient.philhealth_number = request.POST.get('editPhilhealthNumber') or None
                patient.philhealth_category = request.POST.get('editPhilhealthCategory') or None
            else:
                patient.philhealth_number = None
                patient.philhealth_category = None
            
            # Family History
            patient.family_history_hypertension = request.POST.get('editFamilyHistoryHypertension') == 'on'
            patient.family_history_diabetes = request.POST.get('editFamilyHistoryDiabetes') == 'on'
            patient.family_history_cancer = request.POST.get('editFamilyHistoryCancer') == 'on'
            patient.family_history_asthma = request.POST.get('editFamilyHistoryAsthma') == 'on'
            patient.family_history_epilepsy = request.POST.get('editFamilyHistoryEpilepsy') == 'on'
            patient.family_history_tuberculosis = request.POST.get('editFamilyHistoryTuberculosis') == 'on'
            patient.family_history_others = request.POST.get('editFamilyHistoryOthers') or None

            patient.save()
            messages.success(request, "Patient information updated successfully!")
            return render(request, 'patients/user/patient_list.html', {'active_page': 'barangayPatients', 'patients': patients})
        except Facility.DoesNotExist:
            messages.error(request, "No facility found for this user.")
            return render(request, 'patients/user/patient_list.html', {'active_page': 'barangayPatients', 'patients': patients})
        except Patient.DoesNotExist:
            messages.error(request, "Patient not found.")
            return render(request, 'patients/user/patient_list.html', {'active_page': 'barangayPatients', 'patients': patients})
        except Exception as e:
            messages.error(request, f"Error updating patient: {str(e)}")
            return render(request, 'patients/user/patient_list.html', {'active_page': 'barangayPatients', 'patients': patients})


    return render(request, 'patients/user/patient_list.html', {'active_page': 'barangayPatients', 'patients': patients})

def deletePatient(request):
    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        user = request.user
        try:
            # Get the facility associated with the current user
            facility = Facility.objects.get(users=user)
            patient = Patient.objects.get(patients_id=patient_id, facility=facility)
            patient.delete()
            messages.success(request, "Patient deleted successfully!")
            return redirect('patients:barangayPatients')
        except Facility.DoesNotExist:
            messages.error(request, "No facility found for this user.")
            return redirect('patients:barangayPatients')
        except Patient.DoesNotExist:
            messages.error(request, "Patient not found.")
            return redirect('patients:barangayPatients')
        except Exception as e:
            messages.error(request, f"Error deleting patient: {str(e)}")
            return redirect('patients:barangayPatients')
    messages.success(request, "Patient information failed!")
    return redirect('patients:barangayPatients')    

from django.core.paginator import Paginator

def search_patients(request):
    try:
        query = (request.GET.get('q') or '').strip()
        page = int(request.GET.get('page') or 1)
        per_page = 5 if not query else 20

        qs = Patient.objects.all()

        # Scope to current user's facility patients unless staff
        if not request.user.is_staff:
            # Get the facility associated with the current user
            try:
                facility = Facility.objects.get(users=request.user)
                qs = qs.filter(facility=facility)
            except Facility.DoesNotExist:
                # If user has no facility, return empty results
                qs = qs.none()

        if query:
            qs = qs.filter(
                Q(first_name__icontains=query) |
                Q(middle_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(patients_id__icontains=query)
            )

        # Latest by highest patients_id, then stable by name
        qs = qs.order_by('-patients_id', 'last_name', 'first_name')

        paginator = Paginator(qs, per_page)
        page_obj = paginator.get_page(page)

        def to_item(p):
            name = f"{p.first_name} {(p.middle_name or '').strip()} {p.last_name}".replace('  ', ' ').strip()
            return {
                'id': p.patients_id,
                'text': name,
                'name': name,
                'pid': p.patients_id,
                'dob': p.date_of_birth.strftime('%Y-%m-%d') if p.date_of_birth else None,
            }

        return JsonResponse({
            'results': [to_item(p) for p in page_obj.object_list],
            'has_more': page_obj.has_next(),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_patient_details(request, patient_id):
    try:
        logger.info(f"Fetching details for patient ID: {patient_id}")
        
        # Get patient
        patient = Patient.objects.get(patients_id=patient_id)
        logger.info(f"Found patient: {patient.first_name} {patient.last_name}")
        
        # Get all referrals for this patient
        referrals = Referral.objects.filter(patient=patient).order_by('-created_at')
        
        # Get the latest referral
        latest_referral = referrals.first()
        logger.info(f"Latest referral found: {latest_referral.referral_id if latest_referral else 'None'}")
        
        # Get all unique visit dates from referrals with status 'completed'
        completed_referrals = referrals.filter(status='completed')
        visit_dates = list(completed_referrals.values_list('created_at', flat=True).distinct())
        
        # Get the selected date from query parameters
        selected_date = request.GET.get('date')
        
        # If a date is selected, get the referral for that date
        if selected_date: 
            try:
                selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
                selected_referral = referrals.filter(created_at__date=selected_date).first()
                if selected_referral:
                    latest_referral = selected_referral
            except ValueError:
                logger.error(f"Invalid date format: {selected_date}")
        
        # Fetch the medical history note for this patient and date
        if selected_date:
            # If a date is selected, try to fetch the medical history for that date
            medical_history_record = Medical_History.objects.filter(patient_id=patient, diagnosed_date=selected_date).first()
        else:
            # Otherwise, get the latest medical history
            medical_history_record = Medical_History.objects.filter(patient_id=patient).order_by('-diagnosed_date').first()
        medical_history_note = medical_history_record.notes if medical_history_record else None
        medical_history_advice = medical_history_record.advice if medical_history_record else None

        # Prepare the response data
        data = {
            'chief_complaint': latest_referral.chief_complaint if latest_referral else None,
            'symptoms': latest_referral.symptoms if latest_referral else None,
            'visit_dates': [date.strftime('%Y-%m-%d') for date in visit_dates],
            'vital_signs': {
                'bp': f"{latest_referral.bp_systolic}/{latest_referral.bp_diastolic}" if latest_referral else None,
                'hr': f"{latest_referral.pulse_rate}" if latest_referral else None,
                'temp': f"{latest_referral.temperature:.1f}" if latest_referral else None,
                'o2_sat': f"{latest_referral.oxygen_saturation}" if latest_referral else None,
                'resp_rate': f"{latest_referral.respiratory_rate:.1f}" if latest_referral else None,
                'weight': f"{int(latest_referral.weight)}" if latest_referral else None,
                'height': f"{int(latest_referral.height)}" if latest_referral else None,
            } if latest_referral else None,
            'work_up_details': latest_referral.work_up_details if latest_referral else None,
            'medical_history_note': medical_history_note,
            'medical_history_advice': medical_history_advice
        }
        
        logger.info("Successfully prepared patient data")
        return JsonResponse(data)
        
    except Patient.DoesNotExist:
        logger.error(f"Patient not found with ID: {patient_id}")
        return JsonResponse({'error': 'Patient not found'}, status=404)
    except Exception as e:
        logger.error(f"Error fetching patient details: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_patient_sex(request, patient_id):
    """API endpoint to get patient sex for conditional form display"""
    try:
        patient = Patient.objects.get(patients_id=patient_id)
        return JsonResponse({'sex': patient.sex})
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_medical_history_followups(request):
    """
    API endpoint to fetch medical history follow-up dates for calendar display.
    Returns follow-up dates with patient information for the current month.
    Filters by facility unless the user is admin (staff).
    """
    try:
        # Get current month and year
        year = request.GET.get('year', datetime.now().year)
        month = request.GET.get('month', datetime.now().month)
        
        # Convert to integers
        year = int(year)
        month = int(month)
        
        # Get start and end of month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # Base query for medical history records with follow-up dates in the specified month
        followups_query = Medical_History.objects.filter(
            followup_date__gte=start_date,
            followup_date__lte=end_date
        ).select_related('patient_id')
        
        # Filter by current user's facility unless user is admin (staff)
        if not request.user.is_staff:
            # For regular users, only show follow-ups for patients in their facility
            try:
                facility = Facility.objects.get(users=request.user)
                followups_query = followups_query.filter(
                    patient_id__facility=facility
                )
            except Facility.DoesNotExist:
                # If user has no facility, return empty queryset
                followups_query = followups_query.none()
        # Admin users (is_staff=True) can see all follow-ups, so no additional filtering
        
        # Get the filtered followups
        followups = followups_query.values(
            'followup_date',
            'patient_id__patients_id',
            'patient_id__first_name',
            'patient_id__last_name',
            'illness_name',
            'notes',
            'advice',
            'patient_id__user__username'  # Add username for debugging
        )
        
        # Group follow-ups by date
        followups_by_date = {}
        for followup in followups:
            date_key = followup['followup_date'].strftime('%Y-%m-%d')
            if date_key not in followups_by_date:
                followups_by_date[date_key] = []
            
            followups_by_date[date_key].append({
                'patient_id': followup['patient_id__patients_id'],
                'patient_name': f"{followup['patient_id__first_name']} {followup['patient_id__last_name']}",
                'illness_name': followup['illness_name'],
                'notes': followup['notes'],
                'advice': followup['advice'],
                'followup_date': followup['followup_date'].isoformat(),
                'patient_user': followup['patient_id__user__username']  # For debugging
            })
        
        return JsonResponse({
            'success': True,
            'followups': followups_by_date,
            'month': month,
            'year': year,
            'is_admin': request.user.is_staff,
            'current_user': request.user.username
        })
        
    except Exception as e:
        logger.error(f"Error fetching medical history followups: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

 
# New endpoint: send SMS if patient has a check-up (follow-up) scheduled today
from django.contrib.auth.decorators import login_required

@login_required
def send_today_checkup_sms(request, patient_id: int):
    try:
        # Determine today's date (timezone aware if Django timezone configured)
        try:
            from django.utils import timezone
            today = timezone.localdate()
        except Exception:
            from datetime import date
            today = date.today()

        # Scope patient to current user's facility where applicable
        user = request.user
        try:
            # For staff/admin, allow access to all patients
            if user.is_staff or user.is_superuser:
                patient = Patient.objects.get(patients_id=patient_id)
            else:
                # For regular users, check facility
                facility = Facility.objects.get(users=user)
                patient = Patient.objects.get(patients_id=patient_id, facility=facility)
        except Facility.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'No facility for user'}, status=403)
        except Patient.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Patient not found'}, status=404)

        # Check if this is a manual send (allow any follow-up date) or scheduled (only today)
        manual_send = request.GET.get('manual', 'false').lower() == 'true'
        
        if manual_send:
            # For manual sends, check if patient has any follow-up scheduled (any date)
            has_followup = Medical_History.objects.filter(
                patient_id=patient,
                followup_date__isnull=False,
            ).order_by('-followup_date').first()
            
            if not has_followup:
                return JsonResponse({'ok': False, 'error': 'No follow-up scheduled for this patient'}, status=200)
            
            # Use the most recent follow-up date for the message
            followup_date = has_followup.followup_date
            if followup_date == today:
                message = f"Hi {patient.first_name} {patient.last_name}, this is a reminder of your medical check-up scheduled today."
            else:
                message = f"Hi {patient.first_name} {patient.last_name}, this is a reminder of your medical check-up scheduled on {followup_date.strftime('%B %d, %Y')}."
        else:
            # For scheduled sends, only send if follow-up is today
            has_today_followup = Medical_History.objects.filter(
                patient_id=patient,
                followup_date=today,
            ).exists()

            if not has_today_followup:
                return JsonResponse({'ok': False, 'error': 'No check-up scheduled today'}, status=200)
            
            message = f"Hi {patient.first_name} {patient.last_name}, this is a reminder of your medical check-up scheduled today."

        # Optional sender_id via query string
        sender_id = request.GET.get('sender_id') or None

        result = send_sms_iprog(patient.p_number, patient.first_name, patient.last_name, message=message, sender_id=sender_id)
        status = 200 if result.get('ok') else 502
        return JsonResponse(result, status=status)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)
