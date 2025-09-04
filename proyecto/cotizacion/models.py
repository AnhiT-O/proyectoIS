from django.db import models
from monedas.models import Moneda

class Cotizacion(models.Model):
    id_moneda = models.ForeignKey(
        Moneda,
        on_delete=models.PROTECT,  # Protege contra eliminación de monedas que tienen cotizaciones
        related_name='cotizaciones',
        verbose_name='Moneda'
    )
    precio_venta = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Precio de Venta'
    )
    precio_compra = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Precio de Compra'
    )
    fecha_cotizacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Cotización'
    )

    class Meta:
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
        db_table = 'cotizaciones'
        ordering = ['-fecha_cotizacion']  # Ordena por fecha descendente
        # Asegura que no haya cotizaciones duplicadas para la misma moneda en la misma fecha
        unique_together = ['id_moneda', 'fecha_cotizacion']

    def __str__(self):
        return f"{self.id_moneda.simbolo} - {self.fecha_cotizacion.strftime('%Y-%m-%d %H:%M')}"
