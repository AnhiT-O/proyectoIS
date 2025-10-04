from django.db import models
from django.forms import ValidationError
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField

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
    denominaciones = ArrayField(
        base_field=models.IntegerField(),
        default=list
    )
    
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

    def calcular_precio_venta(self, segmento='minorista'):
        """
        Calcula el precio de venta aplicando el beneficio del cliente.
        precio_venta = tasa_base + comision_venta - (comision_venta * porcentaje_beneficio)
        """
        if segmento == 'corporativo':
            porcentaje_beneficio = 5  # Beneficio del 5% para clientes corporativos
        elif segmento == 'vip':
            porcentaje_beneficio = 10  # Beneficio del 10% para clientes VIP
        else:
            porcentaje_beneficio = 0  # Sin beneficio para clientes minoristas

        tasa_base = self.tasa_base
        comision_venta = self.comision_venta
        beneficio = porcentaje_beneficio / 100
        
        precio = int(tasa_base + comision_venta - (comision_venta * beneficio))
        return precio

    def calcular_precio_compra(self, segmento='minorista'):
        """
        Calcula el precio de compra aplicando el beneficio del cliente.
        precio_compra = tasa_base - comision_compra - (comision_compra * porcentaje_beneficio)
        """
        if segmento == 'corporativo':
            porcentaje_beneficio = 5  # Beneficio del 5% para clientes corporativos
        elif segmento == 'vip':
            porcentaje_beneficio = 10  # Beneficio del 10% para clientes VIP
        else:
            porcentaje_beneficio = 0  # Sin beneficio para clientes minoristas
            
        tasa_base = self.tasa_base
        comision_compra = self.comision_compra
        beneficio = porcentaje_beneficio / 100

        precio = int(tasa_base - comision_compra + (comision_compra * beneficio))
        return precio

    def get_precios_cliente(self, cliente):
        """Obtiene los precios finales para un cliente específico"""
        precio_compra = self.calcular_precio_compra(cliente.segmento)
        precio_venta = self.calcular_precio_venta(cliente.segmento)
        return {
            'precio_compra': precio_compra,
            'precio_venta': precio_venta
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
                denominaciones=[1, 2, 5, 10, 20, 50, 100]
            )
            print("✓ Moneda USD creada automáticamente")

class StockGuaranies(models.Model):
    """
    Modelo para almacenar el stock de guaraníes disponible en la casa de cambio
    """
    cantidad = models.BigIntegerField(
        default=1000000000
    )
    denominaciones = ArrayField(
        base_field=models.IntegerField(),
        default=[2000, 5000, 10000, 20000, 50000, 100000]
    )

    class Meta:
        verbose_name = 'Stock de Guaraníes'
        verbose_name_plural = 'Stock de Guaraníes'
        db_table = 'stock_guaranies'
        default_permissions = []

    def __str__(self):
        return f"Stock: Gs. {self.cantidad:,}"
    
@receiver(post_migrate)
def crear_stock_guaranies_inicial(sender, **kwargs):
    """
    Crea automáticamente el stock inicial de guaraníes después de ejecutar las migraciones
    """
    if kwargs['app_config'].name == 'monedas':
        if not StockGuaranies.objects.exists():
            StockGuaranies.objects.create()
            print("Stock inicial de guaraníes creado automáticamente")