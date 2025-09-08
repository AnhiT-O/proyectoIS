from django import forms
from .models import Cotizacion

class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = ['id_moneda']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar clases CSS a los campos
        self.fields['id_moneda'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Seleccione una moneda'
        })
