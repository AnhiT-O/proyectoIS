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
        required=False,
        error_messages={
            'min_value': 'La tasa base debe ser un número positivo.'
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
            'type': 'number'
        })
    )

    class Meta:
        model = Moneda
        fields = ['nombre', 'simbolo', 'tasa_base', 'decimales']

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
    
    def clean_tasa_base(self):
        value = self.cleaned_data.get('tasa_base')
        return value if value is not None else 0

    def clean_decimales(self):
        value = self.cleaned_data.get('decimales')
        return value if value is not None else 3