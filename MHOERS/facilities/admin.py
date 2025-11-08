from django.contrib import admin
from .models import Facility

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'assigned_bhw', 'latitude', 'longitude')
    filter_horizontal = ('users',)  # nice UI for selecting multiple users
