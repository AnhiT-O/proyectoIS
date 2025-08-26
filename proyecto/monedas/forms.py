from django import forms
from django.core.exceptions import ValidationError
from .models import Moneda

class MonedaForm(forms.ModelForm):
    class Meta:
        model = Moneda
        fields = ['nombre', 'simbolo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'simbolo': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '3',
                'style': 'text-transform: uppercase;'
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
            
            # Validar longitud máxima
            if len(simbolo) > 3:
                raise ValidationError('El símbolo no puede tener más de 3 caracteres.')
        
        return simbolo

    def clean_nombre(self):
        """
        Valida que el nombre de la moneda no esté vacío y tenga un formato adecuado.
        """
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            # Capitalizar correctamente el nombre
            nombre = nombre.strip().title()
            
            # Validar longitud mínima
            if len(nombre) < 2:
                raise ValidationError('El nombre de la moneda debe tener al menos 2 caracteres.')
        
        return nombre