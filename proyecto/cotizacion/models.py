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

    def calcular_precio_venta(self, porcentaje_beneficio=0):
        """
        Calcula el precio de venta aplicando el beneficio del cliente.
        precio_venta = tasa_base + comision_venta - (comision_venta * porcentaje_beneficio)
        """
        tasa_base = self.id_moneda.tasa_base
        comision_venta = self.id_moneda.comision_venta
        beneficio = porcentaje_beneficio / 100
        
        precio = int(tasa_base + comision_venta - (comision_venta * beneficio))
        return precio

    def calcular_precio_compra(self, porcentaje_beneficio=0):
        """
        Calcula el precio de compra aplicando el beneficio del cliente.
        precio_compra = tasa_base - comision_compra - (comision_compra * porcentaje_beneficio)
        """
        tasa_base = self.id_moneda.tasa_base
        comision_compra = self.id_moneda.comision_compra
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

    class Meta:
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
        db_table = 'cotizaciones'
        ordering = ['-fecha_cotizacion']  # Ordena por fecha descendente
        # Asegura que no haya cotizaciones duplicadas para la misma moneda en la misma fecha
        unique_together = ['id_moneda', 'fecha_cotizacion']

    def __str__(self):
        return f"{self.id_moneda.simbolo} - {self.fecha_cotizacion.strftime('%Y-%m-%d %H:%M')}"
