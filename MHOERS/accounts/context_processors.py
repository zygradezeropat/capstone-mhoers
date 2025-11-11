from accounts.models import BHWRegistration, Doctors, Nurses
from referrals.models import Referral

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
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        has_profile = False
        for model in (BHWRegistration, Doctors, Nurses):
            try:
                profile = model.objects.get(user=user)
                has_profile = True
                status = getattr(profile, 'status', None)
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

    return {
        'is_approved': is_approved,
        'is_pending': is_pending,
    }


def active_referrals_count(request):
    """Context processor to add active referrals count to all templates"""
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            # For staff/admin, count all active referrals
            active_count = Referral.objects.filter(status__in=['pending', 'in-progress']).count()
        else:
            # For regular users, count active referrals from their assigned facilities
            user_facilities = request.user.shared_facilities.all()
            if user_facilities.exists():
                from django.db.models import Q
                active_count = Referral.objects.filter(
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