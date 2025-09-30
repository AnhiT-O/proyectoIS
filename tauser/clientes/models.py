from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
import stripe
import logging

# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

class Cliente(models.Model):
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
        Validaciones del modelo
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
        Sobrescribir save para ejecutar validaciones
        """
        # Actualizar el beneficio según el segmento
        self.beneficio_segmento = self.BENEFICIOS_SEGMENTO.get(self.segmento, 0)
        
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre}"

    def tiene_tarjetas_activas(self):
        """
        Verifica si un cliente tiene tarjetas de crédito activas en Stripe.
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
        Obtiene las tarjetas de crédito del cliente desde Stripe.
        Retorna una lista de diccionarios con la información de las tarjetas.
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