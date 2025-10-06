"""
Módulo de modelos para la gestión de clientes.

Este módulo contiene los modelos de datos relacionados con la gestión de clientes
del sistema, incluyendo la información personal, segmentación, integración con Stripe
para métodos de pago y relaciones con usuarios operadores.
"""

from django.db import models

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