from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.conf import settings

import requests

from .forms import HealthcareProviderForm, FacilityForm
from facilities.models import Facility, Barangay, Purok


def create_provider(request):
    facilities = Facility.objects.all()
    if request.method == 'POST':
        form = HealthcareProviderForm(request.POST)
        if form.is_valid():
            # Create facility only (no user account)
            facility_name = form.cleaned_data.get('name') or form.cleaned_data.get('username', 'Facility')
            if Facility.objects.filter(name__iexact=facility_name).exists():
                messages.error(request, "A facility with this name already exists.")
                return redirect('user_management')
            
            facility = Facility.objects.create(
                name=facility_name,
                assigned_bhw=f"{form.cleaned_data.get('first_name', '')} {form.cleaned_data.get('last_name', '')}".strip(),
                latitude=form.cleaned_data.get('latitude', 0),
                longitude=form.cleaned_data.get('longitude', 0)
            )

            messages.success(request, "Facility created successfully.")
            return redirect('user_management')
    else:
        form = HealthcareProviderForm()
    
    return redirect('user_management')

@login_required
def create_facility(request):
    if request.method == 'POST':
        form = FacilityForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            if Facility.objects.filter(name__iexact=name).exists():
                messages.error(request, "A facility with this name already exists.")
                return redirect('user_management')
            try:
                Facility.objects.create(
                    name=name,
                    assigned_bhw=form.cleaned_data['assigned_bhw'],
                    barangay=form.cleaned_data.get('barangay', ''),
                    latitude=form.cleaned_data['latitude'],
                    longitude=form.cleaned_data['longitude']
                )
                messages.success(request, "Facility created successfully.")
            except IntegrityError:
                messages.error(request, "A facility with this name already exists.")
            except Exception as e:
                messages.error(request, f"Error creating facility: {str(e)}")
        else:
            messages.error(request, "Please correct the errors in the form.")
    return redirect('user_management')

def facility_list(request):
    facilities = Facility.objects.all()
    data = [{
        'facility_id': facility.facility_id,
        'name': facility.name,
        'assigned_bhw': facility.assigned_bhw,
        'barangay': facility.barangay or '',
        'latitude': facility.latitude,
        'longitude': facility.longitude,
        'user_ids': [user.id for user in facility.users.all()]
    } for facility in facilities]
    return JsonResponse(data, safe=False)

@login_required
def update_facility(request):
    if request.method == 'POST':
        try:
            facility_id = request.POST.get('facility_id')
            facility = Facility.objects.get(facility_id=facility_id)
            
            # Update facility details
            new_name = request.POST.get('facility_name')
            # Enforce uniqueness on rename
            if Facility.objects.filter(name__iexact=new_name).exclude(facility_id=facility.facility_id).exists():
                messages.error(request, "A facility with this name already exists.")
                return redirect(reverse('user_management') + '?active_tab=tab2')

            facility.name = new_name
            facility.assigned_bhw = request.POST.get('assigned_bhw', '').strip()
            facility.barangay = request.POST.get('barangay', '')
            facility.latitude = float(request.POST.get('latitude', 0))
            facility.longitude = float(request.POST.get('longitude', 0))
            facility.save()
            
            messages.success(request, "Facility information updated successfully.")
        except Facility.DoesNotExist:
            messages.error(request, "Facility not found.")
        except Exception as e:
            messages.error(request, f"Error updating facility: {str(e)}")
    
    # Redirect to user_management with the facilities tab active
    return redirect(reverse('user_management') + '?active_tab=tab2')

@login_required
def delete_facility(request):
    if request.method == 'POST':
        try:
            facility_id = request.POST.get('facility_id')
            facility = Facility.objects.get(facility_id=facility_id)
            
            # Get facility name for message
            facility_name = facility.name
            
            # Delete the facility (Django will automatically handle ManyToMany cleanup)
            facility.delete()
            
            messages.success(request, f"Facility '{facility_name}' deleted successfully.")
        except Facility.DoesNotExist:
            messages.error(request, "Facility not found.")
        except Exception as e:
            messages.error(request, f"Error deleting facility: {str(e)}")
    
    # Redirect to user_management with the facilities tab active
    return redirect(reverse('user_management') + '?active_tab=tab2')

@login_required
def create_barangay(request):
    """Create a new barangay"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            # Checkbox sends 'true' if checked, nothing if unchecked
            is_active = request.POST.get('is_active') == 'true'
            
            if not name:
                messages.error(request, "Barangay name is required.")
                return redirect('user_management')
            
            # Check if barangay with same name already exists
            if Barangay.objects.filter(name__iexact=name).exists():
                messages.error(request, "A barangay with this name already exists.")
                return redirect('user_management')
            
            # Create the barangay
            barangay = Barangay.objects.create(
                name=name,
                is_active=is_active
            )
            
            messages.success(request, f"Barangay '{barangay.name}' created successfully.")
        except IntegrityError:
            messages.error(request, "A barangay with this name already exists.")
        except Exception as e:
            messages.error(request, f"Error creating barangay: {str(e)}")
    
    return redirect('user_management')

@login_required
def create_purok(request):
    """Create a new purok"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            barangay_id = request.POST.get('barangay_id', '').strip()
            # Checkbox sends 'true' if checked, nothing if unchecked
            is_active = request.POST.get('is_active') == 'true'
            
            if not name:
                messages.error(request, "Purok name is required.")
                return redirect('user_management')
            
            if not barangay_id:
                messages.error(request, "Barangay selection is required.")
                return redirect('user_management')
            
            try:
                barangay = Barangay.objects.get(barangay_id=barangay_id)
            except Barangay.DoesNotExist:
                messages.error(request, "Selected barangay not found.")
                return redirect('user_management')
            
            # Check if purok with same name already exists in this barangay
            if Purok.objects.filter(barangay=barangay, name__iexact=name).exists():
                messages.error(request, f"A purok with this name already exists in {barangay.name}.")
                return redirect('user_management')
            
            # Create the purok
            purok = Purok.objects.create(
                barangay=barangay,
                name=name,
                is_active=is_active
            )
            
            messages.success(request, f"Purok '{purok.name}' created successfully in {barangay.name}.")
        except IntegrityError:
            messages.error(request, "A purok with this name already exists in the selected barangay.")
        except Exception as e:
            messages.error(request, f"Error creating purok: {str(e)}")
    
    return redirect('user_management')

def get_barangays(request):
    """API endpoint to get all active barangays, optionally filtered by city/municipality"""
    try:
        city = request.GET.get('city', '').strip()
        barangays = Barangay.objects.filter(is_active=True)
        
        # If city is provided, filter barangays (this is a simple name-based filter)
        # In a real scenario, you'd want a proper city field in the Barangay model
        if city:
            # Filter by city name in barangay name or use a mapping
            # For now, we'll return all and let frontend filter based on mapping
            pass
        
        barangays = barangays.order_by('name')
        data = [{
            'barangay_id': barangay.barangay_id,
            'name': barangay.name
        } for barangay in barangays]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def psgc_provinces(request):
    """Get Mindanao provinces from PSGC API."""
    try:
        # Try multiple PSGC API endpoints
        api_endpoints = [
            'https://psgc.rootscratch.com/api/provinces',
            'https://psgc.cloud/api/provinces',
        ]
        
        provinces = []
        mindanao_codes = ['09', '10', '11', '12', '13', '14', '15', '16', '18']
        
        for endpoint in api_endpoints:
            try:
                response = requests.get(endpoint, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Handle different response formats
                provinces_list = []
                if isinstance(data, list):
                    provinces_list = data
                elif isinstance(data, dict):
                    if 'data' in data:
                        provinces_list = data['data']
                    elif 'results' in data:
                        provinces_list = data['results']
                    elif 'provinces' in data:
                        provinces_list = data['provinces']
                
                # Filter for Mindanao provinces
                for province in provinces_list:
                    code = str(province.get('code', province.get('psgc_code', '')))[:2]
                    if code in mindanao_codes:
                        province_name = province.get('name', province.get('province_name', ''))
                        if province_name:
                            # Avoid duplicates
                            if not any(p['name'] == province_name for p in provinces):
                                provinces.append({
                                    'name': province_name,
                                    'id': province.get('code', province.get('psgc_code', '')).lower()
                                })
                
                if provinces:
                    break  # Success, stop trying other endpoints
            except:
                continue  # Try next endpoint
        
        # If still no provinces, use hardcoded Mindanao list as fallback
        if not provinces:
            mindanao_provinces = [
                'Agusan del Norte', 'Agusan del Sur', 'Basilan', 'Bukidnon', 'Camiguin',
                'Davao de Oro', 'Davao del Norte', 'Davao del Sur', 'Davao Occidental', 
                'Davao Oriental', 'Dinagat Islands', 'Lanao del Norte', 'Lanao del Sur', 
                'Maguindanao', 'Misamis Occidental', 'Misamis Oriental', 'Sarangani', 
                'South Cotabato', 'Sultan Kudarat', 'Sulu', 'Surigao del Norte', 
                'Surigao del Sur', 'Tawi-Tawi', 'Zamboanga del Norte', 
                'Zamboanga del Sur', 'Zamboanga Sibugay', 'Cotabato'
            ]
            provinces = [{'name': p, 'id': p.lower().replace(' ', '-')} for p in mindanao_provinces]
        
        return JsonResponse(provinces, safe=False)
    except Exception as e:
        return JsonResponse({'error': f'Failed to contact PSGC API: {str(e)}'}, status=502)

def psgc_cities(request):
    """Get cities/municipalities for a selected province from PSGC API."""
    province = request.GET.get('province', '').strip()
    if not province:
        return JsonResponse({'error': 'Province parameter is required.'}, status=400)
    
    try:
        api_base_urls = [
            'https://psgc.rootscratch.com/api',
            'https://psgc.cloud/api',
        ]
        
        province_code = None
        cities = []
        
        # Find province code
        for base_url in api_base_urls:
            try:
                province_response = requests.get(
                    f'{base_url}/provinces',
                    params={'q': province, 'name': province},
                    timeout=10,
                )
                if province_response.status_code == 200:
                    province_data = province_response.json()
                    provinces_list = []
                    if isinstance(province_data, list):
                        provinces_list = province_data
                    elif isinstance(province_data, dict):
                        provinces_list = province_data.get('data', province_data.get('results', []))
                    
                    for prov in provinces_list:
                        prov_name = prov.get('name', prov.get('province_name', ''))
                        if prov_name.lower() == province.lower():
                            province_code = prov.get('code', prov.get('psgc_code', ''))
                            break
                    
                    if province_code:
                        # Get cities for this province
                        cities_response = requests.get(
                            f'{base_url}/provinces/{province_code}/cities',
                            timeout=10,
                        )
                        if cities_response.status_code == 200:
                            cities_data = cities_response.json()
                            cities_list = []
                            if isinstance(cities_data, list):
                                cities_list = cities_data
                            elif isinstance(cities_data, dict):
                                cities_list = cities_data.get('data', cities_data.get('results', []))
                            
                            for city in cities_list:
                                city_name = city.get('name', city.get('city_name', ''))
                                if city_name:
                                    cities.append({
                                        'name': city_name,
                                        'id': city.get('code', city.get('psgc_code', '')),
                                    })
                        
                        # Get municipalities
                        municipalities_response = requests.get(
                            f'{base_url}/provinces/{province_code}/municipalities',
                            timeout=10,
                        )
                        if municipalities_response.status_code == 200:
                            municipalities_data = municipalities_response.json()
                            municipalities_list = []
                            if isinstance(municipalities_data, list):
                                municipalities_list = municipalities_data
                            elif isinstance(municipalities_data, dict):
                                municipalities_list = municipalities_data.get('data', municipalities_data.get('results', []))
                            
                            for municipality in municipalities_list:
                                municipality_name = municipality.get('name', municipality.get('municipality_name', ''))
                                if municipality_name and not any(c['name'] == municipality_name for c in cities):
                                    cities.append({
                                        'name': municipality_name,
                                        'id': municipality.get('code', municipality.get('psgc_code', '')),
                                    })
                        
                        if cities:
                            break  # Success
            except:
                continue
        
        if not cities:
            return JsonResponse({'error': 'No cities/municipalities found for this province'}, status=404)
        
        return JsonResponse(cities, safe=False)
    except Exception as e:
        return JsonResponse({'error': f'Failed to contact PSGC API: {str(e)}'}, status=502)

def psgc_barangays(request):
    """Get barangays for a selected city/municipality from PSGC API."""
    city = request.GET.get('city', '').strip()
    province = request.GET.get('province', '').strip()
    if not city:
        return JsonResponse({'error': 'City parameter is required.'}, status=400)
    
    try:
        api_base_urls = [
            'https://psgc.rootscratch.com/api',
            'https://psgc.cloud/api',
        ]
        
        city_code = None
        barangays = []
        
        # Find city/municipality code
        for base_url in api_base_urls:
            try:
                # Try cities first
                city_response = requests.get(
                    f'{base_url}/cities',
                    params={'q': city, 'name': city},
                    timeout=10,
                )
                
                if city_response.status_code == 200:
                    city_data = city_response.json()
                    cities_list = []
                    if isinstance(city_data, list):
                        cities_list = city_data
                    elif isinstance(city_data, dict):
                        cities_list = city_data.get('data', city_data.get('results', []))
                    
                    for c in cities_list:
                        city_name = c.get('name', c.get('city_name', ''))
                        if city_name.lower() == city.lower():
                            city_code = c.get('code', c.get('psgc_code', ''))
                            break
                
                # If not found, try municipalities
                if not city_code:
                    municipality_response = requests.get(
                        f'{base_url}/municipalities',
                        params={'q': city, 'name': city},
                        timeout=10,
                    )
                    if municipality_response.status_code == 200:
                        municipality_data = municipality_response.json()
                        municipalities_list = []
                        if isinstance(municipality_data, list):
                            municipalities_list = municipality_data
                        elif isinstance(municipality_data, dict):
                            municipalities_list = municipality_data.get('data', municipality_data.get('results', []))
                        
                        for m in municipalities_list:
                            municipality_name = m.get('name', m.get('municipality_name', ''))
                            if municipality_name.lower() == city.lower():
                                city_code = m.get('code', m.get('psgc_code', ''))
                                break
                
                if city_code:
                    # Get barangays
                    barangays_response = requests.get(
                        f'{base_url}/cities/{city_code}/barangays',
                        timeout=10,
                    )
                    
                    if barangays_response.status_code != 200:
                        barangays_response = requests.get(
                            f'{base_url}/municipalities/{city_code}/barangays',
                            timeout=10,
                        )
                    
                    if barangays_response.status_code == 200:
                        barangays_data = barangays_response.json()
                        barangays_list = []
                        if isinstance(barangays_data, list):
                            barangays_list = barangays_data
                        elif isinstance(barangays_data, dict):
                            barangays_list = barangays_data.get('data', barangays_data.get('results', []))
                        
                        for barangay in barangays_list:
                            barangay_name = barangay.get('name', barangay.get('barangay_name', ''))
                            if barangay_name:
                                barangays.append({
                                    'name': barangay_name,
                                    'id': barangay.get('code', barangay.get('psgc_code', '')),
                                })
                        
                        if barangays:
                            break  # Success
            except:
                continue
        
        if not barangays:
            return JsonResponse({'error': 'No barangays found for this city/municipality'}, status=404)
        
        return JsonResponse(barangays, safe=False)
    except Exception as e:
        return JsonResponse({'error': f'Failed to contact PSGC API: {str(e)}'}, status=502)

def get_puroks_by_barangay(request):
    """API endpoint to get puroks for a selected barangay - supports both barangay_id and barangay name"""
    barangay_id = request.GET.get('barangay_id')
    barangay_name = request.GET.get('barangay', '').strip()
    
    if not barangay_id and not barangay_name:
        return JsonResponse({'error': 'barangay_id or barangay name is required'}, status=400)
    
    try:
        # Try to find barangay by ID first, then by name
        if barangay_id:
            barangay = Barangay.objects.get(barangay_id=barangay_id, is_active=True)
        else:
            # Find by name (case-insensitive)
            barangay = Barangay.objects.filter(name__iexact=barangay_name, is_active=True).first()
            if not barangay:
                return JsonResponse({'error': 'Barangay not found'}, status=404)
        
        puroks = Purok.objects.filter(barangay=barangay, is_active=True).order_by('name')
        
        data = [{
            'purok_id': purok.purok_id,
            'name': purok.name
        } for purok in puroks]
        
        return JsonResponse(data, safe=False)
    except Barangay.DoesNotExist:
        return JsonResponse({'error': 'Barangay not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)