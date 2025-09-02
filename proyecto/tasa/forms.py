from django import forms
from .models import TasaCambio
from monedas.models import Moneda

class TasaCambioForm(forms.ModelForm):
    class Meta:
        model = TasaCambio
        fields = ['moneda', 'precio_base', 'comision_compra', 'comision_venta']
        widgets = {
            'moneda': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Seleccione una moneda'
            }),
            'precio_base': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'min': '0.0001',
                'placeholder': 'Ingrese el precio base'
            }),
            'comision_compra': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '1',
                'placeholder': 'Ej: 0.10 para 10%'
            }),
            'comision_venta': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '1',
                'placeholder': 'Ej: 0.10 para 10%'
            })
        }
        help_texts = {
            'comision_compra': 'Ingrese el valor en decimal (ej: 0.10 para 10%)',
            'comision_venta': 'Ingrese el valor en decimal (ej: 0.10 para 10%)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['moneda'].queryset = Moneda.objects.filter(activa=True)
        self.fields['precio_base'].label = 'Precio Base'
        self.fields['comision_compra'].label = 'Comisión de Compra (en decimal)'
        self.fields['comision_venta'].label = 'Comisión de Venta (en decimal)'

    def clean_comision_compra(self):
        comision = self.cleaned_data.get('comision_compra')
        if comision > 1:
            raise forms.ValidationError('La comisión debe ser menor o igual a 1 (100%)')
        return comision

    def clean_comision_venta(self):
        comision = self.cleaned_data.get('comision_venta')
        if comision > 1:
            raise forms.ValidationError('La comisión debe ser menor o igual a 1 (100%)')
        return comision
