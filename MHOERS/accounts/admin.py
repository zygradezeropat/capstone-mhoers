from django.contrib import admin
from .models import UserConsent, AccountDeletionRequest

@admin.register(UserConsent)
class UserConsentAdmin(admin.ModelAdmin):
    list_display = ('user', 'privacy_policy_accepted', 'data_processing_consent', 'marketing_consent', 'consent_version', 'updated_at')
    list_filter = ('privacy_policy_accepted', 'data_processing_consent', 'marketing_consent', 'consent_version')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(AccountDeletionRequest)
class AccountDeletionRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'requested_at', 'scheduled_deletion_date', 'completed_at')
    list_filter = ('status', 'requested_at', 'scheduled_deletion_date')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('requested_at',)
    date_hierarchy = 'requested_at'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Deletion Request Details', {
            'fields': ('status', 'requested_at', 'scheduled_deletion_date', 'completed_at')
        }),
        ('Additional Information', {
            'fields': ('cancellation_reason', 'notes'),
            'classes': ('collapse',)
        }),
    )
