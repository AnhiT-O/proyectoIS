from django.db import models
from django.forms import ValidationError
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone
from datetime import date

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
                decimales=2,
                stock=1000000
            )
            print("✓ Moneda USD creada automáticamente")


class LimiteGlobal(models.Model):
    """
    Modelo para almacenar los límites globales de transacciones
    que aplican a todos los clientes según la ley de casas de cambio
    """
    limite_diario = models.IntegerField(
        default=90000000,
        help_text="Límite diario global en guaraníes"
    )
    limite_mensual = models.IntegerField(
        default=450000000,
        help_text="Límite mensual global en guaraníes"
    )
    fecha_inicio = models.DateField(
        default=date.today,
        help_text="Fecha desde cuando rige este límite"
    )
    fecha_fin = models.DateField(
        null=True, 
        blank=True,
        help_text="Fecha hasta cuando rige este límite (opcional)"
    )
    activo = models.BooleanField(
        default=True,
        help_text="Indica si este límite está vigente"
    )

    class Meta:
        verbose_name = 'Límite Global'
        verbose_name_plural = 'Límites Globales'
        db_table = 'limite_global'
        default_permissions = []
        permissions = [
            ("gestion", "Puede gestionar límites globales"),
        ]

    def clean(self):
        super().clean()
        if self.limite_diario <= 0:
            raise ValidationError({'limite_diario': 'El límite diario debe ser mayor a 0'})
        if self.limite_mensual <= 0:
            raise ValidationError({'limite_mensual': 'El límite mensual debe ser mayor a 0'})
        if self.limite_diario > self.limite_mensual:
            raise ValidationError({'limite_diario': 'El límite diario no puede ser mayor al mensual'})

    def __str__(self):
        return f"Límite Diario: {self.limite_diario:,} - Mensual: {self.limite_mensual:,}"

    @classmethod
    def obtener_limite_vigente(cls):
        """
        Retorna el límite global vigente para la fecha actual
        """
        hoy = date.today()
        return cls.objects.filter(
            activo=True,
            fecha_inicio__lte=hoy
        ).filter(
            models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gte=hoy)
        ).first()


class ConsumoLimiteCliente(models.Model):
    """
    Modelo para registrar el consumo acumulado de límites por cliente
    Se actualiza con cada transacción y se resetea diaria/mensualmente
    """
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        related_name='consumos_limite'
    )
    fecha = models.DateField(
        default=date.today,
        help_text="Fecha del registro de consumo"
    )
    consumo_diario = models.IntegerField(
        default=0,
        help_text="Consumo acumulado del día en guaraníes"
    )
    consumo_mensual = models.IntegerField(
        default=0,
        help_text="Consumo acumulado del mes en guaraníes"
    )

    class Meta:
        verbose_name = 'Consumo de Límite Cliente'
        verbose_name_plural = 'Consumos de Límites Clientes'
        db_table = 'consumo_limite_cliente'
        unique_together = ['cliente', 'fecha']
        default_permissions = []

    def clean(self):
        super().clean()
        if self.consumo_diario < 0:
            raise ValidationError({'consumo_diario': 'El consumo diario no puede ser negativo'})
        if self.consumo_mensual < 0:
            raise ValidationError({'consumo_mensual': 'El consumo mensual no puede ser negativo'})

    def __str__(self):
        return f"{self.cliente.nombre} - {self.fecha} - Diario: {self.consumo_diario:,}"


@receiver(post_migrate)
def crear_limite_global_inicial(sender, **kwargs):
    """
    Crea automáticamente el límite global inicial después de ejecutar las migraciones
    """
    if kwargs['app_config'].name == 'monedas':
        if not LimiteGlobal.objects.exists():
            LimiteGlobal.objects.create(
                limite_diario=90000000,  # 90 millones
                limite_mensual=450000000,  # 450 millones
                activo=True
            )
            print("Límite global inicial creado automáticamente")

@receiver(models.signals.post_save, sender='clientes.Cliente')
def crear_consumo_limite_cliente(sender, instance, created, **kwargs):
    """
    Crea automáticamente un registro de ConsumoLimiteCliente cuando se crea un nuevo cliente
    """
    if created:
        ConsumoLimiteCliente.objects.create(
            cliente=instance,
            fecha=date.today(),
            consumo_diario=0,
            consumo_mensual=0
        )
