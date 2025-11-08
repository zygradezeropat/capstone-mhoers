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