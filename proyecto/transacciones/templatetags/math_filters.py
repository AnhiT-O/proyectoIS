from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    """Sustrae arg de value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0