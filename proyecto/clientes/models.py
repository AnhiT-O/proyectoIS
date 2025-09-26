"""
Módulo de modelos para la gestión de clientes.

Este módulo contiene los modelos de datos relacionados con la gestión de clientes
del sistema, incluyendo la información personal, segmentación, integración con Stripe
para métodos de pago y relaciones con usuarios operadores.

Autor: Equipo de desarrollo
Fecha: 2025
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
import stripe
import logging

# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

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
        ...     tipoDocCliente="CI",
        ...     docCliente="12345678",
        ...     correoElecCliente="juan@email.com"
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
    
    BENEFICIOS_SEGMENTO = {
        'minorista': 0,
        'corporativo': 5,
        'vip': 10,
    }
    
    nombre = models.CharField(max_length=100)
    tipoDocCliente = models.CharField(
        max_length=3,
        choices=TIPO_DOCUMENTO_CHOICES
    )
    docCliente = models.CharField(
        max_length=20,
        unique=True
    )
    correoElecCliente = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)
    tipoCliente = models.CharField(
        max_length=1,
        choices=TIPO_CLIENTE_CHOICES
    )
    direccion = models.TextField(max_length=100)
    ocupacion = models.CharField(max_length=30)
    declaracion_jurada = models.BooleanField(default=False)
    segmento = models.CharField(
        max_length=20,
        choices=SEGMENTO_CHOICES,
        default='minorista',
    )
    beneficio_segmento = models.IntegerField(default=0)
    usuarios = models.ManyToManyField(
        'usuarios.Usuario',
        through='UsuarioCliente',
        related_name='clientes_operados',
        verbose_name='Usuarios operadores'
    )
    id_stripe = models.CharField(
        max_length=100, 
        blank=True, 
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Realiza validaciones personalizadas del modelo Cliente.

        Valida la coherencia entre el tipo de cliente y el tipo de documento,
        asegurando que las personas jurídicas utilicen RUC como documento.

        Raises:
            ValidationError: Si existe incoherencia entre tipo de cliente y documento

        Note:
            Este método se ejecuta automáticamente al llamar full_clean() o
            durante la validación del formulario.
        """
        super().clean()
        
        # Validar coherencia entre tipo de cliente y tipo de documento
        if self.tipoCliente and self.tipoDocCliente:
            if self.tipoCliente == 'J' and self.tipoDocCliente != 'RUC':
                raise ValidationError({
                    'tipoDocCliente': 'Las personas jurídicas deben usar RUC'
                })

    def save(self, *args, **kwargs):
        """
        Guarda el cliente aplicando validaciones y actualizaciones automáticas.

        Actualiza automáticamente el beneficio por segmento basado en el segmento
        del cliente y ejecuta todas las validaciones antes de guardar.

        Args:
            *args: Argumentos posicionales pasados al método save padre
            **kwargs: Argumentos con nombre pasados al método save padre

        Note:
            El beneficio por segmento se actualiza automáticamente según la
            configuración definida en BENEFICIOS_SEGMENTO.
        """
        # Actualizar el beneficio según el segmento
        self.beneficio_segmento = self.BENEFICIOS_SEGMENTO.get(self.segmento, 0)
        
        self.full_clean()
        super().save(*args, **kwargs)

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
            # Obtener los métodos de pago del cliente desde Stripe
            payment_methods = stripe.PaymentMethod.list(
                customer=self.id_stripe,
                type='card'
            )
            
            # Verificar si hay al menos una tarjeta activa
            return len(payment_methods.data) > 0
            
        except stripe.error.StripeError as e:
            logger.error(f"Error al consultar tarjetas de Stripe para cliente {self.nombre}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado al verificar tarjetas para cliente {self.nombre}: {str(e)}")
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
            # Obtener los métodos de pago del cliente desde Stripe
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
            logger.error(f"Error al obtener tarjetas de Stripe para cliente {self.nombre}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al obtener tarjetas para cliente {self.nombre}: {str(e)}")
            return []
        
    class Meta:
        db_table = 'clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        default_permissions = []  # Deshabilita permisos predeterminados
        permissions = [
            ("gestion", "Puede gestionar clientes (crear y editar)")
        ]

class UsuarioCliente(models.Model):
    """
    Modelo intermedio para la relación muchos-a-muchos entre Usuario y Cliente.

    Esta tabla intermedia permite establecer qué usuarios pueden operar con qué clientes,
    proporcionando un sistema de permisos granular donde los usuarios solo pueden
    acceder a los clientes específicos asignados a ellos.

    Attributes:
        usuario (ForeignKey): Referencia al usuario operador
        cliente (ForeignKey): Referencia al cliente que puede operar
        created_at (DateTimeField): Fecha de creación de la relación

    Examples:
        >>> usuario = Usuario.objects.get(id=1)
        >>> cliente = Cliente.objects.get(id=1)
        >>> relacion = UsuarioCliente.objects.create(usuario=usuario, cliente=cliente)
    """
    
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE)
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """
        Metadatos del modelo UsuarioCliente.

        Define la tabla de base de datos, restricciones de unicidad,
        nombres para mostrar y permisos personalizados.
        """
        db_table = 'usuarios_clientes'
        unique_together = ['usuario', 'cliente']
        verbose_name = 'Relación Usuario-Cliente'
        verbose_name_plural = 'Relaciones Usuario-Cliente'
        default_permissions = []  # Deshabilita permisos predeterminados

    def __str__(self):
        """
        Devuelve la representación en cadena de la relación usuario-cliente.

        Returns:
            str: Cadena con formato "email_usuario - nombre_cliente"
        """
        return f"{self.usuario.email} - {self.cliente.nombre}"