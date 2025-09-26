"""
Módulo de formularios para la gestión de clientes.

Este módulo contiene los formularios de Django utilizados para la creación,
edición y validación de datos de clientes, incluyendo integración con Stripe
para el manejo de métodos de pago.

Autor: Equipo de desarrollo
Fecha: 2025
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import Cliente
from django.conf import settings
import stripe

# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class ClienteForm(forms.ModelForm):
    """
    Formulario para crear y editar clientes del sistema.

    Este formulario maneja la validación y presentación de todos los campos
    necesarios para crear o modificar un cliente, incluyendo validaciones
    personalizadas para teléfono, documento e integración con Stripe.

    Attributes:
        Los campos del formulario corresponden directamente con los campos
        del modelo Cliente, cada uno con sus respectivas validaciones y
        mensajes de error personalizados.

    Examples:
        >>> form = ClienteForm(data={
        ...     'nombre': 'Juan Pérez',
        ...     'tipoDocCliente': 'CI',
        ...     'docCliente': '12345678'
        ... })
        >>> if form.is_valid():
        ...     cliente = form.save()
    """

    nombre = forms.CharField(
        error_messages={
            'required': 'Debes ingresar el nombre.',
            'max_length': 'El nombre no puede exceder los 100 caracteres.'
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
    id_stripe = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    declaracion_jurada = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Cliente
        fields = [
            'nombre', 
            'tipoDocCliente',
            'docCliente',
            'correoElecCliente',
            'telefono',
            'tipoCliente',
            'direccion',
            'ocupacion',
            'segmento',
            'id_stripe',
            'declaracion_jurada'
        ]

    def clean_telefono(self):
        """
        Valida que el número de teléfono contenga únicamente dígitos.

        Realiza validación personalizada del campo teléfono para asegurar
        que solo contenga caracteres numéricos.

        Returns:
            str: El número de teléfono validado

        Raises:
            ValidationError: Si el teléfono contiene caracteres no numéricos

        Examples:
            >>> form.cleaned_data['telefono'] = '0981234567'  # Válido
            >>> form.cleaned_data['telefono'] = '098-123-4567'  # Inválido
        """
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            # Validar que solo contenga números
            if not telefono.isdigit():
                raise ValidationError('El teléfono debe contener solo números')
        
        return telefono

    def clean_docCliente(self):
        """
        Valida que el número de documento contenga únicamente dígitos.

        Realiza validación personalizada del campo documento de cliente
        para asegurar que solo contenga caracteres numéricos.

        Returns:
            str: El número de documento validado

        Raises:
            ValidationError: Si el documento contiene caracteres no numéricos

        Note:
            Esta validación se aplica tanto para cédulas de identidad como
            para números RUC, ambos deben ser completamente numéricos.

        Examples:
            >>> form.cleaned_data['docCliente'] = '12345678'  # Válido
            >>> form.cleaned_data['docCliente'] = '1234-5678-9'  # Inválido
        """
        doc_cliente = self.cleaned_data.get('docCliente')
        
        if doc_cliente:
            # Validar que solo contenga números
            if not doc_cliente.isdigit():
                raise ValidationError('El documento debe contener solo números')
        
        return doc_cliente
    
    def clean_id_stripe(self):
        """
        Valida que el ID de Stripe sea válido y exista en la plataforma.

        Realiza una consulta a la API de Stripe para verificar que el ID
        proporcionado corresponde a un cliente existente en Stripe.

        Returns:
            str: El ID de Stripe validado

        Raises:
            ValidationError: Si el ID de Stripe no es válido o no existe

        Note:
            Esta validación requiere conexión a internet y hace una llamada
            a la API de Stripe. El campo es opcional, por lo que la validación
            solo se ejecuta si se proporciona un valor.

        Examples:
            >>> form.cleaned_data['id_stripe'] = 'cus_1234567890abcdef'  # Válido
            >>> form.cleaned_data['id_stripe'] = 'invalid_id'  # Inválido
        """
        id_stripe = self.cleaned_data.get('id_stripe')
        if id_stripe:
            try:
                # Intentar recuperar el cliente de Stripe para validar el ID
                stripe.Customer.retrieve(id_stripe)
            except stripe.error.InvalidRequestError:
                raise ValidationError('El ID de Stripe no es válido.')
            except Exception as e:
                raise ValidationError(f'Error al validar el ID de Stripe: {str(e)}')
        return id_stripe


class AgregarTarjetaForm(forms.Form):
    """
    Formulario para agregar una tarjeta de crédito a un cliente usando Stripe Elements.

    Este formulario maneja la integración con Stripe para procesar tokens de tarjetas
    de crédito generados en el frontend y asociarlas a un cliente específico.

    Attributes:
        stripe_token (CharField): Campo oculto que contiene el token generado por Stripe Elements
        cliente: Instancia del cliente al que se agregará la tarjeta

    Note:
        Este formulario trabaja en conjunto con Stripe Elements en el frontend.
        El token se genera de forma segura en el navegador del usuario y se
        envía al backend para su procesamiento.

    Examples:
        >>> form = AgregarTarjetaForm(
        ...     data={'stripe_token': 'tok_1234567890abcdef'},
        ...     cliente=cliente_instance
        ... )
        >>> if form.is_valid():
        ...     payment_method = form.save()
    """
    
    stripe_token = forms.CharField(
        widget=forms.HiddenInput(),
        error_messages={
            'required': 'Token de Stripe requerido.'
        }
    )
    
    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario con un cliente específico.

        Args:
            cliente: Instancia del cliente al que se agregará la tarjeta
            *args: Argumentos posicionales pasados al constructor padre
            **kwargs: Argumentos con nombre pasados al constructor padre
        """
        self.cliente = kwargs.pop('cliente', None)
        super().__init__(*args, **kwargs)
    
    def clean_stripe_token(self):
        """
        Valida que el token de Stripe esté presente y no esté vacío.

        Realiza validación básica del token de Stripe para asegurar
        que se ha proporcionado un valor válido.

        Returns:
            str: El token de Stripe validado

        Raises:
            ValidationError: Si el token está vacío o es inválido

        Note:
            Esta validación es básica. La validación completa del token
            se realiza en la API de Stripe durante el método save().
        """
        token = self.cleaned_data.get('stripe_token')
        if not token:
            raise ValidationError('Token de Stripe inválido.')
        return token
    
    def save(self):
        """
        Procesa el token de Stripe y agrega la tarjeta al cliente.

        Este método maneja todo el proceso de agregar una tarjeta de crédito
        al cliente, incluyendo la creación del cliente en Stripe si no existe,
        el procesamiento del token y la asociación del método de pago.

        Returns:
            stripe.PaymentMethod: El método de pago creado y asociado al cliente

        Raises:
            ValidationError: Si no se especifica cliente o si ocurre algún error
                           durante el procesamiento en Stripe

        Process:
            1. Verifica que se haya especificado un cliente
            2. Si el cliente no tiene ID de Stripe, lo crea en la plataforma
            3. Crea el método de pago desde el token proporcionado
            4. Asocia el método de pago al cliente en Stripe

        Examples:
            >>> form = AgregarTarjetaForm(data={'stripe_token': token}, cliente=cliente)
            >>> if form.is_valid():
            ...     payment_method = form.save()
            ...     print(f"Tarjeta agregada: {payment_method.id}")
        """
        if not self.cliente:
            raise ValidationError('Cliente no especificado.')
        
        token = self.cleaned_data['stripe_token']
        
        try:
            # Si el cliente no tiene ID de Stripe, crearlo primero
            if not self.cliente.id_stripe:
                stripe_customer = stripe.Customer.create(
                    name=self.cliente.nombre,
                    email=self.cliente.correoElecCliente,
                    phone=self.cliente.telefono,
                    description=f"Cliente {self.cliente.docCliente}"
                )
                self.cliente.id_stripe = stripe_customer.id
                self.cliente.save()
            
            # Crear el método de pago desde el token
            payment_method = stripe.PaymentMethod.create(
                type='card',
                card={'token': token}
            )
            
            # Adjuntar el método de pago al cliente
            payment_method.attach(customer=self.cliente.id_stripe)
            
            return payment_method
            
        except stripe.error.CardError as e:
            raise ValidationError(f'Error con la tarjeta: {e.user_message}')
        except stripe.error.InvalidRequestError as e:
            raise ValidationError(f'Error en la solicitud: {str(e)}')
        except stripe.error.StripeError as e:
            raise ValidationError(f'Error de Stripe: {str(e)}')
        except Exception as e:
            raise ValidationError(f'Error inesperado: {str(e)}')