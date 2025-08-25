from django.db.models import Prefetch, Q, Count
from referrals.models import Referral
from patients.models import Patient
from facilities.models import Facility

class ReferralQueryOptimizer:
    """Optimizes database queries for referral data"""
    
    @classmethod
    def get_optimized_referrals(cls, status_filter=None):
        """Get referrals with optimized queries"""
        queryset = Referral.objects.select_related(
            'patient',
            'patient__facility',
            'user'
        ).prefetch_related(
            'patient__medical_history_set'
        )
        
        if status_filter:
            if isinstance(status_filter, list):
                queryset = queryset.filter(status__in=status_filter)
            else:
                queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')
    
    @classmethod
    def get_active_referrals(cls):
        """Get active referrals with optimized queries"""
        return cls.get_optimized_referrals(['in-progress', 'pending'])
    
    @classmethod
    def get_completed_referrals(cls):
        """Get completed referrals with optimized queries"""
        return cls.get_optimized_referrals('completed')
    
    @classmethod
    def get_all_referrals(cls):
        """Get all referrals with optimized queries"""
        return cls.get_optimized_referrals(['pending', 'in-progress', 'completed', 'rejected'])
    
    @classmethod
    def get_patients_with_referral_count(cls):
        """Get patients with referral count using optimized queries"""
        return Patient.objects.select_related('facility').annotate(
            referral_count=Count('referral')
        ).prefetch_related('referral_set')
