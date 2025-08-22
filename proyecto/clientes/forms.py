from django import forms
from .models import Cliente

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'nombre', 
            'apellido',
            'tipoDocCliente',
            'docCliente',
            'correoElecCliente',
            'telefono',
            'tipoCliente',
            'direccion',
            'ocupacion',
            'declaracion_jurada'
        ]
        widgets = {
            'tipoDocCliente': forms.Select(attrs={'class': 'form-control'}),
            'tipoCliente': forms.Select(attrs={'class': 'form-control'}),
            'declaracion_jurada': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }