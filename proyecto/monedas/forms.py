from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import Moneda
from transacciones.models import LimiteGlobal

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

    stock = forms.IntegerField(
        required= True,
        error_messages={
            'required': 'Debe ingresar una cantidad de stock'
        },
        widget= forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'type': 'number'
        })

    )


    class Meta:
        model = Moneda
        fields = ['nombre', 'simbolo', 'tasa_base', 'decimales', 'comision_compra', 'comision_venta', 'stock']

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

    def es_moneda_base(self):
        """
        Verifica si la moneda actual es la moneda base del sistema (Guaraní).
        """
        simbolo = self.cleaned_data.get('simbolo', '').upper()
        moneda_base = settings.MONEDA_BASE_GUARANIES
        return simbolo == moneda_base['simbolo']

    def get_moneda_base_info(self):
        """
        Retorna la información de la moneda base del sistema.
        """
        return settings.MONEDA_BASE_GUARANIES


class LimiteGlobalForm(forms.ModelForm):
    """
    Formulario para gestionar los límites globales de transacciones
    """
    
    limite_diario = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'step': '1000',
        }),
        error_messages={
            'required': 'Debes ingresar el límite diario.',
            'invalid': 'El límite diario debe ser un número entero.',
            'min_value': 'El límite diario debe ser mayor a 0.',
        },
        help_text='Límite diario en guaraníes'
    )
    
    limite_mensual = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'step': '1000',
        }),
        error_messages={
            'required': 'Debes ingresar el límite mensual.',
            'invalid': 'El límite mensual debe ser un número entero.',
            'min_value': 'El límite mensual debe ser mayor a 0.',
        },
        help_text='Límite mensual en guaraníes'
    )

    class Meta:
        model = LimiteGlobal
        fields = ['limite_diario', 'limite_mensual']

    def clean(self):
        cleaned_data = super().clean()
        limite_diario = cleaned_data.get('limite_diario')
        limite_mensual = cleaned_data.get('limite_mensual')

        # Validar que el límite diario no sea mayor al mensual
        if limite_diario and limite_mensual:
            if limite_diario > limite_mensual:
                raise ValidationError(
                    'El límite diario no puede ser mayor al límite mensual.'
                )

        return cleaned_data

    def clean_limite_diario(self):
        limite_diario = self.cleaned_data.get('limite_diario')
        if limite_diario and limite_diario <= 0:
            raise ValidationError('El límite diario debe ser mayor a 0.')
        return limite_diario

    def clean_limite_mensual(self):
        limite_mensual = self.cleaned_data.get('limite_mensual')
        if limite_mensual and limite_mensual <= 0:
            raise ValidationError('El límite mensual debe ser mayor a 0.')
        return limite_mensual