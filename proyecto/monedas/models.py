from django.db import models
from django.forms import ValidationError
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone

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
    decimales = models.SmallIntegerField(default=2)
    fecha_cotizacion = models.DateTimeField(default=timezone.now)
    
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
                tasa_base=7030,
                comision_compra=30,
                comision_venta=40,
                fecha_cotizacion=timezone.make_aware(timezone.datetime(2025, 10, 28, 13, 10, 0))
            )
            print("✓ Moneda USD creada automáticamente")

class StockGuaranies(models.Model):
    """
    Modelo para almacenar el stock de guaraníes disponible en la casa de cambio
    """
    cantidad = models.BigIntegerField(
        default=1000000000
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

class Denominacion(models.Model):
    """
    Modelo para representar las denominaciones de una moneda específica
    """
    moneda = models.ForeignKey(Moneda, on_delete=models.CASCADE, null=True, blank=True)
    valor = models.IntegerField()

    class Meta:
        verbose_name = 'Denominación'
        verbose_name_plural = 'Denominaciones'
        db_table = 'denominaciones'
        default_permissions = []

    def __str__(self):
        return f"{self.valor}"
    
@receiver(post_migrate)
def crear_denominaciones_iniciales(sender, **kwargs):
    """
    Crea automáticamente algunas denominaciones iniciales para USD y el stock de guaraníes
    después de ejecutar las migraciones
    """
    if kwargs['app_config'].name == 'monedas':
        usd = Moneda.objects.filter(simbolo='USD').first()
        if usd:
            for valor in [1, 5, 10, 20, 50, 100]:
                Denominacion.objects.create(moneda=usd, valor=valor)
            print("Denominaciones iniciales para USD creadas automáticamente")

        for valor in [2000, 5000, 10000, 20000, 50000, 100000]:
            Denominacion.objects.create(valor=valor)
        print("Denominaciones iniciales para Stock de Guaraníes creadas automáticamente")

class HistorialCotizacion(models.Model):
    """
    Modelo para almacenar el historial de cotizaciones de las monedas
    """
    moneda = models.ForeignKey(Moneda, on_delete=models.CASCADE, related_name='historial_cotizaciones')
    nombre_moneda = models.CharField(max_length=100, default='')  # Nombre de la moneda para facilitar consultas
    fecha = models.DateField()
    tasa_base = models.IntegerField()
    comision_compra = models.IntegerField()
    comision_venta = models.IntegerField()
    precio_compra = models.IntegerField()  # tasa_base - comision_compra
    precio_venta = models.IntegerField()   # tasa_base + comision_venta
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historial de Cotización'
        verbose_name_plural = 'Historial de Cotizaciones'
        db_table = 'historial_cotizaciones'
        default_permissions = []
        # Removemos unique_together para permitir múltiples ediciones por día
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.moneda.nombre} - {self.fecha}"

    def save(self, *args, **kwargs):
        # Guardar automáticamente el nombre de la moneda
        if self.moneda:
            self.nombre_moneda = self.moneda.nombre
        
        # Calcular precios automáticamente
        self.precio_compra = self.tasa_base - self.comision_compra
        self.precio_venta = self.tasa_base + self.comision_venta
        super().save(*args, **kwargs)

from django.db.models.signals import pre_save, post_save

@receiver(pre_save, sender=Moneda)
def guardar_valores_anteriores(sender, instance, **kwargs):
    """
    Guarda los valores anteriores de la moneda antes de actualizar
    """
    if instance.pk:  # Solo si ya existe en la BD
        # old_instance: valores actuales en la BD (ANTES del save)
        old_instance = Moneda.objects.get(pk=instance.pk)
        
        # instance: valores NUEVOS que se van a guardar
        instance._old_tasa_base = old_instance.tasa_base
        instance._old_comision_compra = old_instance.comision_compra
        instance._old_comision_venta = old_instance.comision_venta
        
        # Puedes acceder a ambos:
        print(f"Valor VIEJO: {old_instance.comision_compra}")
        print(f"Valor NUEVO: {instance.comision_compra}")

@receiver(post_save, sender=Moneda)
def crear_historial_cotizacion(sender, instance, created, **kwargs):
    """
    Crea un registro en el historial cuando se crea una moneda o se actualizan
    sus campos de cotización (tasa_base, comision_compra, comision_venta)
    """
    if created:
        fecha_hoy = instance.fecha_cotizacion.date()
        HistorialCotizacion.objects.create(
            moneda=instance,
            nombre_moneda=instance.nombre,
            fecha=fecha_hoy,
            tasa_base=instance.tasa_base,
            comision_compra=instance.comision_compra,
            comision_venta=instance.comision_venta
        )
    else:
        # Verificar si cambió algún campo usando los valores guardados en pre_save
        if (
            hasattr(instance, '_old_tasa_base') and
            (instance.tasa_base != instance._old_tasa_base or
             instance.comision_compra != instance._old_comision_compra or
             instance.comision_venta != instance._old_comision_venta)
        ):
            fecha_hoy = timezone.now().date()
            HistorialCotizacion.objects.create(
                moneda=instance,
                nombre_moneda=instance.nombre,
                fecha=fecha_hoy,
                tasa_base=instance.tasa_base,
                comision_compra=instance.comision_compra,
                comision_venta=instance.comision_venta
            )