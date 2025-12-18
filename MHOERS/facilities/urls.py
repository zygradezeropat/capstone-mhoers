from django.urls import path
from .views import *

app_name = 'facilities'

urlpatterns = [
    path('create_provider/', create_provider, name='create_provider'),
    path('create_facility/', create_facility, name='create_facility'),
    path('create_barangay/', create_barangay, name='create_barangay'),
    path('create_purok/', create_purok, name='create_purok'),
    path('api/facilities/', facility_list, name='facility_list'),
    path('api/barangays/', get_barangays, name='get_barangays'),
    path('api/psgc-provinces/', psgc_provinces, name='psgc_provinces'),
    path('api/psgc-cities/', psgc_cities, name='psgc_cities'),
    path('api/psgc-barangays/', psgc_barangays, name='psgc_barangays'),
    path('api/puroks/', get_puroks_by_barangay, name='get_puroks_by_barangay'),
    path('update_facility/', update_facility, name='update_facility'),
    path('delete_facility/', delete_facility, name='delete_facility'),
]
