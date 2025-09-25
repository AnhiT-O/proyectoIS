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
        required=True,
        error_messages={'required': 'Debes seleccionar una moneda.'}
    )

    monto = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'id_monto',
            'placeholder': 'Ingresa el monto en la moneda extranjera',
            'step': '0.01',
            'min': '0.01'
        }),
        required=True,
        error_messages={'required': 'Debes ingresar un monto numérico.'}
    )

    def clean(self):
        """
        Validación personalizada para monto en moneda extranjera.
        Similar al modo "venta" del simulador pero para operación de compra.
        """
        cleaned_data = super().clean()
        moneda = cleaned_data.get('moneda')
        monto = cleaned_data.get('monto')
        
        if monto is not None:
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
        
        self.fields['moneda'].choices = [('', 'Selecciona una moneda')] + monedas_choices

        # Modificar el widget para que la opción inicial sea disabled, selected y hidden
        self.fields['moneda'].widget.choices = self.fields['moneda'].choices
        self.fields['moneda'].widget.attrs['onchange'] = "this.options[0].setAttribute('hidden', 'hidden');"
        # Usar render_option para agregar los atributos (solo para Select, no para ModelChoiceField)
        original_create_option = self.fields['moneda'].widget.create_option
        def custom_create_option(*args, **kwargs):
            option_dict = original_create_option(*args, **kwargs)
            if option_dict['value'] == '':
                option_dict['attrs']['disabled'] = True
                option_dict['attrs']['selected'] = True
                option_dict['attrs']['hidden'] = True
            return option_dict
        self.fields['moneda'].widget.create_option = custom_create_option

        # Agregar atributos data para JavaScript dinámico
        import json
        self.fields['moneda'].widget.attrs.update({
            'data-monedas': json.dumps(monedas_data)
        })

class RecargoForm(forms.ModelForm):
    """
    Formulario para gestionar recargos en transacciones.
    """
    recargo = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '1',
            'min': '0',
            'placeholder': 'Ingresa el recargo en porcentaje'
        }),
        required=True,
        error_messages={
            'invalid': 'Por favor, ingresa un valor numérico válido para el recargo.'
        }
    )
    
    class Meta:
        from .models import Recargos
        model = Recargos
        fields = ['recargo']
