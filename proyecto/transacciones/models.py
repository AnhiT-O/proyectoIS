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

from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta


class Recargos(models.Model):
    """
    Modelo para gestionar los recargos aplicables por tipo de medio de pago.
    
    Los recargos son porcentajes adicionales que se aplican a las transacciones
    según el medio de pago utilizado (ej: tarjeta de crédito, billeteras digitales).
    
    Attributes:
        nombre (CharField): Nombre del medio de pago (ej: "Tarjeta de Crédito")
        recargo (SmallIntegerField): Porcentaje de recargo a aplicar (0-100)
        
    Meta:
        verbose_name: "Recargo"
        verbose_name_plural: "Recargos"
        db_table: "recargos"
        permissions: [('edicion', 'Puede editar recargos')]
    """
    nombre = models.CharField(max_length=50)
    recargo = models.SmallIntegerField(default=0)

    class Meta:
        verbose_name = "Recargo"
        verbose_name_plural = "Recargos"
        db_table = "recargos"
        default_permissions = []  # Deshabilita permisos predeterminados
        permissions = [
            ('edicion', 'Puede editar recargos'),
        ]

    def __str__(self):
        """
        Representación en cadena del modelo Recargos.
        
        Returns:
            str: El nombre del medio de pago
        """
        return self.nombre


@receiver(post_migrate)
def crear_recargos(sender, **kwargs):
    """
    Signal handler que crea automáticamente los recargos predeterminados.
    
    Se ejecuta después de aplicar las migraciones de la aplicación transacciones.
    Crea los recargos estándar para diferentes medios de pago si no existen.
    
    Recargos creados:
        - Tarjeta de Crédito: 1%
        - Tigo Money: 2%
        - Billetera Personal: 2%
        - Zimple: 3%
    
    Args:
        sender: La aplicación que envía la señal
        **kwargs: Argumentos adicionales de la señal post_migrate
    """
    # Solo crear si la migración es de la app transacciones
    if kwargs['app_config'].name == 'transacciones':

        if not Recargos.objects.filter(nombre='Tarjeta de Crédito').exists():
            Recargos.objects.create(
                nombre='Tarjeta de Crédito',
                recargo=1
            )

        if not Recargos.objects.filter(nombre='Tigo Money').exists():
            Recargos.objects.create(
                nombre='Tigo Money',
                recargo=2
            )

        if not Recargos.objects.filter(nombre='Billetera Personal').exists():
            Recargos.objects.create(
                nombre='Billetera Personal',
                recargo=2
            )

        if not Recargos.objects.filter(nombre='Zimple').exists():
            Recargos.objects.create(
                nombre='Zimple',
                recargo=3
            )

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
    medio_pago = models.CharField(max_length=50) 
    medio_cobro = models.CharField(max_length=100, default='')  # Agregar campo medio_cobro 
    fecha_hora = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='Pendiente')
    token = models.CharField(max_length=255, blank=True, null=True)  # Campo para el token
    token_expiracion = models.DateTimeField(blank=True, null=True)  # Campo para la expiración del token
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE)
    
    # Campos para almacenar cotizaciones originales al crear la transacción
    precio_compra_original = models.IntegerField(null=True, blank=True)  # Precio de compra al momento de crear la transacción
    precio_venta_original = models.IntegerField(null=True, blank=True)   # Precio de venta al momento de crear la transacción
    fecha_cotizacion_original = models.DateTimeField(null=True, blank=True)  # Fecha de cotización original
    
    class Meta:
        verbose_name = "Transacción"
        verbose_name_plural = "Transacciones"
        db_table = "transacciones"
        default_permissions = []
        permissions = []  # De momento no hay permisos necesarios
    
    def __str__(self):
        """
        Representación en cadena del modelo Transaccion.
        
        Returns:
            str: Descripción de la transacción en formato "Tipo - Cliente - Monto Moneda"
        """
        return f"{self.tipo.title()} - {self.cliente} - {self.monto} {self.moneda.simbolo}"
    
    def token_valido(self):
        """
        Verifica si el token de la transacción aún es válido.
        
        Un token es válido si existe y no ha expirado según su timestamp
        de expiración configurado.
        
        Returns:
            bool: True si el token es válido, False en caso contrario
        """
        if not self.token or not self.token_expiracion:
            return False
        return timezone.now() < self.token_expiracion
    
    def establecer_token_con_expiracion(self, token):
        """
        Asigna un token a la transacción con tiempo de expiración automático.
        
        Establece el token y calcula su fecha de expiración (5 minutos desde ahora).
        Guarda automáticamente los cambios en la base de datos.
        
        Args:
            token (str): Token único generado para la transacción
        """
        self.token = token
        self.token_expiracion = timezone.now() + timedelta(minutes=5)
        self.save()
    
    @classmethod
    def limpiar_tokens_expirados(cls):
        """
        Elimina todas las transacciones con tokens expirados del sistema.
        
        Método de clase que busca y elimina transacciones cuyo token ha expirado
        según el timestamp actual. Útil para limpieza periódica del sistema.
        
        Returns:
            int: Número de transacciones eliminadas
        """
        now = timezone.now()
        transacciones_expiradas = cls.objects.filter(
            token__isnull=False,
            token_expiracion__lt=now
        )
        count = transacciones_expiradas.count()
        transacciones_expiradas.delete()
        return count

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