from django import template

register = template.Library()

@register.filter(name='tiene_acceso_tasas')
def tiene_acceso_tasas(user):
    """Verifica si el usuario tiene acceso a la gestión de tasas"""
    return user.groups.filter(name__in=['administrador', 'analista cambiario']).exists()
