"""
Modelos para el sistema de transacciones de Global Exchange.

Este módulo contiene los modelos de datos relacionados con las transacciones
financieras, incluyendo la gestión de recargos y el procesamiento de 
transacciones de compra y venta de monedas extranjeras.

Clases principales:
    - Recargos: Gestiona los recargos aplicables por tipo de medio de pago
    - Transaccion: Representa una transacción de compra o venta de monedas

Author: Equipo de desarrollo Global Exchange
Date: 2024
"""

import ast
from datetime import date
from decimal import Decimal
import secrets
from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone
import stripe
from monedas.models import Moneda, StockGuaranies
from django.db import transaction

class Recargos(models.Model):
    """
    Modelo para almacenar recargos aplicables según el medio de pago.
    """
    medio = models.CharField(max_length=50)
    marca = models.CharField(max_length=100, unique=True)
    recargo = models.DecimalField(max_digits=4, decimal_places=1)

    class Meta:
        verbose_name = "Recargo"
        verbose_name_plural = "Recargos"
        db_table = "recargos"
        default_permissions = []  # Deshabilitar permisos por defecto

    def __str__(self):
        """
        Representación en cadena del modelo Recargos.
        
        Returns:
            str: La marca del recargo
        """
        return self.marca

class LimiteGlobal(models.Model):
    """
    Modelo para almacenar los límites globales de transacciones
    que aplican a todos los clientes según la ley de casas de cambio
    """
    limite_diario = models.BigIntegerField(
        default=90000000,
        help_text="Límite diario global en guaraníes"
    )
    limite_mensual = models.BigIntegerField(
        default=450000000,
        help_text="Límite mensual global en guaraníes"
    )

    class Meta:
        verbose_name = 'Límite Global'
        verbose_name_plural = 'Límites Globales'
        db_table = 'limite_global'
        default_permissions = []

    def __str__(self):
        return f"Límite Diario: {self.limite_diario:,} - Mensual: {self.limite_mensual:,}"

class Transaccion(models.Model):
    """
    Modelo principal para representar transacciones de compra y venta de monedas.
    
    Una transacción registra todos los detalles de una operación de cambio de moneda,
    incluyendo el cliente, tipo de operación, medios de pago/cobro, montos y estado.
    
    Attributes:
        cliente (ForeignKey): Cliente que realiza la transacción
        tipo (CharField): Tipo de operación ('compra' o 'venta')
        moneda (ForeignKey): Moneda extranjera involucrada en la transacción
        monto (DecimalField): Cantidad de la moneda extranjera
        medio_pago (CharField): Forma de pago del cliente (efectivo, tarjeta, etc.)
        medio_cobro (CharField): Forma de cobro para entregar el dinero al cliente
        fecha_hora (DateTimeField): Timestamp de creación/actualización de la transacción
        estado (CharField): Estado actual de la transacción (Pendiente, Completada, etc.)
        token (CharField): Token único para transacciones que lo requieren
        token_expiracion (DateTimeField): Fecha y hora de expiración del token
        usuario (ForeignKey): Usuario del sistema que procesó la transacción
        
    Meta:
        verbose_name: "Transacción"
        verbose_name_plural: "Transacciones"
        db_table: "transacciones"
    """
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10)  # 'compra' o 'venta'
    moneda = models.ForeignKey('monedas.Moneda', on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=30, decimal_places=8)
    cotizacion = models.IntegerField()
    precio_base = models.IntegerField()
    monto_original = models.DecimalField(max_digits=30, decimal_places=8)
    beneficio_segmento = models.IntegerField()
    porc_beneficio_segmento = models.CharField(max_length=3)
    recargo_pago = models.IntegerField()
    porc_recargo_pago = models.CharField(max_length=4)
    recargo_cobro = models.IntegerField()
    porc_recargo_cobro = models.CharField(max_length=4)
    redondeo_efectivo_monto = models.DecimalField(max_digits=30, decimal_places=8)
    redondeo_efectivo_precio_final = models.IntegerField()
    precio_final = models.IntegerField()
    medio_pago = models.CharField(max_length=50) 
    medio_cobro = models.CharField(max_length=100)  
    fecha_hora = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='Pendiente')
    razon = models.CharField(max_length=100, blank=True, null=True) 
    token = models.CharField(max_length=255, blank=True, null=True)  
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Transacción"
        verbose_name_plural = "Transacciones"
        db_table = "transacciones"
        default_permissions = []  # Deshabilitar permisos por defecto
        permissions = [
            ("edicion", "Puede editar límites de transacción y porcentaje de recargos"),
            ("visualizacion", "Puede ver el historial de todos los clientes")
            ] 
    
    def __str__(self):
        """
        Representación en cadena del modelo Transaccion.
        
        Returns:
            str: Descripción de la transacción en formato "Tipo - Cliente - Monto Moneda"
        """
        return f"{self.tipo.title()} - {self.cliente} - {self.monto} {self.moneda.simbolo}"
    
@transaction.atomic
def procesar_transaccion(transaccion, recibido=0):
    
    if transaccion.medio_pago == 'Transferencia Bancaria':
        if recibido < transaccion.precio_final:
            print('Notificar usuario que transferencia es incompleta')
        else:
            transaccion.estado = 'Confirmada'
            transaccion.fecha_hora = timezone.now()
            stock = StockGuaranies.objects.first()
            stock.cantidad += recibido
            stock.save()
            transaccion.cliente.consumo_diario += transaccion.precio_final
            transaccion.cliente.consumo_mensual += transaccion.precio_final
            transaccion.cliente.ultimo_consumo = date.today()
            transaccion.cliente.save()
            transaccion.save()
            print('Notificar usuario que transferencia fue confirmada y transacción confirmada')
    elif transaccion.medio_pago in Recargos.objects.filter(medio='Billetera Electrónica'):
        if recibido < transaccion.precio_final:
            print('Notificar usuario que transferencia es incompleta')
        else:
            transaccion.estado = 'Confirmada'
            transaccion.fecha_hora = timezone.now()
            stock = StockGuaranies.objects.first()
            monto_recargo_pago = Decimal(recibido) * (Decimal(Recargos.objects.get(marca=transaccion.medio_pago).recargo) / Decimal(100))
            stock.cantidad += recibido - monto_recargo_pago
            stock.save()
            transaccion.cliente.consumo_diario += transaccion.precio_final
            transaccion.cliente.consumo_mensual += transaccion.precio_final
            transaccion.cliente.ultimo_consumo = date.today()
            transaccion.cliente.save()
            transaccion.save()
            print('Notificar usuario que transferencia fue confirmada y transacción confirmada')
    elif transaccion.medio_pago.startswith('Tarjeta de Crédito'):
        if transaccion.tipo == 'compra':
            transaccion.estado = 'Confirmada'
            transaccion.fecha_hora = timezone.now()
            stock = StockGuaranies.objects.first()
            stock.cantidad += transaccion.precio_final - transaccion.recargo_pago
            stock.save()
            transaccion.cliente.consumo_diario += transaccion.precio_final
            transaccion.cliente.consumo_mensual += transaccion.precio_final
            transaccion.cliente.ultimo_consumo = date.today()
            transaccion.cliente.save()
            transaccion.save()
        else:
            transaccion.estado = 'Confirmada'
            transaccion.fecha_hora = timezone.now()
            stock = StockGuaranies.objects.first()
            stock.cantidad += (transaccion.monto * transaccion.moneda.tasa_base) - transaccion.recargo_pago
            stock.save()
            transaccion.cliente.consumo_diario += transaccion.precio_final
            transaccion.cliente.consumo_mensual += transaccion.precio_final
            transaccion.cliente.ultimo_consumo = date.today()
            transaccion.cliente.save()
            transaccion.save()
            if transaccion.medio_cobro != 'Efectivo':
                stock.cantidad -= transaccion.precio_final + transaccion.recargo_cobro
                stock.save()
                print('Notificar usuario que se realizó la transferencia en su cuenta o billetera')
                transaccion.estado = 'Completa'
                transaccion.fecha_hora = timezone.now()
                transaccion.save()
