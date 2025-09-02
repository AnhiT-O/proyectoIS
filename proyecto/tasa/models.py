from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from monedas.models import Moneda
from django.utils import timezone
from django.core.exceptions import ValidationError

class TasaCambio(models.Model):
    moneda = models.ForeignKey(
        Moneda,
        on_delete=models.PROTECT,
        related_name='tasas',
        verbose_name='Moneda'
    )
    precio_base = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(0.0001)],
        verbose_name='Precio Base'
    )
    comision_compra = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name='Comisión de Compra (en decimal, ej: 0.100 = 10%)',
        default=0,
        help_text='Ingrese el valor en decimal (entre 0 y 1). Ejemplo: 0.100 para 10%'
    )
    comision_venta = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name='Comisión de Venta (en decimal, ej: 0.100 = 10%)',
        default=0,
        help_text='Ingrese el valor en decimal (entre 0 y 1). Ejemplo: 0.100 para 10%'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última modificación'
    )
    activa = models.BooleanField(
        default=True,
        verbose_name='Tasa activa'
    )
    ultimo_editor = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Último editor',
        related_name='tasas_editadas'
    )

    class Meta:
        verbose_name = 'Tasa de cambio'
        verbose_name_plural = 'Tasas de cambio'
        db_table = 'tasas_cambio'
        default_permissions = []
        permissions = [
            ("crear_tasa", "Puede crear tasas de cambio"),
            ("editar_tasa", "Puede editar tasas de cambio"),
            ("activar_tasa", "Puede activar/desactivar tasas de cambio"),
            ("ver_tasa", "Puede ver tasas de cambio")
        ]

    def clean(self):
        super().clean()
        # Validar que no exista otra tasa de cambio para la misma moneda.
        # Se excluye la instancia actual para permitir actualizaciones.
        if TasaCambio.objects.filter(moneda=self.moneda).exclude(pk=self.pk).exists():
            raise ValidationError('Ya existe una tasa de cambio registrada para esta moneda.')
        
        if self.precio_base <= 0:
            raise ValidationError('El precio base debe ser mayor que cero.')
        
        if self.comision_compra < 0 or self.comision_venta < 0:
            raise ValidationError('Las comisiones no pueden ser negativas.')

    def __str__(self):
        return f'{self.moneda.simbolo} - Base: {self.precio_base} (Compra: {self.comision_compra}%, Venta: {self.comision_venta}%)'
