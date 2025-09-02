from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='percentage')
def percentage(value):
    if value is None:
        return "0%"
    try:
        return f"{float(value) * 100:.0f}%"
    except (ValueError, TypeError):
        return "0%"
