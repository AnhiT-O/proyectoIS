from django.db import models
from django.forms import ValidationError

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
