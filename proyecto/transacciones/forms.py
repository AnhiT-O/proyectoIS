from django import forms
from monedas.models import Moneda
from decimal import Decimal


class SeleccionMonedaMontoForm(forms.Form):
    """
    Formulario para seleccionar la moneda y el monto para compra.
    Comportamiento consistente con el simulador para operaciones de compra.
    """
    
    moneda = forms.ModelChoiceField(
        queryset=Moneda.objects.filter(activa=True),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_moneda'
        }),
        label='Moneda a comprar',
        required=False
    )

    monto = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'id_monto',
            'placeholder': 'Ingrese el monto en la moneda extranjera',
            'step': '0.01',
            'min': '0.01'
        }),
        label='Monto a comprar',
        required=False
    )

    def clean(self):
        """
        Validación personalizada para monto en moneda extranjera.
        Similar al modo "venta" del simulador pero para operación de compra.
        """
        cleaned_data = super().clean()
        moneda = cleaned_data.get('moneda')
        monto = cleaned_data.get('monto', None)

        # Validar moneda requerida
        if not moneda:
            self.add_error('moneda', 'Debe seleccionar una moneda.')
            return cleaned_data
        
        # Validar monto requerido y mínimo
        if not monto:
            self.add_error('monto', 'El monto es obligatorio.')
            return cleaned_data
        
        try:
            monto = Decimal(monto)
            if monto <= 0:
                self.add_error('monto', 'El monto debe ser mayor a 0.')
                return cleaned_data
            
            # Para monto en moneda extranjera, usar los decimales de la moneda seleccionada
            monto_minimo = Decimal('1') / (Decimal('10') ** moneda.decimales)
            if monto < monto_minimo:
                self.add_error('monto', f'El monto mínimo para {moneda.nombre} es {monto_minimo} {moneda.simbolo}.')
                return cleaned_data
                
        except (ValueError, TypeError):
            self.add_error('monto', 'Por favor, ingrese un monto válido.')
            return cleaned_data
        
        # Agregar el monto convertido a los datos limpios
        cleaned_data['monto_decimal'] = monto
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar el widget de moneda para mostrar símbolo y nombre, con datos para JS
        monedas_choices = []
        monedas_data = {}
        for moneda in Moneda.objects.filter(activa=True):
            choice_text = f"{moneda.simbolo} - {moneda.nombre}"
            monedas_choices.append((moneda.pk, choice_text))
            monedas_data[str(moneda.pk)] = {
                'simbolo': moneda.simbolo,
                'decimales': moneda.decimales
            }
        
        self.fields['moneda'].choices = [('', 'Seleccione una moneda')] + monedas_choices
        
        # Agregar atributos data para JavaScript dinámico
        import json
        self.fields['moneda'].widget.attrs.update({
            'data-monedas': json.dumps(monedas_data)
        })
