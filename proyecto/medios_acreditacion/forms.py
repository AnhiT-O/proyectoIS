from django import forms
from .models import CuentaBancaria, Billetera

class CuentaBancariaForm(forms.ModelForm):
    class Meta:
        model = CuentaBancaria
        fields = ['banco', 'numero_cuenta', 'nombre_titular']
        widgets = {
            'banco': forms.Select(attrs={'class': 'form-control'}),
            'numero_cuenta': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_titular': forms.TextInput(attrs={'class': 'form-control'}),
        }

class BilleteraForm(forms.ModelForm):
    class Meta:
        model = Billetera
        fields = ['tipo_billetera', 'numero_billetera', 'nombre_titular', 'ci']
        widgets = {
            'tipo_billetera': forms.Select(attrs={'class': 'form-control'}),
            'numero_billetera': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_titular': forms.TextInput(attrs={'class': 'form-control'}),
            'ci': forms.TextInput(attrs={'class': 'form-control'}),
        }
