from django import forms
from django.core.exceptions import ValidationError
from .models import Cliente
from django.conf import settings
import stripe

# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class ClienteForm(forms.ModelForm):

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
    
    def clean_id_stripe(self):
        """
        Valida que el ID de Stripe tenga el formato correcto si se proporciona.
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
    Formulario para agregar una tarjeta de crédito a un cliente usando Stripe Elements
    """
    stripe_token = forms.CharField(
        widget=forms.HiddenInput(),
        error_messages={
            'required': 'Token de Stripe requerido.'
        }
    )
    
    def __init__(self, *args, **kwargs):
        self.cliente = kwargs.pop('cliente', None)
        super().__init__(*args, **kwargs)
    
    def clean_stripe_token(self):
        """
        Valida que el token de Stripe sea válido
        """
        token = self.cleaned_data.get('stripe_token')
        if not token:
            raise ValidationError('Token de Stripe inválido.')
        return token
    
    def save(self):
        """
        Procesa el token y agrega la tarjeta al cliente en Stripe
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