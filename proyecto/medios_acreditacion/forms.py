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
    TarjetaLocalForm: Formulario para agregar tarjetas locales (Panal y Cabal).
"""

from django import forms
from datetime import datetime
from .models import CuentaBancaria, Billetera, TarjetaLocal


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

class TarjetaLocalForm(forms.Form):
    """
    Formulario para agregar tarjetas de crédito locales (Panal y Cabal).
    
    Este formulario maneja la captura y validación de datos de tarjetas locales,
    incluyendo validaciones de número de tarjeta, fecha de expiración y CVV.
    
    Attributes:
        brand: Campo de selección para el tipo de tarjeta.
        numero_tarjeta: Campo de texto para el número de tarjeta.
        nombre_titular: Campo de texto para el nombre del titular.
        nro_documento: Campo de texto para el número de documento.
        mes_expiracion: Campo de selección para el mes de expiración.
        anio_expiracion: Campo de selección para el año de expiración.
        cvv: Campo de texto para el código de seguridad.
    """
    
    brand = forms.ChoiceField(
        choices=TarjetaLocal.TIPO_TARJETA_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'title': 'Seleccione el tipo de tarjeta'
        }),
        error_messages={
            'required': 'Debes seleccionar un tipo de tarjeta.',
        },
        help_text="Seleccione Panal o Cabal"
    )
    
    numero_tarjeta = forms.CharField(
        max_length=19,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234 5678 9012 3456',
            'title': 'Número de tarjeta (16 dígitos)',
            'maxlength': '19'
        }),
        error_messages={
            'required': 'Debes ingresar el número de tarjeta.',
            'max_length': 'El número de tarjeta no puede exceder los 19 caracteres.'
        },
        help_text="Ingrese el número completo de la tarjeta"
    )
    
    nombre_titular = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre completo del titular',
            'title': 'Nombre tal como aparece en la tarjeta'
        }),
        error_messages={
            'required': 'Debes ingresar el nombre del titular.',
            'max_length': 'El nombre del titular no puede exceder los 100 caracteres.'
        },
        help_text="Nombre completo tal como aparece en la tarjeta"
    )
    
    nro_documento = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de documento',
            'title': 'Cédula de identidad del titular'
        }),
        error_messages={
            'required': 'Debes ingresar el número de documento del titular.',
            'max_length': 'El número de documento no puede exceder los 20 caracteres.'
        },
        help_text="Número de cédula del titular de la tarjeta"
    )
    
    mes_expiracion = forms.ChoiceField(
        choices=[(i, f'{i:02d}') for i in range(1, 13)],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'title': 'Mes de expiración'
        }),
        error_messages={
            'required': 'Debes seleccionar el mes de expiración.',
        },
        help_text="Mes de expiración (MM)"
    )
    
    anio_expiracion = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(datetime.now().year, datetime.now().year + 11)],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'title': 'Año de expiración'
        }),
        error_messages={
            'required': 'Debes seleccionar el año de expiración.',
        },
        help_text="Año de expiración (AAAA)"
    )
    
    cvv = forms.CharField(
        max_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'CVV',
            'title': 'Código de seguridad (3 o 4 dígitos)',
            'maxlength': '4'
        }),
        error_messages={
            'required': 'Debes ingresar el código CVV.',
            'max_length': 'El CVV no puede exceder los 4 dígitos.'
        },
        help_text="Código de seguridad de 3 o 4 dígitos"
    )
    
    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario con el cliente asociado.
        
        Args:
            cliente: Instancia del cliente al que se agregará la tarjeta.
        """
        self.cliente = kwargs.pop('cliente', None)
        super().__init__(*args, **kwargs)
    
    def clean_numero_tarjeta(self):
        """
        Validación del número de tarjeta.
        Limpia espacios y verifica que contenga solo dígitos.
        """
        numero = self.cleaned_data.get('numero_tarjeta', '').replace(' ', '')
        
        if not numero.isdigit():
            raise forms.ValidationError('El número de tarjeta debe contener solo dígitos.')
        
        if len(numero) != 16:
            raise forms.ValidationError('El número de tarjeta debe tener 16 dígitos.')
        
        # Formatear con espacios para visualización
        numero_formateado = ' '.join([numero[i:i+4] for i in range(0, len(numero), 4)])
        return numero_formateado
    
    def clean_cvv(self):
        """
        Validación del CVV.
        Verifica que contenga solo dígitos y tenga 3 o 4 caracteres.
        """
        cvv = self.cleaned_data.get('cvv', '')
        
        if not cvv.isdigit():
            raise forms.ValidationError('El CVV debe contener solo dígitos.')
        
        if len(cvv) < 3 or len(cvv) > 4:
            raise forms.ValidationError('El CVV debe tener 3 o 4 dígitos.')
        
        return cvv
    
    def clean(self):
        """
        Validación general del formulario.
        Verifica que la fecha de expiración sea válida.
        """
        cleaned_data = super().clean()
        mes = cleaned_data.get('mes_expiracion')
        anio = cleaned_data.get('anio_expiracion')
        
        if mes and anio:
            mes_int = int(mes)
            anio_int = int(anio)
            fecha_actual = datetime.now()
            
            # Verificar que la tarjeta no esté expirada
            if anio_int < fecha_actual.year or (anio_int == fecha_actual.year and mes_int < fecha_actual.month):
                raise forms.ValidationError('La tarjeta está expirada.')
        
        return cleaned_data
    
    def save(self):
        """
        Crea y guarda la tarjeta local en la base de datos.
        
        Returns:
            TarjetaLocal: La instancia de la tarjeta creada.
        
        Raises:
            ValidationError: Si no se especifica cliente o si ocurre algún error.
        """
        if not self.cliente:
            raise forms.ValidationError('Cliente no especificado.')
        
        tarjeta = TarjetaLocal.objects.create(
            cliente=self.cliente,
            brand=self.cleaned_data['brand'],
            numero_tarjeta=self.cleaned_data['numero_tarjeta'],
            nombre_titular=self.cleaned_data['nombre_titular'],
            nro_documento=self.cleaned_data['nro_documento'],
            mes_expiracion=int(self.cleaned_data['mes_expiracion']),
            anio_expiracion=int(self.cleaned_data['anio_expiracion']),
            cvv=self.cleaned_data['cvv'],
            activo=True
        )
        
        return tarjeta
