from django import forms
from django.core.exceptions import ValidationError
import re
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
            'declaracion_jurada': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Solo números'
            }),
            'docCliente': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Solo números'
            }),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'correoElecCliente': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ocupacion': forms.TextInput(attrs={'class': 'form-control'})
        }

    def clean_telefono(self):
        """
        Valida que el teléfono contenga solo números.
        """
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            # Validar que solo contenga números
            if not telefono.isdigit():
                raise ValidationError('El teléfono debe contener solo números')
        
        return telefono

    def clean_docCliente(self):
        """
        Valida que el documento contenga solo números.
        """
        doc_cliente = self.cleaned_data.get('docCliente')
        
        if doc_cliente:
            # Validar que solo contenga números
            if not doc_cliente.isdigit():
                raise ValidationError('El documento debe contener solo números')
        
        return doc_cliente

    def clean(self):
        """
        Validaciones adicionales que requieren múltiples campos
        """
        cleaned_data = super().clean()
        tipo_cliente = cleaned_data.get('tipoCliente')
        tipo_doc = cleaned_data.get('tipoDocCliente')
        
        # Validar coherencia entre tipo de cliente y tipo de documento
        if tipo_cliente and tipo_doc:
            if tipo_cliente == 'J' and tipo_doc != 'RUC':
                raise ValidationError(
                    'Las personas jurídicas solo pueden usar RUC'
                )
        
        return cleaned_data

class CambiarCategoriaForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['categoria']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-control'})
        }