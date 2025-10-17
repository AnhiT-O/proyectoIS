"""
Módulo de modelos para la gestión de clientes.

Este módulo contiene los modelos de datos relacionados con la gestión de clientes
del sistema, incluyendo la información personal, segmentación, integración con Stripe
para métodos de pago y relaciones con usuarios operadores.
"""

from django.db import models
from django.conf import settings
import stripe

# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class Cliente(models.Model):
    """
    Modelo que representa un cliente del sistema.

    Este modelo almacena toda la información relevante de los clientes,
    incluyendo datos personales, de contacto, segmentación comercial e
    integración con servicios de pago externos como Stripe.

    Attributes:
        TIPO_CLIENTE_CHOICES (list): Opciones para el tipo de cliente (Física/Jurídica)
        TIPO_DOCUMENTO_CHOICES (list): Opciones para el tipo de documento (CI/RUC)
        SEGMENTO_CHOICES (list): Opciones para la segmentación de clientes
        BENEFICIOS_SEGMENTO (dict): Mapeo de beneficios por segmento de cliente

    Examples:
        >>> cliente = Cliente(
        ...     nombre="Juan Pérez",
        ...     tipo_documento="CI",
        ...     numero_documento="12345678",
        ...     correo_electronico="juan@email.com"
        ... )
        >>> cliente.save()
    """

    TIPO_CLIENTE_CHOICES = [
        ('F', 'Persona Física'),
        ('J', 'Persona Jurídica'),
    ]
    TIPO_DOCUMENTO_CHOICES = [
        ('CI', 'Cédula de Identidad'),
        ('RUC', 'Registro Único de Contribuyente'),
    ]
    SEGMENTO_CHOICES = [
        ('minorista', 'Minorista'),
        ('corporativo', 'Corporativo'),
        ('vip', 'VIP'),
    ]
    
    nombre = models.CharField(max_length=100)
    tipo_documento = models.CharField(max_length=3,choices=TIPO_DOCUMENTO_CHOICES)
    numero_documento = models.CharField(
        max_length=10,
        unique=True
    )
    correo_electronico = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)
    tipo = models.CharField(max_length=1,choices=TIPO_CLIENTE_CHOICES)
    direccion = models.TextField()
    ocupacion = models.CharField(max_length=30)
    declaracion_jurada = models.BooleanField(default=False)
    segmento = models.CharField(max_length=11,choices=SEGMENTO_CHOICES)
    usuarios = models.ManyToManyField(
        'usuarios.Usuario',
        related_name='clientes_operados'
    )
    id_stripe = models.CharField(
        max_length=100, 
        blank=True, 
        null=True
    )
    consumo_diario = models.IntegerField(default=0)
    consumo_mensual = models.IntegerField(default=0)
    ultimo_consumo = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'clientes'
        default_permissions = []
        permissions = [
            ("gestion", "Puede gestionar clientes (crear y editar)")
        ]

    def __str__(self):
        """
        Devuelve la representación en cadena del cliente.

        Returns:
            str: El nombre del cliente
        """
        return f"{self.nombre}"

    def tiene_tarjetas_activas(self):
        """
        Verifica si el cliente tiene tarjetas de crédito activas en Stripe.

        Consulta la API de Stripe para determinar si el cliente tiene al menos
        una tarjeta de crédito registrada y activa.

        Returns:
            bool: True si el cliente tiene al menos una tarjeta activa, False en caso contrario

        Note:
            Requiere que el cliente tenga un id_stripe válido. Si ocurre algún error
            en la consulta a Stripe, se registra en el log y retorna False.

        Examples:
            >>> cliente = Cliente.objects.get(id=1)
            >>> if cliente.tiene_tarjetas_activas():
            ...     print("Cliente puede realizar pagos con tarjeta")
        """
        if not self or not getattr(self, 'id_stripe', None):
            return False
        
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=self.id_stripe,
                type='card'
            )
            
            return len(payment_methods.data) > 0
            
        except stripe.error.StripeError as e:
            print(f"Error al consultar tarjetas de Stripe para cliente {self.nombre}: {str(e)}")
            return False
        except Exception as e:
            print(f"Error inesperado al verificar tarjetas para cliente {self.nombre}: {str(e)}")
            return False

    def obtener_tarjetas_stripe(self):
        """
        Obtiene la información detallada de las tarjetas de crédito del cliente desde Stripe.

        Consulta la API de Stripe para obtener todos los métodos de pago tipo tarjeta
        asociados al cliente y formatea la información en una estructura de datos útil.

        Returns:
            list: Lista de diccionarios, cada uno conteniendo la información de una tarjeta:
                - id (str): ID del método de pago en Stripe
                - brand (str): Marca de la tarjeta (VISA, MASTERCARD, etc.)
                - last4 (str): Últimos 4 dígitos de la tarjeta
                - exp_month (int): Mes de expiración
                - exp_year (int): Año de expiración
                - funding (str): Tipo de financiamiento (credit, debit, etc.)
                - created (int): Timestamp de creación en Stripe

        Note:
            Requiere que el cliente tenga un id_stripe válido. Si ocurre algún error,
            se registra en el log y retorna una lista vacía.

        Examples:
            >>> cliente = Cliente.objects.get(id=1)
            >>> tarjetas = cliente.obtener_tarjetas_stripe()
            >>> for tarjeta in tarjetas:
            ...     print(f"Tarjeta {tarjeta['brand']} ****{tarjeta['last4']}")
        """
        if not self or not getattr(self, 'id_stripe', None):
            return []
        
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=self.id_stripe,
                type='card'
            )
            
            tarjetas = []
            for payment_method in payment_methods.data:
                card = payment_method.card
                tarjeta_info = {
                    'id': payment_method.id,
                    'brand': card.brand.upper(),
                    'last4': card.last4,
                    'exp_month': card.exp_month,
                    'exp_year': card.exp_year,
                    'funding': card.funding,
                    'created': payment_method.created,
                }
                tarjetas.append(tarjeta_info)
            
            return tarjetas
            
        except stripe.error.StripeError as e:
            print(f"Error al obtener tarjetas de Stripe para cliente {self.nombre}: {str(e)}")
            return []
        except Exception as e:
            print(f"Error inesperado al obtener tarjetas para cliente {self.nombre}: {str(e)}")
            return []