from django import forms
from django.core.exceptions import ValidationError
from .models import Moneda

class MonedaForm(forms.ModelForm):
    class Meta:
        model = Moneda
        fields = ['nombre', 'simbolo', 'tasa_base', 'decimales']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'simbolo': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '3',
                'style': 'text-transform: uppercase;'
            }),
            'tasa_base': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'decimales': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '10',
                'step': '1',
                'type': 'number',
            })
        }

    def clean_simbolo(self):
        """
        Valida que el símbolo contenga solo letras mayúsculas.
        """
        simbolo = self.cleaned_data.get('simbolo')
        if simbolo:
            # Convertir a mayúsculas automáticamente
            simbolo = simbolo.upper()
            
            # Validar que solo contenga letras
            if not simbolo.isalpha():
                raise ValidationError('El símbolo debe contener solo letras.')
        return simbolo