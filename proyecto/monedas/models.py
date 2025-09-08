from django.db import models
from django.forms import ValidationError
from django.db.models.signals import post_migrate
from django.dispatch import receiver

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
    tasa_base = models.DecimalField(default=0, max_digits=15, decimal_places=2, verbose_name='Tasa base')
    comision_compra = models.DecimalField(default=0, max_digits=15, decimal_places=2, verbose_name='Comisión de compra')
    comision_venta = models.DecimalField(default=0, max_digits=15, decimal_places=2, verbose_name='Comisión de venta')
    decimales = models.SmallIntegerField(default=3)

    class Meta:
        verbose_name = 'Moneda'
        verbose_name_plural = 'Monedas'
        db_table = 'monedas'
        default_permissions = []  # Deshabilita permisos predeterminados
        permissions = [
            ("gestion", "Puede gestionar monedas (crear y editar)"),
            ("activacion", "Puede activar/desactivar monedas"),
            ("cambiar_tasa", "Puede cambiar la tasa base de una moneda"),
            ("cambiar_decimales", "Puede cambiar el número de decimales de una moneda"),    
            ("cambiar_comisiones", "Puede cambiar las comisiones de compra y venta de una moneda")
        ]

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
                nombre='Dólar Estadounidense',
                simbolo='USD',
                activa=True,
                tasa_base=7400,
                comision_compra=200,
                comision_venta=250,
                decimales=2
            )
            print("✓ Moneda USD creada automáticamente")
