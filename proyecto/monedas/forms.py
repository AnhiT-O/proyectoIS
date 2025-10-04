from django import forms
from django.core.exceptions import ValidationError
from .models import Moneda

class NoBracketsArrayWidget(forms.TextInput):
    """
    Widget personalizado para renderizar ArrayField como una cadena separada por comas.
    """
    def render(self, name, value, attrs=None, renderer=None):
        if value is not None and isinstance(value, (list, tuple)):
            # Convierte la lista/tupla en una cadena separada por comas
            value = ', '.join(map(str, value))
        return super().render(name, value, attrs, renderer)

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
    denominaciones = forms.CharField(
        required=True,
        error_messages={
            'required': 'Debes ingresar las denominaciones disponibles.'
        },
        widget=NoBracketsArrayWidget(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 1,2,5,10,20,50,100',
            'data-toggle': 'tooltip',
            'title': 'Ingresa las denominaciones separadas por comas'
        }),
        help_text='Ingresa las denominaciones disponibles separadas por comas (ej: 1,2,5,10,20,50,100)'
    )

    class Meta:
        model = Moneda
        fields = ['nombre', 'simbolo', 'tasa_base', 'decimales', 'comision_compra', 'comision_venta', 'denominaciones']

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
        if value:
            if value > 8:
                raise ValidationError('El número de decimales no puede ser mayor a 8.')
        return value if value is not None else 3

    def clean_tasa_base(self):
        """
        Valida que la tasa base sea un número positivo.
        """
        tasa_base = self.cleaned_data.get('tasa_base')
        if tasa_base:
            if tasa_base < 0:
                raise ValidationError('La tasa base debe ser un número positivo.')
        return tasa_base

    def clean_comision_compra(self):
        """
        Valida que la comisión de compra sea un número positivo.
        """
        comision_compra = self.cleaned_data.get('comision_compra')
        if comision_compra:
            if comision_compra < 0:
                raise ValidationError('La comisión de compra debe ser un número positivo.')
        return comision_compra

    def clean_comision_venta(self):
        """
        Valida que la comisión de venta sea un número positivo.
        """
        comision_venta = self.cleaned_data.get('comision_venta')
        if comision_venta:
            if comision_venta < 0:
                raise ValidationError('La comisión de venta debe ser un número positivo.')
        return comision_venta

    def clean_denominaciones(self):
        """
        Convierte el string de denominaciones a una lista de enteros.
        """
        denominaciones_str = self.cleaned_data.get('denominaciones')
        if not denominaciones_str:
            raise ValidationError('Debes ingresar al menos una denominación.')
        
        try:
            # Separar por comas y convertir a enteros
            denominaciones_list = [int(x.strip()) for x in denominaciones_str.split(',') if x.strip()]
            
            # Validar que no esté vacía
            if not denominaciones_list:
                raise ValidationError('Debes ingresar al menos una denominación válida.')
            
            # Validar que todos sean números positivos
            for denominacion in denominaciones_list:
                if denominacion <= 0:
                    raise ValidationError('Todas las denominaciones deben ser números positivos.')
            
            # Remover duplicados y ordenar
            denominaciones_list = sorted(list(set(denominaciones_list)))
            
            return denominaciones_list
            
        except ValueError:
            raise ValidationError('Las denominaciones deben ser números enteros separados por comas.')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si estamos editando una moneda existente, convertir la lista a string
        if self.instance and self.instance.pk and self.instance.denominaciones:
            # Convertir la lista de enteros a string separado por comas
            denominaciones_str = ','.join(map(str, self.instance.denominaciones))
            self.fields['denominaciones'].initial = denominaciones_str