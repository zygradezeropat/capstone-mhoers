from accounts.models import BHWRegistration, Doctors, Nurses
from referrals.models import Referral, FollowUpVisit
from patients.models import Medical_History
from datetime import datetime

def pending_users_count(request):
    """Context processor to add pending users count to all templates"""
    if request.user.is_authenticated:
        # Count all pending users
        pending_bhw_count = BHWRegistration.objects.filter(status='PENDING_APPROVAL').count()
        pending_doctors_count = Doctors.objects.filter(status='PENDING_APPROVAL').count()
        pending_nurses_count = Nurses.objects.filter(status='PENDING_APPROVAL').count()
        
        total_pending_users = pending_bhw_count + pending_doctors_count + pending_nurses_count
        
        return {
            'pending_users_count': total_pending_users,
            'pending_bhw_count': pending_bhw_count,
            'pending_doctors_count': pending_doctors_count,
            'pending_nurses_count': pending_nurses_count,
        }
    return {
        'pending_users_count': 0,
        'pending_bhw_count': 0,
        'pending_doctors_count': 0,
        'pending_nurses_count': 0,
    }


def user_approval_status(request):
    """Expose is_approved and is_pending for the current user across templates."""
    is_approved = True
    is_pending = False
    is_doctor = False
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        has_profile = False
        for model in (BHWRegistration, Doctors, Nurses):
            try:
                profile = model.objects.get(user=user)
                has_profile = True
                status = getattr(profile, 'status', None)
                
                # Check if user is a doctor
                if model == Doctors and status == 'ACTIVE':
                    is_doctor = True
                
                if status == 'APPROVED':
                    # Keep approved True unless contradicted later (shouldn't happen)
                    pass
                elif status == 'PENDING_APPROVAL':
                    is_approved = False
                    is_pending = True
                elif status == 'REJECTED':
                    is_approved = False
                # If multiple profiles exist, pending/rejected should override
            except model.DoesNotExist:
                continue
        # Users with no profile treated as approved (public users)
        if not has_profile:
            is_approved = True
            is_pending = False
    else:
        is_approved = False
        is_pending = False
        is_doctor = False

    return {
        'is_approved': is_approved,
        'is_pending': is_pending,
        'is_doctor': is_doctor,
    }


def active_referrals_count(request):
    """Context processor to add active referrals count to all templates"""
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            # For staff/admin, count all active referrals
            # Use the same queryset structure as admin_patient_list view for consistency
            base_qs = Referral.objects.select_related('patient', 'patient__facility', 'user')
            active_count = base_qs.filter(status__in=['pending', 'in-progress']).count()
        else:
            # For regular users, count active referrals from their assigned facilities
            user_facilities = request.user.shared_facilities.all()
            if user_facilities.exists():
                from django.db.models import Q
                base_qs = Referral.objects.select_related('patient', 'patient__facility', 'user')
                active_count = base_qs.filter(
                    Q(facility__in=user_facilities) | Q(patient__facility__in=user_facilities),
                    status__in=['pending', 'in-progress']
                ).count()
            else:
                active_count = 0
        return {
            'active_referrals_count': active_count,
        }
    return {
        'active_referrals_count': 0,
    }


def followups_count(request):
    """Context processor to add follow-ups count to all templates"""
    if request.user.is_authenticated:
        # Get follow-ups for the Follow-ups tab
        # Filter by facility unless user is admin
        followups_qs = Medical_History.objects.filter(
            followup_date__isnull=False
        ).select_related('patient_id', 'patient_id__facility', 'user_id', 'referral', 'referral__examined_by')
        
        # Check if user is a doctor
        is_doctor = False
        try:
            doctor_profile = Doctors.objects.get(user=request.user)
            if doctor_profile.status == 'ACTIVE':
                is_doctor = True
        except Doctors.DoesNotExist:
            pass
        
        if not (request.user.is_staff or request.user.is_superuser):
            # Doctors can see all follow-ups (no filter)
            # For non-doctor users (BHW), filter by facility
            if not is_doctor:
                user_facilities = request.user.shared_facilities.all()
                if user_facilities.exists():
                    followups_qs = followups_qs.filter(patient_id__facility__in=user_facilities)
                else:
                    followups_qs = followups_qs.none()
        
        # Get all completed follow-up visit medical_history IDs for efficient lookup
        completed_medical_history_ids = set(
            FollowUpVisit.objects.filter(
                status='completed',
                medical_history__in=followups_qs
            ).values_list('medical_history_id', flat=True)
        )
        
        # Count only non-completed follow-ups
        today = datetime.now().date()
        followups_count = 0
        
        for followup in followups_qs:
            # Check if there's a completed follow-up visit
            has_completed_visit = followup.history_id in completed_medical_history_ids
            
            if not has_completed_visit:
                # Count non-completed follow-ups for the badge
                followups_count += 1
        
        return {
            'followups_count': int(followups_count) if followups_count else 0,
        }
    return {
        'followups_count': 0,
    }


def user_facility(request):
    """Context processor to add user's facility name to all templates"""
    if request.user.is_authenticated:
        # Check if user is BHW and get their facility
        try:
            bhw_profile = BHWRegistration.objects.select_related('facility').get(user=request.user)
            if bhw_profile.facility:
                return {
                    'user_facility': bhw_profile.facility.name,
                }
        except BHWRegistration.DoesNotExist:
            pass
        
        # Check if user has shared facilities
        facilities = request.user.shared_facilities.all()
        if facilities.exists():
            return {
                'user_facility': facilities.first().name,
            }
    
    return {
        'user_facility': None,
    }