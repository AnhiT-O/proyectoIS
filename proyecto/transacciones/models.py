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
from decimal import Decimal
from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from monedas.models import StockGuaranies

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

@receiver(post_migrate)
def crear_recargos(sender, **kwargs):
    """
    Signal handler que crea automáticamente los recargos predeterminados.
    
    Se ejecuta después de aplicar las migraciones de la aplicación transacciones.
    Crea los recargos estándar para diferentes medios de pago si no existen.
    
    Recargos creados:
        - VISA: 1%
        - MASTERCARD: 1,5%
        - Tigo Money: 2%
        - Billetera Personal: 2%
        - Zimple: 3%
    
    Args:
        sender: La aplicación que envía la señal
        **kwargs: Argumentos adicionales de la señal post_migrate
    """
    # Solo crear si la migración es de la app transacciones
    if kwargs['app_config'].name == 'transacciones':

        if not Recargos.objects.filter(marca='VISA').exists():
            Recargos.objects.create(
                marca='VISA',
                medio='Tarjeta de Crédito',
                recargo='1'
            )

        if not Recargos.objects.filter(marca='MASTERCARD').exists():
            Recargos.objects.create(
                marca='MASTERCARD',
                medio='Tarjeta de Crédito',
                recargo='1.5'
            )

        if not Recargos.objects.filter(marca='Tigo Money').exists():
            Recargos.objects.create(
                marca='Tigo Money',
                medio='Billetera Electrónica',
                recargo='2'
            )

        if not Recargos.objects.filter(marca='Billetera Personal').exists():
            Recargos.objects.create(
                marca='Billetera Personal',
                medio='Billetera Electrónica',
                recargo='2'
            )

        if not Recargos.objects.filter(marca='Zimple').exists():
            Recargos.objects.create(
                marca='Zimple',
                medio='Billetera Electrónica',
                recargo='3'
            )

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

@receiver(post_migrate)
def crear_limite_global_inicial(sender, **kwargs):
    """
    Crea automáticamente el límite global inicial después de ejecutar las migraciones
    """
    if kwargs['app_config'].name == 'monedas':
        if not LimiteGlobal.objects.exists():
            LimiteGlobal.objects.create()
            print("Límite global inicial creado automáticamente")

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
    redondeo_efectivo_monto_final = models.IntegerField()
    monto_final = models.IntegerField()
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
        permissions = [("edicion", "Puede editar límites de transacción y porcentaje de recargos")]  # De momento no hay permisos necesarios
    
    def __str__(self):
        """
        Representación en cadena del modelo Transaccion.
        
        Returns:
            str: Descripción de la transacción en formato "Tipo - Cliente - Monto Moneda"
        """
        return f"{self.tipo.title()} - {self.cliente} - {self.monto} {self.moneda.simbolo}"

    def almacenar_cotizacion_original(self):
        """
        Almacena los precios de compra y venta originales al momento de crear la transacción.
        
        Calcula y guarda los precios según la configuración actual de la moneda
        para poder detectar cambios posteriores.
        """
        if self.moneda:
            # Calcular precios según el tipo de transacción
            precio_compra = self.moneda.tasa_base + self.moneda.comision_compra
            precio_venta = self.moneda.tasa_base - self.moneda.comision_venta
            
            self.precio_compra_original = precio_compra
            self.precio_venta_original = precio_venta
            self.fecha_cotizacion_original = self.moneda.fecha_cotizacion
            self.save(update_fields=['precio_compra_original', 'precio_venta_original', 'fecha_cotizacion_original'])

    def verificar_cambio_cotizacion(self):
        """
        Verifica si la cotización ha cambiado desde que se creó la transacción.
        
        Returns:
            dict: Diccionario con información de cambios o None si no hay cambios
                - 'hay_cambios': boolean indicando si hubo cambios
                - 'valores_anteriores': dict con precio_compra y precio_venta originales
                - 'valores_actuales': dict con precio_compra y precio_venta actuales
        """
        if not self.moneda or not self.precio_compra_original or not self.precio_venta_original:
            return None
            
        # Calcular precios actuales
        precio_compra_actual = self.moneda.tasa_base + self.moneda.comision_compra
        precio_venta_actual = self.moneda.tasa_base - self.moneda.comision_venta
        
        # Verificar si hay cambios
        hay_cambios = (
            precio_compra_actual != self.precio_compra_original or 
            precio_venta_actual != self.precio_venta_original
        )
        
        if hay_cambios:
            return {
                'hay_cambios': True,
                'valores_anteriores': {
                    'precio_compra': self.precio_compra_original,
                    'precio_venta': self.precio_venta_original
                },
                'valores_actuales': {
                    'precio_compra': precio_compra_actual,
                    'precio_venta': precio_venta_actual
                }
            }
        
        return {'hay_cambios': False}

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para actualizar timestamp en cambios de estado.
        
        Cuando el estado de una transacción cambia, actualiza automáticamente
        el campo fecha_hora con el timestamp actual.
        
        Args:
            *args: Argumentos posicionales para el método save del padre
            **kwargs: Argumentos de palabra clave para el método save del padre
        """
        if self.pk:  # Si la instancia ya existe
            try:
                old_instance = Transaccion.objects.get(pk=self.pk)
                if old_instance.estado != self.estado:
                    self.fecha_hora = timezone.now()
            except Transaccion.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)

def calcular_conversion(monto, moneda, operacion, pago='Efectivo', cobro='Efectivo', segmentacion='minorista'):

    if pago.startswith('{'):
        dict_pago = ast.literal_eval(pago)
    else:
        dict_pago = pago
    if cobro.startswith('{'):
        dict_cobro = ast.literal_eval(cobro)
    else:
        dict_cobro = cobro
    redondeo_efectivo_monto = 0
    redondeo_efectivo_monto_final = 0
    monto_original = monto
    if dict_cobro == 'Efectivo' and operacion == 'compra':
        redondeo_efectivo_monto = moneda.denominaciones[0] - (monto % moneda.denominaciones[0])
        if redondeo_efectivo_monto == moneda.denominaciones[0]:
            redondeo_efectivo_monto = 0
        monto += redondeo_efectivo_monto
    elif dict_pago == 'Efectivo' and operacion == 'venta':
        redondeo_efectivo_monto = monto % moneda.denominaciones[0]
        monto -= redondeo_efectivo_monto
    if operacion == 'compra':
        cotizacion = moneda.tasa_base + moneda.comision_venta
        precio_base = monto * (moneda.tasa_base + moneda.comision_venta)
        if segmentacion == 'corporativo':
            monto_final = monto * (moneda.tasa_base + (moneda.comision_venta * Decimal(0.95)))
            porc_beneficio_segmento = 5
        elif segmentacion == 'vip':
            monto_final = monto * (moneda.tasa_base + (moneda.comision_venta * Decimal(0.9)))
            porc_beneficio_segmento = 10
        else:
            monto_final = precio_base
            porc_beneficio_segmento = 0
    else:
        cotizacion = moneda.tasa_base - moneda.comision_compra
        precio_base = monto * (moneda.tasa_base - moneda.comision_compra)
        if segmentacion == 'corporativo':
            monto_final = monto * (moneda.tasa_base - (moneda.comision_compra * Decimal(0.95)))
            porc_beneficio_segmento = 5
        elif segmentacion == 'vip':
            monto_final = monto * (moneda.tasa_base - (moneda.comision_compra * Decimal(0.9)))
            porc_beneficio_segmento = 10
        else:
            monto_final = precio_base
            porc_beneficio_segmento = 0
    beneficio_segmento = abs(precio_base - monto_final)
    if isinstance(dict_pago, dict) and 'brand' in dict_pago:
        monto_recargo_pago =  Decimal(monto_final) * (Decimal(Recargos.objects.get(marca=dict_pago['brand']).recargo) / Decimal(100))
        porc_recargo_pago = Recargos.objects.get(marca=dict_pago['brand']).recargo
    elif dict_pago in Recargos.objects.filter(medio='Billetera Electrónica').values_list('marca', flat=True):
        monto_recargo_pago =  Decimal(monto_final) * (Decimal(Recargos.objects.get(marca=dict_pago).recargo) / Decimal(100))
        porc_recargo_pago = Recargos.objects.get(marca=dict_pago).recargo
    else:
        monto_recargo_pago = 0
        porc_recargo_pago = 0

    if isinstance(dict_cobro, dict) and 'tipo_billetera' in dict_cobro:
        monto_recargo_cobro =  Decimal(monto_final) * (Decimal(Recargos.objects.get(marca=dict_cobro['tipo_billetera']).recargo) / Decimal(100))
        porc_recargo_cobro = Recargos.objects.get(marca=dict_cobro['tipo_billetera']).recargo
    else:
        monto_recargo_cobro = 0
        porc_recargo_cobro = 0
    monto_final = monto_final - monto_recargo_pago - monto_recargo_cobro if operacion == 'venta' else monto_final + monto_recargo_pago + monto_recargo_cobro
    if dict_pago == 'Efectivo' and operacion == 'compra':
        redondeo_efectivo_monto_final = monto_final % StockGuaranies.objects.first().denominaciones[0]
        monto_final -= redondeo_efectivo_monto_final
    if dict_cobro == 'Efectivo' and operacion == 'venta':
        redondeo_efectivo_monto_final = StockGuaranies.objects.first().denominaciones[0] - (monto_final % StockGuaranies.objects.first().denominaciones[0])
        if redondeo_efectivo_monto_final == StockGuaranies.objects.first().denominaciones[0]:
            redondeo_efectivo_monto_final = 0
        monto_final += redondeo_efectivo_monto_final
    return {
        'cotizacion': int(cotizacion),
        'precio_base': int(precio_base),
        'beneficio_segmento': int(beneficio_segmento),
        'porc_beneficio_segmento': f'{porc_beneficio_segmento}%',
        'redondeo_efectivo_monto': redondeo_efectivo_monto,
        'redondeo_efectivo_monto_final': int(redondeo_efectivo_monto_final),
        'monto_recargo_pago': int(monto_recargo_pago),
        'porc_recargo_pago': f'{porc_recargo_pago}%',
        'monto_recargo_cobro': int(monto_recargo_cobro),
        'porc_recargo_cobro': f'{porc_recargo_cobro}%',
        'monto_original': monto_original,
        'monto': monto,
        'monto_final': int(monto_final)
    }