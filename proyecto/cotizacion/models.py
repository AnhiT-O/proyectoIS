from django.db import models
from decimal import Decimal
from monedas.models import Moneda
from clientes.models import Cliente

class Cotizacion(models.Model):
    id_moneda = models.ForeignKey(
        Moneda,
        on_delete=models.PROTECT,  # Protege contra eliminación de monedas que tienen cotizaciones
        related_name='cotizaciones',
        verbose_name='Moneda'
    )
    fecha_cotizacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Cotización'
    )

    class Meta:
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
        db_table = 'cotizaciones'
        ordering = ['-fecha_cotizacion']
        default_permissions = []  # Deshabilita permisos predeterminados

    def __str__(self):
        return f"{self.id_moneda.simbolo} - {self.fecha_cotizacion.strftime('%Y-%m-%d %H:%M')}"
