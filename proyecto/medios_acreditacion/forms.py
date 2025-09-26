"""
Formularios para la gestión de medios de acreditación.

Este módulo contiene los formularios de Django que manejan la validación y 
presentación de datos para los medios de acreditación, incluyendo cuentas 
bancarias y billeteras electrónicas.

Los formularios incluyen validaciones personalizadas, mensajes de error 
personalizados y configuración de widgets para mejorar la experiencia del usuario.

Clases:
    CuentaBancariaForm: Formulario para crear y editar cuentas bancarias.
    BilleteraForm: Formulario para crear y editar billeteras electrónicas.
"""

from django import forms
from .models import CuentaBancaria, Billetera


class CuentaBancariaForm(forms.ModelForm):
    """
    Formulario para la gestión de cuentas bancarias.
    
    Este formulario permite crear y editar cuentas bancarias con validaciones
    personalizadas y mensajes de error específicos para cada campo.
    
    Attributes:
        banco: Campo de selección para el banco.
        numero_cuenta: Campo de texto para el número de cuenta.
        nombre_titular: Campo de texto para el nombre del titular.
        nro_documento: Campo de texto para el número de documento.
    """
    # Campo de selección para el banco con validación personalizada
    banco = forms.ChoiceField(
        choices=CuentaBancaria.BANCO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'title': 'Seleccione el banco al que pertenece la cuenta'
        }),
        error_messages={
            'required': 'Debes seleccionar un banco.',
        },
        help_text="Seleccione el banco donde está registrada la cuenta"
    )
    # Campo de texto para el número de cuenta bancaria
    numero_cuenta = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el número de cuenta',
            'title': 'Número de la cuenta bancaria'
        }),
        error_messages={
            'required': 'Debes ingresar el número de cuenta.',
            'max_length': 'El número de cuenta no puede exceder los 30 caracteres.'
        },
        help_text="Ingrese el número de cuenta tal como aparece en el banco"
    )
    
    # Campo de texto para el nombre completo del titular de la cuenta
    nombre_titular = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre completo del titular',
            'title': 'Nombre completo tal como aparece en el banco'
        }),
        error_messages={
            'required': 'Debes ingresar el nombre del titular.',
            'max_length': 'El nombre del titular no puede exceder los 100 caracteres.'
        },
        help_text="Nombre completo del titular tal como está registrado en el banco"
    )
    
    # Campo de texto para el número de documento del titular
    nro_documento = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de documento',
            'title': 'Cédula de identidad, RUC u otro documento'
        }),
        error_messages={
            'required': 'Debes ingresar el número de documento del titular.',
            'max_length': 'El número de documento no puede exceder los 20 caracteres.'
        },
        help_text="Número de cédula, RUC u otro documento de identidad"
    )

    class Meta:
        """Metadatos del formulario CuentaBancariaForm."""
        model = CuentaBancaria  # Modelo asociado al formulario
        fields = ['banco', 'numero_cuenta', 'nombre_titular', 'nro_documento']  # Campos a incluir

    def clean_banco(self):
        """
        Validación personalizada para el campo banco.
        
        Verifica que se haya seleccionado un banco válido y no la opción por defecto.
        
        Returns:
            str: El valor del banco seleccionado si es válido.
            
        Raises:
            forms.ValidationError: Si no se seleccionó un banco válido.
        """
        banco = self.cleaned_data.get('banco')
        # Verificar que no sea la opción por defecto "-------"
        if banco == '-------':
            raise forms.ValidationError('Debes seleccionar un banco válido.')
        return banco

class BilleteraForm(forms.ModelForm):
    """
    Formulario para la gestión de billeteras electrónicas.
    
    Este formulario permite crear y editar billeteras electrónicas con validaciones
    personalizadas y mensajes de error específicos para cada campo.
    
    Attributes:
        tipo_billetera: Campo de selección para el tipo de billetera.
        telefono: Campo de texto para el número de teléfono.
        nombre_titular: Campo de texto para el nombre del titular.
        nro_documento: Campo de texto para el número de documento.
    """
    # Campo de selección para el tipo de billetera electrónica
    tipo_billetera = forms.ChoiceField(
        choices=Billetera.TIPO_BILLETERA_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'title': 'Seleccione el tipo de billetera electrónica'
        }),
        error_messages={
            'required': 'Debes seleccionar un tipo de billetera.',
        },
        help_text="Seleccione el tipo de billetera electrónica"
    )
    
    # Campo de texto para el número de teléfono asociado a la billetera
    telefono = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de teléfono',
            'title': 'Número de teléfono asociado a la billetera'
        }),
        error_messages={
            'required': 'Debes ingresar el número de teléfono asociado a la billetera.',
            'max_length': 'El número de teléfono no puede exceder los 15 caracteres.'
        },
        help_text="Número de teléfono registrado en la billetera electrónica"
    )
    
    # Campo de texto para el nombre completo del titular de la billetera
    nombre_titular = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre completo del titular',
            'title': 'Nombre completo tal como está registrado en la billetera'
        }),
        error_messages={
            'required': 'Debes ingresar el nombre del titular.',
            'max_length': 'El nombre del titular no puede exceder los 100 caracteres.'
        },
        help_text="Nombre completo del titular tal como está registrado en la billetera"
    )
    
    # Campo de texto para el número de documento del titular
    nro_documento = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de documento',
            'title': 'Cédula de identidad, RUC u otro documento'
        }),
        error_messages={
            'required': 'Debes ingresar el número de documento del titular.',
            'max_length': 'El número de documento no puede exceder los 20 caracteres.'
        },
        help_text="Número de cédula, RUC u otro documento de identidad"
    )
    
    class Meta:
        """Metadatos del formulario BilleteraForm."""
        model = Billetera  # Modelo asociado al formulario
        fields = ['tipo_billetera', 'telefono', 'nombre_titular', 'nro_documento']  # Campos a incluir
    
    def clean_tipo_billetera(self):
        """
        Validación personalizada para el campo tipo_billetera.
        
        Verifica que se haya seleccionado un tipo de billetera válido y no la opción por defecto.
        
        Returns:
            str: El valor del tipo de billetera seleccionado si es válido.
            
        Raises:
            forms.ValidationError: Si no se seleccionó un tipo de billetera válido.
        """
        tipo_billetera = self.cleaned_data.get('tipo_billetera')
        # Verificar que no sea la opción por defecto "-------"
        if tipo_billetera == '-------':
            raise forms.ValidationError('Debes seleccionar un tipo de billetera válido.')
        return tipo_billetera