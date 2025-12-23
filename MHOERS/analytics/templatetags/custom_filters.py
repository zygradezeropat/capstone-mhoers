from django import template
from analytics.models import Disease
register = template.Library()

@register.filter
def dict_get(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def zip_lists(value, arg):
    try:
        return zip(value, arg)
    except TypeError:
        return []


@register.filter
def sum_values(iterable):
    try:
        return sum(iterable)
    except TypeError:
        return 0


@register.filter
def icd_to_disease(icd_code):
    """Convert ICD code to disease name with description"""
    if not icd_code:
        return icd_code
    
    # Handle string values like "No prediction available" or "Unspecified"
    if isinstance(icd_code, str):
        icd_code_str = icd_code.strip()
        # If it's already a descriptive string, return as-is
        if 'No prediction' in icd_code_str or 'Unspecified' in icd_code_str:
            return icd_code_str
    else:
        icd_code_str = str(icd_code).strip()
    
    # ICD code to disease name mapping
    icd_mapping = {
        'T14.1': 'Open Wounds',
        'W54.99': 'Dog Bites',
        'J06.9': 'Acute respiratory infections',
        'J15': 'Pneumonia',
        'I10.1': 'Hypertension Level 2',
        'I10-1': 'Hypertension Level 2',  # Alternative format
        'I10.0': 'Hypertension Level 1',
        'I10-0': 'Hypertension Level 1',  # Alternative format
    }
    
    disease_name = icd_mapping.get(icd_code_str, None)
    
    if disease_name:
        return f"{icd_code_str} - {disease_name}"
    
    # If not found in mapping, return the code as-is
    return icd_code_str


@register.filter
def icd_to_severity(icd_code):
    """Get severity (critical_level) from Disease model by ICD code"""
    if not icd_code:
        return "Unspecified"
    
    # Handle string values like "No prediction available" or "Unspecified"
    if isinstance(icd_code, str):
        icd_code_str = icd_code.strip()
        # If it's already a descriptive string, return Unspecified
        if 'No prediction' in icd_code_str or 'Unspecified' in icd_code_str:
            return "Unspecified"
    else:
        icd_code_str = str(icd_code).strip()
    
    # Try to find Disease by ICD code (exact match first)
    try:
        disease = Disease.objects.get(icd_code=icd_code_str)
        # Get the display value for critical_level (capitalize first letter)
        severity = disease.critical_level
        if severity:
            return severity.capitalize()
        return "Unspecified"
    except Disease.DoesNotExist:
        # Try alternative format (replace dots with dashes or vice versa)
        try:
            # Try with dots replaced by dashes
            alt_code = icd_code_str.replace('.', '-')
            if alt_code != icd_code_str:
                disease = Disease.objects.get(icd_code=alt_code)
                severity = disease.critical_level
                if severity:
                    return severity.capitalize()
        except Disease.DoesNotExist:
            try:
                # Try with dashes replaced by dots
                alt_code = icd_code_str.replace('-', '.')
                if alt_code != icd_code_str:
                    disease = Disease.objects.get(icd_code=alt_code)
                    severity = disease.critical_level
                    if severity:
                        return severity.capitalize()
            except Disease.DoesNotExist:
                pass
        return "Unspecified"
    except Exception:
        return "Unspecified"


@register.filter
def get_bhw_name(user):
    """Get BHW name from user. Returns BHW's first_name and last_name if user has BHWRegistration, otherwise returns user's name."""
    if not user:
        return ""
    
    try:
        from accounts.models import BHWRegistration
        bhw = BHWRegistration.objects.get(user=user)
        return f"{bhw.first_name} {bhw.last_name}".strip()
    except BHWRegistration.DoesNotExist:
        # Fallback to user's first_name and last_name
        if user.first_name or user.last_name:
            return f"{user.first_name} {user.last_name}".strip()
        return user.username
    except Exception:
        # If any error occurs, return username as fallback
        return user.username if user else ""