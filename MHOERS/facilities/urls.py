from django.urls import path
from .views import *

app_name = 'facilities'

urlpatterns = [
    path('create_provider/', create_provider, name='create_provider'),
    path('api/facilities/', facility_list, name='facility_list'),
    path('update_facility/', update_facility, name='update_facility'),
    path('delete_facility/', delete_facility, name='delete_facility'),
]
