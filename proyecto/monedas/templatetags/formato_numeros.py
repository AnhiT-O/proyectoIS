from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='formateado')
def formateado(value, max_decimals=2):
    """
    Formatea un número con separador de miles y decimales solo si existen.

    Uso: {{ valor|formateado }} o {{ valor|formateado:4 }}
    """
    try:
        # Convertir a Decimal para mayor precisión
        if value is None or value == '':
            return ''
        
        num = Decimal(str(value))
        
        # Verificar si tiene decimales
        if num % 1 == 0:
            # Sin decimales
            return '{:,.0f}'.format(num).replace(',', '.')
        else:
            # Con decimales - limitar a max_decimals
            format_str = f'{{:,.{max_decimals}f}}'
            formatted = format_str.format(num)
            
            # Eliminar ceros innecesarios al final
            formatted = formatted.rstrip('0').rstrip('.')
            
            # Reemplazar separadores (punto por coma para miles)
            return formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
            
    except (ValueError, TypeError, AttributeError):
        return value