from django import forms
from .models import CuentaBancaria, Billetera

class CuentaBancariaForm(forms.ModelForm):
    class Meta:
        model = CuentaBancaria
        fields = ['banco', 'numero_cuenta', 'nombre_titular', 'nro_documento']
        widgets = {
            'banco': forms.Select(attrs={'class': 'form-control'}),
            'numero_cuenta': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_titular': forms.TextInput(attrs={'class': 'form-control'}),
            'nro_documento': forms.TextInput(attrs={'class': 'form-control'}),
        }

class BilleteraForm(forms.ModelForm):
    class Meta:
        model = Billetera
        fields = ['tipo_billetera', 'telefono', 'nombre_titular', 'nro_documento']
        widgets = {
            'tipo_billetera': forms.Select(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_titular': forms.TextInput(attrs={'class': 'form-control'}),
            'nro_documento': forms.TextInput(attrs={'class': 'form-control'}),
        }
