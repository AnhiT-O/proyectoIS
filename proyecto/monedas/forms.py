from django import forms
from django.core.exceptions import ValidationError
from .models import Moneda

class MonedaForm(forms.ModelForm):

    nombre = forms.CharField(
        error_messages={
            'required': 'Debes ingresar un nombre.',
            'max_length': 'El nombre no puede exceder los 30 caracteres.',
            'unique': 'Ya existe una moneda con este nombre.'
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    simbolo = forms.CharField(
        max_length=3,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'maxlength': '3',
            'style': 'text-transform: uppercase;'
        }),
        error_messages={
            'required': 'Debes ingresar un símbolo.',
            'max_length': 'El símbolo no puede exceder las 3 letras.',
            'unique': 'Ya existe una moneda con este símbolo.'
        }
    )
    tasa_base = forms.IntegerField(
        required=True,
        error_messages={
            'min_value': 'La tasa base debe ser un número positivo.',
            'required': 'Debes ingresar una tasa base.'
        },
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'type': 'number'
        })
    )
    comision_compra = forms.IntegerField(
        required=True,
        error_messages={
            'min_value': 'La comisión de compra debe ser un número positivo.',
            'required': 'Debes ingresar una comisión de compra.'
        },
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'type': 'number'
        })
    )
    comision_venta = forms.IntegerField(
        required=True,
        error_messages={
            'min_value': 'La comisión de venta debe ser un número positivo.',
            'required': 'Debes ingresar una comisión de venta.'
        },
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'type': 'number'
        })
    )
    decimales = forms.IntegerField(
        required=False,
        error_messages={
            'min_value': 'El número de decimales debe ser al menos 0.'
        },
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'step': '1',
            'type': 'number',
            'value': '3'
        })
    )

    class Meta:
        model = Moneda
        fields = ['nombre', 'simbolo', 'tasa_base', 'decimales', 'comision_compra', 'comision_venta']

    def clean_simbolo(self):
        """
        Convierte el símbolo a mayúsculas.
        """
        simbolo = self.cleaned_data.get('simbolo')
        if simbolo:
            # Convertir a mayúsculas automáticamente
            simbolo = simbolo.upper()
            
            # Validar que solo contenga letras
            if not simbolo.isalpha():
                raise ValidationError('El símbolo debe contener solo letras.')
        return simbolo

    def clean_decimales(self):
        value = self.cleaned_data.get('decimales')
        return value if value is not None else 3

    def clean_tasa_base(self):
        """
        Valida que la tasa base sea un número positivo.
        """
        tasa_base = self.cleaned_data.get('tasa_base')
        if tasa_base is not None and tasa_base < 0:
            raise ValidationError('La tasa base debe ser un número positivo.')
        return tasa_base

    def clean_comision_compra(self):
        """
        Valida que la comisión de compra sea un número positivo.
        """
        comision_compra = self.cleaned_data.get('comision_compra')
        if comision_compra is not None and comision_compra < 0:
            raise ValidationError('La comisión de compra debe ser un número positivo.')
        return comision_compra

    def clean_comision_venta(self):
        """
        Valida que la comisión de venta sea un número positivo.
        """
        comision_venta = self.cleaned_data.get('comision_venta')
        if comision_venta is not None and comision_venta < 0:
            raise ValidationError('La comisión de venta debe ser un número positivo.')
        return comision_venta