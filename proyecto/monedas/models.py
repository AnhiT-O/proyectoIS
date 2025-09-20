from django.db import models
from django.forms import ValidationError
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class Moneda(models.Model):
    nombre = models.CharField(
        max_length=30,
        unique=True,
        blank=False,
        null=False
    )
    simbolo = models.CharField(
        max_length=3,
        unique=True,
        blank=False,
        null=False
    )
    activa = models.BooleanField(default=True)
    tasa_base = models.IntegerField(default=0)
    comision_compra = models.IntegerField(default=0)
    comision_venta = models.IntegerField(default=0)
    decimales = models.SmallIntegerField(default=3)
    fecha_cotizacion = models.DateTimeField(auto_now=True)
    stock = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):
        if self.pk:
            old = Moneda.objects.get(pk=self.pk)
            if (
                self.tasa_base != old.tasa_base or
                self.comision_compra != old.comision_compra or
                self.comision_venta != old.comision_venta
            ):
                self.fecha_cotizacion = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Moneda'
        verbose_name_plural = 'Monedas'
        db_table = 'monedas'
        default_permissions = []  # Deshabilita permisos predeterminados
        permissions = [
            ("gestion", "Puede gestionar monedas (crear y editar)"),
            ("activacion", "Puede activar/desactivar monedas"),
            ("cotizacion", "Puede actualizar cotización de monedas")
        ]

    def get_limite_por_segmentacion(self, segmentacion):
        """Obtiene el porcentaje límite para una segmentación específica"""
        try:
            limitacion = self.limitaciones.get(segmentacion=segmentacion)
            return limitacion.porcentaje_limite
        except:
            return None

    def get_cantidad_maxima_por_segmentacion(self, segmentacion):
        """Calcula la cantidad máxima que puede comprar/vender una segmentación"""
        limite = self.get_limite_por_segmentacion(segmentacion)
        if limite:
            return (self.stock * limite) / 100
        return 0

    def tiene_stock_disponible(self, cantidad_solicitada, segmentacion):
        """Verifica si hay stock suficiente para una operación considerando las limitaciones"""
        cantidad_maxima = self.get_cantidad_maxima_por_segmentacion(segmentacion)
        return cantidad_solicitada <= cantidad_maxima

    def __str__(self):
        return f"{self.nombre} ({self.simbolo})"

class Limitacion(models.Model):
    SEGMENTACION_CHOICES = [
        ('VIP', 'VIP'),
        ('CORPORATIVO', 'Corporativo'),
        ('MINORISTA', 'Minorista'),
    ]

    moneda = models.ForeignKey(
        Moneda,
        on_delete=models.CASCADE,
        related_name='limitaciones',
        verbose_name='Moneda'
    )
    segmentacion = models.CharField(
        max_length=20,
        choices=SEGMENTACION_CHOICES,
        verbose_name='Segmentación'
    )
    porcentaje_limite = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ],
        verbose_name='Porcentaje límite'
    )

    class Meta:
        verbose_name = 'Limitación'
        verbose_name_plural = 'Limitaciones'
        db_table = 'limitaciones'
        unique_together = ['moneda', 'segmentacion']  # No puede haber duplicados de moneda-segmentación

    def __str__(self):
        return f"{self.moneda.nombre} - {self.segmentacion}: {self.porcentaje_limite}%"

    def calcular_cantidad_maxima(self):
        """Calcula la cantidad máxima que se puede comprar/vender según el stock y el porcentaje"""
        return (self.moneda.stock * self.porcentaje_limite) / 100
        verbose_name_plural = 'Limitaciones'
        db_table = 'limitaciones'
        unique_together = ['moneda', 'segmentacion']  # No puede haber duplicados de moneda-segmentación

    def calcular_precio_venta(self, porcentaje_beneficio=0):
        """
        Calcula el precio de venta aplicando el beneficio del cliente.
        precio_venta = tasa_base + comision_venta - (comision_venta * porcentaje_beneficio)
        """
        tasa_base = self.tasa_base
        comision_venta = self.comision_venta
        beneficio = porcentaje_beneficio / 100
        
        precio = int(tasa_base + comision_venta - (comision_venta * beneficio))
        return precio

    def calcular_precio_compra(self, porcentaje_beneficio=0):
        """
        Calcula el precio de compra aplicando el beneficio del cliente.
        precio_compra = tasa_base - comision_compra - (comision_compra * porcentaje_beneficio)
        """
        tasa_base = self.tasa_base
        comision_compra = self.comision_compra
        beneficio = porcentaje_beneficio / 100

        precio = int(tasa_base - comision_compra + (comision_compra * beneficio))
        return precio

    def get_precios_cliente(self, cliente):
        """
        Obtiene los precios de compra y venta para un cliente específico
        aplicando su porcentaje de beneficio.
        """
        # Si hay un cliente, usamos su beneficio_segmento
        porcentaje_beneficio = 0
        if cliente:
            porcentaje_beneficio = cliente.beneficio_segmento
        
        return {
            'precio_venta': self.calcular_precio_venta(porcentaje_beneficio),
            'precio_compra': self.calcular_precio_compra(porcentaje_beneficio)
        }

    def clean(self):
        super().clean()
        if self.simbolo and not self.simbolo.isupper():
            raise ValidationError({'simbolo': 'El símbolo debe contener solo letras en mayúsculas.'})

    def __str__(self):
        return self.nombre


@receiver(post_migrate)
def crear_moneda_usd(sender, **kwargs):
    """
    Crea automáticamente la moneda USD después de ejecutar las migraciones
    """
    # Solo crear si la migración es de la app monedas
    if kwargs['app_config'].name == 'monedas':
        # Verificar si ya existe la moneda USD
        if not Moneda.objects.filter(simbolo='USD').exists():
            Moneda.objects.create(
                nombre='Dólar estadounidense',
                simbolo='USD',
                activa=True,
                tasa_base=7400,
                comision_compra=200,
                comision_venta=250,
                decimales=2
            )
            print("✓ Moneda USD creada automáticamente")
