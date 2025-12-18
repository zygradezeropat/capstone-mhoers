from django.contrib import admin
from .models import UserConsent, AccountDeletionRequest, ApprovedBHW, ApprovedDoctor

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

@admin.register(ApprovedBHW)
class ApprovedBHWAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'registration_number', 'accreditation_number', 'barangay', 'is_active', 'created_at']
    list_filter = ['is_active', 'barangay', 'created_at']
    search_fields = ['first_name', 'last_name', 'middle_name', 'registration_number', 'accreditation_number', 'email', 'phone', 'barangay']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'middle_name', 'last_name', 'phone', 'email', 'barangay')
        }),
        ('Professional Information', {
            'fields': ('registration_number', 'accreditation_number')
        }),
        ('Status & Notes', {
            'fields': ('is_active', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ApprovedDoctor)
class ApprovedDoctorAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'specialization', 'license_number', 'barangay', 'is_active', 'created_at']
    list_filter = ['is_active', 'specialization', 'barangay', 'created_at']
    search_fields = ['first_name', 'last_name', 'middle_name', 'license_number', 'specialization', 'email', 'phone', 'barangay']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'middle_name', 'last_name', 'phone', 'email', 'barangay')
        }),
        ('Professional Information', {
            'fields': ('specialization', 'license_number')
        }),
        ('Status & Notes', {
            'fields': ('is_active', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
