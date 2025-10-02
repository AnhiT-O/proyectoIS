from django.db import models
from django.forms import ValidationError
from django.db.models.signals import post_migrate
from django.contrib.postgres.fields import ArrayField
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
    denominaciones = ArrayField(models.IntegerField(), blank=True, default=list)
    stock = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    
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

    def verificar_cambio_cotizacion(self, precio_original):
        """
        Verifica si hubo cambios en la cotización comparando con el precio original
        Args:
            precio_original: El precio que se mostró inicialmente al cliente
        Returns:
            dict: Diccionario con información sobre el cambio de cotización
        """
        precio_actual = self.calcular_precio_venta()  # O calcular_precio_compra según el caso
        if precio_actual != precio_original:
            return {
                'hubo_cambio': True,
                'precio_original': precio_original,
                'precio_actual': precio_actual,
                'diferencia': precio_actual - precio_original
            }
        return {'hubo_cambio': False}

    def ha_cambiado_cotizacion(self, tasa_base_anterior, comision_compra_anterior, comision_venta_anterior):
        """
        Verifica si algún componente de la cotización ha cambiado
        Args:
            tasa_base_anterior: Valor anterior de la tasa base
            comision_compra_anterior: Valor anterior de la comisión de compra
            comision_venta_anterior: Valor anterior de la comisión de venta
        Returns:
            dict: Información sobre los cambios en la cotización
        """
        cambios = {
            'tasa_base': self.tasa_base != tasa_base_anterior,
            'comision_compra': self.comision_compra != comision_compra_anterior,
            'comision_venta': self.comision_venta != comision_venta_anterior,
            'hubo_cambio': False
        }
        
        # Verifica si hubo algún cambio
        if any([cambios['tasa_base'], cambios['comision_compra'], cambios['comision_venta']]):
            cambios['hubo_cambio'] = True
            # Calcular las diferencias en los precios finales
            precio_compra_anterior = tasa_base_anterior - comision_compra_anterior
            precio_venta_anterior = tasa_base_anterior + comision_venta_anterior
            precio_compra_actual = self.tasa_base - self.comision_compra
            precio_venta_actual = self.tasa_base + self.comision_venta
            
            cambios.update({
                'precio_compra_anterior': precio_compra_anterior,
                'precio_venta_anterior': precio_venta_anterior,
                'precio_compra_actual': precio_compra_actual,
                'precio_venta_actual': precio_venta_actual,
                'diferencia_compra': precio_compra_actual - precio_compra_anterior,
                'diferencia_venta': precio_venta_actual - precio_venta_anterior
            })
            
        return cambios


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
                denominaciones=[1, 2, 5, 10, 20, 50, 100],
                stock=1000000
            )
            print("✓ Moneda USD creada automáticamente")

class StockGuaranies(models.Model):
    """
    Modelo para almacenar el stock de guaraníes disponible en la casa de cambio
    """
    cantidad = models.BigIntegerField(
        default=1000000000,
        help_text="Cantidad de guaraníes disponibles en stock"
    )
    denominaciones = ArrayField(models.IntegerField(), blank=True, default=list)

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
            StockGuaranies.objects.create(denominaciones=[2000, 5000, 10000, 20000, 50000, 100000])
            print("Stock inicial de guaraníes creado automáticamente")