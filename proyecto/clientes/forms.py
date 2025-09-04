from django import forms
from django.core.exceptions import ValidationError
from .models import Cliente

class ClienteForm(forms.ModelForm):

    nombre = forms.CharField(
        error_messages={
            'required': 'Debes ingresar el nombre.',
            'max_length': 'El nombre no puede exceder los 100 caracteres.'
        },
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    apellido = forms.CharField(
        error_messages={
            'required': 'Debes ingresar el apellido.',
            'max_length': 'El apellido no puede exceder los 100 caracteres.'
        },
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    docCliente = forms.CharField(
        error_messages={
            'required': 'Debes ingresar el número de documento.',
            'max_length': 'El documento no puede exceder los 20 caracteres.',
            'unique': 'Ya existe un cliente con este número de documento.'
        },
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    tipoDocCliente = forms.ChoiceField(
        choices=Cliente.TIPO_DOCUMENTO_CHOICES,
        error_messages={
            'required': 'Debes seleccionar un tipo de documento.'
        },
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    correoElecCliente = forms.EmailField(
        error_messages={
            'required': 'Debes ingresar un correo electrónico.',
            'invalid': 'Debes ingresar un correo electrónico válido.',
            'unique': 'Ya existe un cliente con este correo electrónico.'
        },
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    telefono = forms.CharField(
        error_messages={
            'required': 'Debes ingresar un número de teléfono.',
            'max_length': 'El teléfono no puede exceder los 20 caracteres.'
        },
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    tipoCliente = forms.ChoiceField(
        choices=Cliente.TIPO_CLIENTE_CHOICES,
        error_messages={
            'required': 'Debes seleccionar un tipo de cliente.'
        },
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    direccion = forms.CharField(
        error_messages={
            'max_length': 'La dirección no puede exceder los 100 caracteres.',
            'required': 'Debes ingresar una dirección.'
        },
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    ocupacion = forms.CharField(
        error_messages={
            'max_length': 'La ocupación no puede exceder los 30 caracteres.',
            'required': 'Debes ingresar una ocupación.'
        },
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    segmento = forms.ChoiceField(
        choices=Cliente.SEGMENTO_CHOICES,
        error_messages={
            'required': 'Debes seleccionar un segmento.'
        },
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    declaracion_jurada = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

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
            'segmento',
            'declaracion_jurada'
        ]

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