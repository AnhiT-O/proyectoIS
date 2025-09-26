from django import template

register = template.Library()

@register.filter
def add_class(field, css_class):
    """
    Añade una clase CSS a un campo de formulario
    """
    return field.as_widget(attrs={'class': css_class})

@register.filter
def format_number(value):
    """
    Formatea un número agregando puntos como separadores de miles
    Ejemplo: 90000000 -> 90.000.000
    """
    if not value:
        return value
    try:
        # Convertir a entero para eliminar decimales
        num = int(float(value))
        # Formatear con puntos como separadores de miles
        return "{:,}".format(num).replace(',', '.')
    except (ValueError, TypeError):
        return value