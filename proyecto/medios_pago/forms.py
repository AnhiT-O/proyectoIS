from django import forms
from django.core.exceptions import ValidationError
from .models import MedioPago, MedioPagoCliente
import re


class TarjetaCreditoForm(forms.Form):
    """
    Formulario para agregar una tarjeta de crédito a un cliente
    """
    numero_tarjeta = forms.CharField(
        max_length=16,
        min_length=16,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234567890123456',
            'pattern': '[0-9]{16}',
            'title': 'Ingrese exactamente 16 dígitos'
        }),
        label='Número de Tarjeta',
        help_text='Ingrese los 16 dígitos de la tarjeta sin espacios'
    )
    
    cvv = forms.CharField(
        max_length=3,
        min_length=3,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '123',
            'pattern': '[0-9]{3}',
            'title': 'Ingrese exactamente 3 dígitos'
        }),
        label='CVV',
        help_text='Código de seguridad de 3 dígitos'
    )
    
    nombre_titular_tarjeta = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre como aparece en la tarjeta',
            'style': 'text-transform: uppercase;'
        }),
        label='Nombre del Titular',
        help_text='Nombre completo como aparece en la tarjeta'
    )
    
    fecha_vencimiento_tc = forms.CharField(
        max_length=7,
        min_length=7,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MM/AAAA',
            'pattern': '(0[1-9]|1[0-2])\/[0-9]{4}',
            'title': 'Ingrese el mes y año en formato MM/AAAA'
        }),
        label='Fecha de Vencimiento',
        help_text='Ingrese el mes y año de vencimiento (MM/AAAA)'
    )

    def clean_fecha_vencimiento_tc(self):
        fecha = self.cleaned_data.get('fecha_vencimiento_tc')
        if fecha and not re.match(r'^(0[1-9]|1[0-2])\/[0-9]{4}$', fecha):
            raise ValidationError('Ingrese la fecha en formato MM/AAAA')
        return fecha
    
    descripcion_tarjeta = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Tarjeta personal, Tarjeta de empresa',
        }),
        label='Descripción de la Tarjeta',
        help_text='Descripción breve para identificar esta tarjeta'
    )
    
    moneda_tc = forms.ChoiceField(
        choices=MedioPagoCliente.MONEDA_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Moneda de la Tarjeta',
        help_text='Seleccione la moneda de la tarjeta'
    )

    def clean_numero_tarjeta(self):
        numero = self.cleaned_data.get('numero_tarjeta')
        if numero and not numero.isdigit():
            raise ValidationError('El número de tarjeta debe contener solo dígitos')
        if numero and len(numero) != 16:
            raise ValidationError('El número de tarjeta debe tener exactamente 16 dígitos')
        return numero

    def clean_cvv(self):
        cvv = self.cleaned_data.get('cvv')
        if cvv and not cvv.isdigit():
            raise ValidationError('El CVV debe contener solo dígitos')
        if cvv and len(cvv) != 3:
            raise ValidationError('El CVV debe tener exactamente 3 dígitos')
        return cvv

    def clean_nombre_titular_tarjeta(self):
        nombre = self.cleaned_data.get('nombre_titular_tarjeta')
        if nombre:
            nombre = nombre.strip().upper()
            if len(nombre) < 3:
                raise ValidationError('El nombre debe tener al menos 3 caracteres')
        return nombre
        
    def clean_descripcion_tarjeta(self):
        descripcion = self.cleaned_data.get('descripcion_tarjeta')
        if descripcion:
            descripcion = descripcion.strip()
            if len(descripcion) < 3:
                raise ValidationError('La descripción debe tener al menos 3 caracteres')
        return descripcion


class CuentaBancariaForm(forms.Form):
    """
    Formulario para agregar una cuenta bancaria para transferencias
    """
    banco = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Banco Nacional de Fomento',
        }),
        label='Banco',
        help_text='Nombre del banco donde tiene la cuenta'
    )
    
    numero_cuenta = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 1234567890',
        }),
        label='Número de Cuenta',
        help_text='Número de cuenta bancaria donde recibirá los guaraníes'
    )
    
    nombre_titular_cuenta = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre completo del titular',
            'style': 'text-transform: uppercase;'
        }),
        label='Nombre del Titular de la Cuenta',
        help_text='Nombre completo del titular como aparece en la cuenta'
    )
    
    tipo_cuenta = forms.ChoiceField(
        choices=[
            ('corriente', 'Cuenta Corriente'),
            ('ahorro', 'Caja de Ahorro'),
            ('otro', 'Otro')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Tipo de Cuenta',
        help_text='Tipo de cuenta bancaria'
    )

    def clean_numero_cuenta(self):
        numero = self.cleaned_data.get('numero_cuenta')
        if numero:
            numero = numero.strip()
            if len(numero) < 6:
                raise ValidationError('El número de cuenta debe tener al menos 6 caracteres')
        return numero

    def clean_nombre_titular_cuenta(self):
        nombre = self.cleaned_data.get('nombre_titular_cuenta')
        if nombre:
            nombre = nombre.strip().upper()
            if len(nombre) < 3:
                raise ValidationError('El nombre debe tener al menos 3 caracteres')
        return nombre

    def clean_banco(self):
        banco = self.cleaned_data.get('banco')
        if banco:
            banco = banco.strip().title()
            if len(banco) < 3:
                raise ValidationError('El nombre del banco debe tener al menos 3 caracteres')
        return banco