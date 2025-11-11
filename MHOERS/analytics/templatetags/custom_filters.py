from django import template
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
    
    # Handle string values like "No prediction available"
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