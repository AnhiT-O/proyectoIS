"""
Formularios para el sistema de transacciones de Global Exchange.

Este módulo contiene los formularios utilizados en el proceso de transacciones,
incluyendo la selección de monedas, montos y configuración de recargos.

Formularios principales:
    - SeleccionMonedaMontoForm: Selección de moneda y monto para transacciones
    - RecargoForm: Gestión de recargos por medio de pago
"""

from django import forms
from monedas.models import Moneda
from decimal import Decimal


class SeleccionMonedaMontoForm(forms.Form):
    """
    Formulario para seleccionar moneda y monto en operaciones de compra/venta.
    
    Este formulario permite al usuario seleccionar la moneda extranjera
    y especificar el monto que desea comprar o vender. Incluye validaciones
    específicas para cada moneda según sus decimales configurados.
    
    Fields:
        moneda (ModelChoiceField): Selector de moneda activa del sistema
        monto (DecimalField): Monto en la moneda seleccionada
        
    Validaciones:
        - El monto debe ser positivo y mayor al mínimo permitido
        - Se respetan los decimales configurados para cada moneda
        - Consistente con el comportamiento del simulador
    """
    
    moneda = forms.ModelChoiceField(
        queryset=Moneda.objects.filter(activa=True),
        empty_label="",
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
            'step': '1',
            'min': '1'
        }),
        required=True,
        error_messages={'required': 'Debes ingresar un monto numérico.'}
    )

    def clean(self):
        """
        Validación personalizada para el monto en moneda extranjera.
        
        Realiza validaciones específicas sobre el monto ingresado:
        - Verifica que sea un valor positivo
        - Comprueba que respete el monto mínimo según los decimales de la moneda
        - Convierte el monto a tipo Decimal para precisión
        
        Returns:
            dict: Datos limpios del formulario incluyendo monto_decimal
            
        Raises:
            ValidationError: Si el monto no cumple las validaciones
        """
        cleaned_data = super().clean()
        moneda = cleaned_data.get('moneda')
        monto = cleaned_data.get('monto')
        
        if monto is not None and moneda is not None:
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

class RecargoForm(forms.ModelForm):
    """
    Formulario para la gestión de recargos por medio de pago.
    
    Permite a los administradores editar los porcentajes de recargo
    aplicables a diferentes medios de pago en las transacciones.
    
    Fields:
        recargo (IntegerField): Porcentaje de recargo (0-100)
        
    Validaciones:
        - El recargo debe ser un valor numérico entero
        - Rango permitido de 0 a 100 por ciento
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
