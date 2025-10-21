from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import HealthcareProviderForm
from facilities.models import Facility
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


def create_provider(request):
    facilities = Facility.objects.all()
    if request.method == 'POST':
        form = HealthcareProviderForm(request.POST)
        if form.is_valid():
            # Check password match
            if form.cleaned_data['password1'] != form.cleaned_data['password2']:
                messages.error(request, "Passwords do not match.")
                return render(request, 'accounts/user_management.html', {'form': form, 'active_page': 'user_management'})

            # Create user
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
            )

            # Create facility and assign to user
            Facility.objects.create(
                name=f"{form.cleaned_data['username']}",
                assigned_bhw=f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}",
                latitude=form.cleaned_data['latitude'],
                longitude=form.cleaned_data['longitude'],
                user_id=user
            )

            messages.success(request, "Healthcare provider and facility created.")
            return render(request, 'accounts/user_management.html', {'facilities': facilities,'form': form, 'active_page': 'user_management'})
    else:
        form = HealthcareProviderForm()
        return render(request, 'accounts/user_management.html', {'facilities': facilities,'form': form, 'active_page': 'user_management'})
    
    return render(request, 'accounts/user_management.html', {'facilities': facilities,'form': form, 'active_page': 'user_management'})

def facility_list(request):
    facilities = Facility.objects.all()
    data = [{
        'facility_id': facility.facility_id,
        'name': facility.name,
        'assigned_bhw': facility.assigned_bhw,
        'latitude': facility.latitude,
        'longitude': facility.longitude,
        'user_id': facility.user_id.id if facility.user_id else None
    } for facility in facilities]
    return JsonResponse(data, safe=False)

@login_required
def update_facility(request):
    facilities = Facility.objects.all()
    if request.method == 'POST':
        try:
            facility_id = request.POST.get('facility_id')
            facility = Facility.objects.get(facility_id=facility_id)
            user = facility.user_id
            
            # Update facility details
            facility.name = request.POST.get('facility_name')
            facility.assigned_bhw = f"{request.POST.get('first_name')} {request.POST.get('last_name')}"
            facility.latitude = float(request.POST.get('latitude'))
            facility.longitude = float(request.POST.get('longitude'))
            facility.save()
            
            # Update user details
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            
            # Update password if provided
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            if password1 and password2:
                if password1 != password2:
                    messages.error(request, "Passwords do not match.")
                    return render(request, 'accounts/user_management.html', {'facilities': facilities, 'active_page': 'user_management'})
                user.set_password(password1)
            
            user.save()
            
            messages.success(request, "Facility and user information updated successfully.")
        except Facility.DoesNotExist:
            messages.error(request, "Facility not found.")
        except Exception as e:
            messages.error(request, f"Error updating facility: {str(e)}")
            
    return render(request, 'accounts/user_management.html', {'facilities': facilities, 'active_page': 'user_management'})

@login_required
def delete_facility(request):
    if request.method == 'POST':
        try:
            facility_id = request.POST.get('facility_id')
            facility = Facility.objects.get(facility_id=facility_id)
            
            # Get the associated user before deleting the facility
            user = facility.user_id
            
            # Delete the facility
            facility.delete()
            
            # Delete the associated user
            user.delete()
            
            messages.success(request, "Facility and associated user deleted successfully.")
        except Facility.DoesNotExist:
            messages.error(request, "Facility not found.")
        except Exception as e:
            messages.error(request, f"Error deleting facility: {str(e)}")
    
    # Get updated facilities list for the template
    facilities = Facility.objects.all()
    return render(request, 'accounts/user_management.html', {'facilities': facilities, 'active_page': 'user_management'})