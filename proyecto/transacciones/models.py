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
import os
from django.conf import settings
import socket
import requests
from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone
import stripe
from monedas.models import Moneda, StockGuaranies, Denominacion
from django.db import transaction
import random
import string
from django.core.mail import EmailMessage

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

        if not Recargos.objects.filter(marca='PANAL').exists():
            Recargos.objects.create(
                marca='PANAL',
                medio='Tarjeta de Crédito',
                recargo='2'
            )

        if not Recargos.objects.filter(marca='CABAL').exists():
            Recargos.objects.create(
                marca='CABAL',
                medio='Tarjeta de Crédito',
                recargo='1'
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

class TransactionToken(models.Model):
    """
    Modelo para almacenar tokens temporales de autenticación de dos factores
    para transacciones que requieren verificación adicional.
    """
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE)
    token = models.CharField(max_length=6)  # Token de 6 dígitos
    transaccion_data = models.JSONField()  # Datos de la transacción pendiente
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Token de Transacción"
        verbose_name_plural = "Tokens de Transacción"
        db_table = "transaction_tokens"
        default_permissions = []
        
    def __str__(self):
        return f"Token {self.token} - Usuario: {self.usuario.username}"
    
    def is_valid(self):
        """
        Verifica si el token es válido (no usado y no expirado)
        """
        return not self.used and timezone.now() <= self.expires_at
    
    def mark_as_used(self):
        """
        Marca el token como usado
        """
        self.used = True
        self.save()
    
    @classmethod
    def generate_token(cls, usuario, transaccion_data):
        """
        Genera un nuevo token para un usuario y datos de transacción específicos.
        Elimina tokens previos no usados del mismo usuario.
        """
        from django.conf import settings
        
        # Eliminar tokens previos no usados del usuario
        cls.objects.filter(usuario=usuario, used=False).delete()
        
        # Generar token de 6 dígitos
        token = ''.join(random.choices(string.digits, k=settings.TWO_FACTOR_AUTH['TOKEN_LENGTH']))
        
        # Calcular tiempo de expiración
        expires_at = timezone.now() + timezone.timedelta(
            minutes=settings.TWO_FACTOR_AUTH['TOKEN_EXPIRY_MINUTES']
        )
        
        # Crear y guardar el token
        token_obj = cls.objects.create(
            usuario=usuario,
            token=token,
            transaccion_data=transaccion_data,
            expires_at=expires_at
        )
        
        return token_obj

class Tauser(models.Model):
    puerto = models.SmallIntegerField(unique=True)
    sucursal = models.CharField(max_length=100, unique=True)
    billetes = models.ManyToManyField(Denominacion, through='BilletesTauser', blank=True)

    class Meta:
        verbose_name = "Tauser"
        verbose_name_plural = "Tausers"
        db_table = "tausers"
        default_permissions = []
        permissions = [
            ("revision", "Puede revisar información de tausers")
        ]
    
    def __str__(self):
        """
        Representación en cadena del TAUser.
        
        Returns:
            str: Descripción del TAUser en formato "TAUser Puerto {puerto}"
        """
        return f"TAUser Puerto {self.puerto}"
    
    def esta_activo(self):
        """
        Verifica si hay un servidor Django corriendo en el puerto del TAUser.
        
        Primero verifica si el puerto está en uso, luego intenta hacer una petición HTTP
        para confirmar que es un servidor Django.
        
        Returns:
            bool: True si hay un servidor Django corriendo, False en caso contrario
        """
        try:
            # Verificar si el puerto está en uso
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)  # Timeout de 1 segundo
                result = sock.connect_ex(('localhost', self.puerto))
                
                if result != 0:
                    # Puerto no está en uso
                    return False
            
            # Si el puerto está en uso, verificar si es un servidor Django
            try:
                response = requests.get(
                    f'http://localhost:{self.puerto}/',
                    timeout=2,
                    headers={'User-Agent': 'TAUser-Checker/1.0'}
                )
                
                # Verificar si la respuesta contiene indicadores de Django
                # Django típicamente incluye estos headers o contenido
                django_indicators = [
                    'django' in response.headers.get('server', '').lower(),
                    'csrftoken' in response.text.lower(),
                    'django' in response.text.lower(),
                    response.status_code in [200, 302, 404]  # Códigos típicos de Django
                ]
                
                return any(django_indicators)
                
            except requests.exceptions.RequestException:
                # Si hay error en la petición HTTP pero el puerto está abierto,
                # asumimos que podría ser Django pero no responde correctamente
                return True
                
        except Exception:
            return False
    
class BilletesTauser(models.Model):
    tauser = models.ForeignKey(Tauser, on_delete=models.CASCADE)
    denominacion = models.ForeignKey(Denominacion, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Billete Tauser"
        verbose_name_plural = "Billetes Tauser"
        db_table = "billetes_tauser"
        default_permissions = []

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
    tipo = models.CharField(max_length=7)  # 'compra' o 'venta'
    moneda = models.ForeignKey('monedas.Moneda', on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=30, decimal_places=8)
    cotizacion = models.IntegerField()
    precio_base = models.IntegerField()
    beneficio_segmento = models.IntegerField()
    porc_beneficio_segmento = models.CharField(max_length=3)
    recargo_pago = models.IntegerField()
    porc_recargo_pago = models.CharField(max_length=4)
    recargo_cobro = models.IntegerField()
    porc_recargo_cobro = models.CharField(max_length=4)
    precio_final = models.IntegerField()
    pagado = models.IntegerField(default=0)
    medio_pago = models.CharField(max_length=50) 
    medio_cobro = models.CharField(max_length=100)  
    fecha_hora = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='Pendiente')
    razon = models.CharField(max_length=100, blank=True, null=True) 
    token = models.CharField(max_length=8, blank=True, null=True, unique=True)
    factura = models.CharField(max_length=100, blank=True, null=True)
    numero_factura = models.SmallIntegerField(blank=True, null=True)
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Transacción"
        verbose_name_plural = "Transacciones"
        db_table = "transacciones"
        default_permissions = []  # Deshabilitar permisos por defecto
        permissions = [
            ("edicion", "Puede editar límites de transacción y porcentaje de recargos")
            ] 
    
    def __str__(self):
        """
        Representación en cadena del modelo Transaccion.
        
        Returns:
            str: Descripción de la transacción en formato "Tipo - Cliente - Monto Moneda"
        """
        return f"{self.tipo.title()} - {self.cliente} - {self.monto} {self.moneda.simbolo}"

def calcular_conversion(monto, moneda, operacion, pago='Efectivo', cobro='Efectivo', segmentacion='minorista'):
    """
    Returns:
        cotizacion (int): Cotización de la moneda según el tipo de operación
        precio_base (int): Monto en guaraníes sin considerar recargos o beneficios por segmento
        porc_beneficio_segmento (str): Porcentaje de beneficio aplicado según el segmento del cliente
        beneficio_segmento (int): Beneficio aplicado en la operación según el segmento del cliente
        monto_recargo_pago (int): Monto del recargo aplicado según el medio de pago
        porc_recargo_pago (str): Porcentaje del recargo aplicado según el medio de pago
        monto_recargo_cobro (int): Monto del recargo aplicado según el medio de cobro
        porc_recargo_cobro (str): Porcentaje del recargo aplicado según el medio
        monto (Decimal): Monto de la divisa a operar
        precio_final (int): Monto en guaraníes final a pagar o cobrar
    """
    # Primero convertimos el pago y cobro a diccionarios si vienen como strings
    if pago.startswith('{'):
        dict_pago = ast.literal_eval(pago)
    else:
        dict_pago = pago
    if cobro.startswith('{'):
        dict_cobro = ast.literal_eval(cobro)
    else:
        dict_cobro = cobro
    # Calculos para compra
    if operacion == 'compra':
        # Se guarda la cotización y el precio base
        cotizacion = moneda.tasa_base + moneda.comision_venta
        precio_base = monto * cotizacion
        # Calculo del precio final según el segmento
        if segmentacion == 'corporativo':
            precio_final = monto * (moneda.tasa_base + (moneda.comision_venta * Decimal(0.95)))
            porc_beneficio_segmento = 5
        elif segmentacion == 'vip':
            precio_final = monto * (moneda.tasa_base + (moneda.comision_venta * Decimal(0.9)))
            porc_beneficio_segmento = 10
        else:
            precio_final = precio_base
            porc_beneficio_segmento = 0
        # Se guarda el beneficio por segmento
        beneficio_segmento = abs(precio_base - precio_final)
        # Calculo de recargos por medio de pago
        # Si el pago es con tarjeta de crédito
        if isinstance(dict_pago, dict) and 'brand' in dict_pago:
            monto_recargo_pago =  Decimal(precio_final * Recargos.objects.get(marca=dict_pago['brand']).recargo) / Decimal(100-Recargos.objects.get(marca=dict_pago['brand']).recargo)
            porc_recargo_pago = Recargos.objects.get(marca=dict_pago['brand']).recargo
        # Si el pago es con billetera electrónica
        elif dict_pago in Recargos.objects.filter(medio='Billetera Electrónica').values_list('marca', flat=True):
            monto_recargo_pago =  Decimal(precio_final * Recargos.objects.get(marca=dict_pago).recargo) / Decimal(100-Recargos.objects.get(marca=dict_pago).recargo)
            porc_recargo_pago = Recargos.objects.get(marca=dict_pago).recargo
        # Si el pago es en efectivo o transferencia, no hay recargo
        else:
            monto_recargo_pago = 0
            porc_recargo_pago = 0
        # Calculo del monto en guaraníes a pagar con recargos
        precio_final += monto_recargo_pago
        # No hay recargo por medio de cobro ya que siempre es en efectivo
        monto_recargo_cobro = 0
        porc_recargo_cobro = 0
    # Calculos para venta
    else:
        # Se guarda la cotización y el precio base
        cotizacion = moneda.tasa_base - moneda.comision_compra
        precio_base = monto * cotizacion
        # Calculo del precio final según el segmento
        if segmentacion == 'corporativo':
            precio_final = monto * (moneda.tasa_base - (moneda.comision_compra * Decimal(0.95)))
            porc_beneficio_segmento = 5
        elif segmentacion == 'vip':
            precio_final = monto * (moneda.tasa_base - (moneda.comision_compra * Decimal(0.9)))
            porc_beneficio_segmento = 10
        else:
            precio_final = precio_base
            porc_beneficio_segmento = 0
        # Se guarda el beneficio por segmento
        beneficio_segmento = abs(precio_base - precio_final)
        # Calculo de recargos por medio de pago y cobro
        # Si el pago es con tarjeta de crédito
        if isinstance(dict_pago, dict) and 'brand' in dict_pago:
            monto_recargo_pago =  Decimal(monto * moneda.tasa_base) * (Decimal(Recargos.objects.get(marca=dict_pago['brand']).recargo) / Decimal(100))
            porc_recargo_pago = Recargos.objects.get(marca=dict_pago['brand']).recargo
        else:
            monto_recargo_pago = 0
            porc_recargo_pago = 0
        # Si el cobro es con billetera electrónica
        if isinstance(dict_cobro, dict) and 'tipo_billetera' in dict_cobro:
            monto_recargo_cobro =  Decimal(precio_final) * (Decimal(Recargos.objects.get(marca=dict_cobro['tipo_billetera']).recargo) / Decimal(100))
            porc_recargo_cobro = Recargos.objects.get(marca=dict_cobro['tipo_billetera']).recargo
        else:
        # Si el cobro es en efectivo o cuenta bancaria, no hay recargo
            monto_recargo_cobro = 0
            porc_recargo_cobro = 0
        # Calculo del monto en guaraníes a cobrar con recargos
        precio_final -= monto_recargo_pago + monto_recargo_cobro
            
    return {
        'cotizacion': int(cotizacion),
        'precio_base': int(precio_base),
        'beneficio_segmento': int(beneficio_segmento),
        'porc_beneficio_segmento': f'{porc_beneficio_segmento}%',
        'monto_recargo_pago': int(monto_recargo_pago),
        'porc_recargo_pago': f'{porc_recargo_pago}%',
        'monto_recargo_cobro': int(monto_recargo_cobro),
        'porc_recargo_cobro': f'{porc_recargo_cobro}%',
        'monto': monto,
        'precio_final': int(precio_final)
    }

def procesar_pago_stripe(transaccion, payment_method_id):
    """
    Procesa un pago con Stripe para una transacción dada.
    
    Args:
        transaccion (Transaccion): La transacción a procesar
    
    Returns:
        dict: Diccionario con 'token' (str) y 'datos' (dict) de la transacción
        
    Raises:
        ValueError: Si la transacción no existe
    """
    try:
        if transaccion.tipo == 'venta':
            monto_centavos = int(transaccion.monto * 100)
            moneda_stripe = 'usd' 
        else:
            monto_centavos = transaccion.precio_final
            moneda_stripe = 'pyg' 
        # Crear PaymentIntent
        payment_intent = stripe.PaymentIntent.create(
            amount=monto_centavos,
            currency=moneda_stripe,
            payment_method=payment_method_id,
            customer=transaccion.cliente.id_stripe,
            confirmation_method='manual',
            confirm=True,
            return_url='https://localhost:8000',  # URL de retorno (puedes personalizar)
            metadata={
                'transaccion_id': str(transaccion.id),
                'tipo': transaccion.tipo,
                'cliente_id': str(transaccion.cliente.id)
            }
        )

        print(f"Pago Stripe procesado exitosamente para transacción {transaccion.id}. PaymentIntent: {payment_intent.id}")
        
        return {
            'success': True,
            'payment_intent_id': payment_intent.id,
            'status': payment_intent.status,
            'error': None
        }
        
    except Transaccion.DoesNotExist:
        error_msg = f"Transacción {transaccion.id} no encontrada"
        print(error_msg)
        return {
            'success': False,
            'payment_intent_id': None,
            'error': error_msg
        }
        
    except stripe.error.CardError as e:
        # Error con la tarjeta (declined, insufficient funds, etc.)
        error_msg = f"Error con la tarjeta: {e.user_message}"
        print(f"CardError en transacción {transaccion.id}: {str(e)}")
        return {
            'success': False,
            'payment_intent_id': None,
            'error': error_msg
        }
        
    except stripe.error.RateLimitError as e:
        error_msg = "Demasiadas solicitudes. Intente nuevamente en unos minutos."
        print(f"RateLimitError en transacción {transaccion.id}: {str(e)}")
        return {
            'success': False,
            'payment_intent_id': None,
            'error': error_msg
        }
        
    except stripe.error.InvalidRequestError as e:
        error_msg = "Parámetros inválidos en la solicitud de pago."
        print(f"InvalidRequestError en transacción {transaccion.id}: {str(e)}")
        return {
            'success': False,
            'payment_intent_id': None,
            'error': error_msg
        }
        
    except stripe.error.AuthenticationError as e:
        error_msg = "Error de autenticación con Stripe."
        print(f"AuthenticationError en transacción {transaccion.id}: {str(e)}")
        return {
            'success': False,
            'payment_intent_id': None,
            'error': error_msg
        }
        
    except stripe.error.APIConnectionError as e:
        error_msg = "Error de conexión con Stripe. Intente nuevamente."
        print(f"APIConnectionError en transacción {transaccion.id}: {str(e)}")
        return {
            'success': False,
            'payment_intent_id': None,
            'error': error_msg
        }
        
    except stripe.error.StripeError as e:
        error_msg = f"Error de Stripe: {str(e)}"
        print(f"StripeError en transacción {transaccion.id}: {str(e)}")
        return {
            'success': False,
            'payment_intent_id': None,
            'error': error_msg
        }
        
    except Exception as e:
        error_msg = f"Error inesperado al procesar el pago: {str(e)}"
        print(f"Error inesperado en transacción {transaccion.id}: {str(e)}")
        return {
            'success': False,
            'payment_intent_id': None,
            'error': error_msg
        }

def generar_token_transaccion(transaccion):
    """
    Genera un token único de seguridad para transacciones específicas.
    
    Se utiliza para transacciones con medios de pago que requieren verificación
    adicional como Efectivo o Transferencia. El token tiene una validez de 5 minutos.
    """
    # Generar token único de 8 caracteres (números y letras mayúsculas)
    import string
    import random
    caracteres = string.ascii_uppercase + string.digits
    
    # Verificar unicidad del token
    token = None
    max_intentos = 100  # Evitar bucle infinito
    intentos = 0
    
    while token is None and intentos < max_intentos:
        token_candidato = ''.join(random.choice(caracteres) for _ in range(8))
        # Verificar si el token ya existe en la base de datos
        if not Transaccion.objects.filter(token=token_candidato).exists():
            token = token_candidato
        intentos += 1
    
    # Si no se pudo generar un token único, usar fallback con timestamp
    if token is None:
        import time
        timestamp_suffix = str(int(time.time()))[-2:]  # Últimos 2 dígitos del timestamp
        token = ''.join(random.choice(caracteres) for _ in range(6)) + timestamp_suffix
    
    # Crear datos del token
    datos_token = {
        'token': token,
        'transaccion_id': transaccion.id
    }
    
    # Actualizar la transacción con el token y su expiración
    transaccion.token = token
    transaccion.fecha_hora = timezone.now()
    transaccion.save()

    return {
        'token': token,
        'datos': datos_token
    }

def enviar_notificacion_cambio_cotizacion(usuario, transaccion, cambios_cotizacion):
    """
    Envía un correo electrónico de notificación cuando se detectan cambios en la cotización
    durante el proceso de confirmación de una transacción.
    
    Args:
        usuario: Usuario que realiza la transacción
        transaccion: Instancia de la transacción afectada
        cambios_cotizacion (dict): Diccionario con información de cambios de cotización
            - 'hay_cambios': boolean indicando si hubo cambios
            - 'valores_anteriores': dict con precios originales
            - 'valores_actuales': dict con precios actuales
            - 'moneda': instancia de la moneda
    
    Returns:
        bool: True si el correo se envió exitosamente, False en caso contrario
    """
    try:
        from django.utils import timezone
        from django.template.loader import render_to_string
        import os
        
        # Verificar que el usuario tenga email
        if not usuario.email:
            print(f"Usuario {usuario.username} no tiene email configurado para notificación de cambio de cotización")
            return False
            
        # Preparar datos para el template del email
        fecha_actual = timezone.now()
        moneda = cambios_cotizacion['moneda']
        valores_anteriores = cambios_cotizacion['valores_anteriores']
        valores_actuales = cambios_cotizacion['valores_actuales']
        
        # Determinar qué precio cambió según el tipo de operación
        if transaccion.tipo == 'compra':
            precio_anterior = valores_anteriores['precio_venta']
            precio_actual = valores_actuales['precio_venta']
            precio_tipo = 'venta'
        else:  # venta
            precio_anterior = valores_anteriores['precio_compra'] 
            precio_actual = valores_actuales['precio_compra']
            precio_tipo = 'compra'
        
        # Calcular la diferencia y porcentaje de cambio
        diferencia = precio_actual - precio_anterior
        porcentaje_cambio = (diferencia / precio_anterior) * 100 if precio_anterior != 0 else 0
        
        # Determinar si el cambio es favorable o desfavorable para el cliente
        if transaccion.tipo == 'compra':
            # Para compras, precio menor es mejor
            cambio_favorable = diferencia < 0
        else:
            # Para ventas, precio mayor es mejor
            cambio_favorable = diferencia > 0
            
        contexto_email = {
            'usuario_nombre': usuario.first_name or usuario.username,
            'cliente_nombre': transaccion.cliente.nombre,
            'transaccion_id': transaccion.id,
            'tipo_operacion': transaccion.tipo,
            'moneda_nombre': moneda.nombre,
            'moneda_simbolo': moneda.simbolo,
            'monto_transaccion': transaccion.monto,
            'precio_anterior': precio_anterior,
            'precio_actual': precio_actual,
            'precio_tipo': precio_tipo,
            'diferencia': abs(diferencia),
            'porcentaje_cambio': abs(porcentaje_cambio),
            'fecha_hora': fecha_actual,
            'medio_pago': transaccion.medio_pago,
            'medio_cobro': transaccion.medio_cobro,
            'precio_final': transaccion.precio_final,
            'empresa': 'Global Exchange'
        }
        
        # Preparar asunto del correo
        direccion_cambio = "bajó" if diferencia < 0 else "subió"
        asunto = f"Cambio de Cotización Detectado - {moneda.nombre} {direccion_cambio} - Transacción #{transaccion.id}"
        
        # Crear contenido del email en texto plano
        mensaje_texto = f"""
Estimado/a {contexto_email['usuario_nombre']},

Se ha detectado un cambio en la cotización durante su proceso de transacción.

DETALLES DE LA TRANSACCIÓN:
================================
Cliente: {contexto_email['cliente_nombre']}
Transacción ID: #{contexto_email['transaccion_id']}
Tipo de Operación: {contexto_email['tipo_operacion'].title()}
Moneda: {contexto_email['moneda_nombre']} ({contexto_email['moneda_simbolo']})
Monto: {contexto_email['monto_transaccion']:,.{moneda.decimales}f} {contexto_email['moneda_simbolo']}

CAMBIO DE COTIZACIÓN:
=====================
Precio de {contexto_email['precio_tipo']} anterior: Gs. {contexto_email['precio_anterior']:,.0f}
Precio de {contexto_email['precio_tipo']} actual: Gs. {contexto_email['precio_actual']:,.0f}
Diferencia: {"+" if diferencia > 0 else ""}{diferencia:,.0f} Gs. ({porcentaje_cambio:+.2f}%)

INFORMACIÓN ADICIONAL:
======================
Medio de Pago: {contexto_email['medio_pago']}
Medio de Cobro: {contexto_email['medio_cobro']}
Monto Final: Gs. {contexto_email['precio_final']:,.0f}
Fecha y Hora: {contexto_email['fecha_hora'].strftime('%d/%m/%Y %H:%M:%S')}

Este cambio se detectó mientras usted se encontraba en la página de confirmación de la transacción.
Puede continuar con la transacción aceptando el nuevo precio o cancelar la operación.

---
{contexto_email['empresa']}
Sistema Automatizado de Notificaciones
"""

        # Crear y enviar el email
        email = EmailMessage(
            subject=asunto,
            body=mensaje_texto,
            from_email=os.environ.get('EMAIL_HOST_USER'),
            to=[usuario.email],
        )
        
        email.send()
        print(f"Notificación de cambio de cotización enviada exitosamente a {usuario.email} para transacción #{transaccion.id}")
        return True
        
    except Exception as e:
        print(f"Error al enviar notificación de cambio de cotización: {str(e)}")
        return False

def verificar_cambio_cotizacion_sesion(request, tipo_transaccion='compra'):
    """
    Verifica si ha habido cambios en la cotización durante el proceso de transacción.
    
    Compara los precios almacenados en la sesión al iniciar la transacción con los precios actuales.
    Si detecta cambios, también envía una notificación por correo electrónico al usuario.
    
    Args:
        request (HttpRequest): Petición HTTP con datos de sesión
        tipo_transaccion (str): 'compra' o 'venta'
        
    Returns:
        dict: Diccionario con información de cambios o None si no hay cambios
            - 'hay_cambios': boolean indicando si hubo cambios
            - 'valores_anteriores': dict con precio_compra y precio_venta originales
            - 'valores_actuales': dict con precio_compra y precio_venta actuales
            - 'moneda': instancia de la moneda
            - 'email_enviado': boolean indicando si se envió notificación por email
    """
    try:
        # Obtener datos de la sesión
        datos_key = f'{tipo_transaccion}_datos'
        precio_compra_key = 'precio_compra_inicial'
        precio_venta_key = 'precio_venta_inicial'
        
        datos_transaccion = request.session.get(datos_key)
        precio_compra_inicial = request.session.get(precio_compra_key)
        precio_venta_inicial = request.session.get(precio_venta_key)
        if not datos_transaccion or (precio_compra_inicial is None and precio_venta_inicial is None):
            return None
            
        # Obtener moneda actual
        moneda = Moneda.objects.get(id=datos_transaccion['moneda'])
        cliente_activo = request.user.cliente_activo
        
        # Calcular precios actuales
        precios_actuales = moneda.get_precios_cliente(cliente_activo)
        precio_compra_actual = precios_actuales['precio_compra']
        precio_venta_actual = precios_actuales['precio_venta']

        # Verificar si hay cambios
        hay_cambios = (
            precio_compra_actual != precio_compra_inicial and 
            precio_venta_actual != precio_venta_inicial
        )
        if hay_cambios:
            cambios_info = {
                'hay_cambios': True,
                'valores_anteriores': {
                    'precio_compra': precio_compra_inicial,
                    'precio_venta': precio_venta_inicial
                },
                'valores_actuales': {
                    'precio_compra': precio_compra_actual,
                    'precio_venta': precio_venta_actual
                },
                'moneda': moneda,
                'email_enviado': False
            }
            
            return cambios_info
        
        return {'hay_cambios': False}
        
    except Exception:
        return None
    
@transaction.atomic
def procesar_transaccion(transaccion, recibido=0):
    
    if transaccion.medio_pago == 'Transferencia Bancaria':
        transaccion.pagado = recibido
        if recibido < transaccion.precio_final:
            print('Notificar usuario que transferencia es incompleta')
        else:
            transaccion.estado = 'Confirmada'
            transaccion.fecha_hora = timezone.now()
            generar_factura_electronica(transaccion)
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
        transaccion.pagado = recibido
        if recibido < transaccion.precio_final:
            print('Notificar usuario que transferencia es incompleta')
        else:
            transaccion.estado = 'Confirmada'
            generar_factura_electronica(transaccion)
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
            transaccion.pagado = transaccion.precio_final
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
            transaccion.pagado = transaccion.precio_final
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
                transaccion.estado = 'Completa'
                transaccion.fecha_hora = timezone.now()
                transaccion.save()
        generar_factura_electronica(transaccion)

def no_redondeado(monto, denominaciones, cantidades=None):
    """
    Verifica si el monto puede ser formado exactamente con las denominaciones disponibles.
    
    Esta función utiliza el algoritmo de Frobenius optimizado y teoría de números
    para determinar eficientemente si es posible formar el monto exacto usando 
    una combinación de las denominaciones disponibles.
    Por ejemplo, 707000 puede formarse con 141 billetes de 5000 y 1 billete de 2000.
    
    Args:
        monto (int o Decimal): Monto a verificar
        denominaciones (list): Lista de denominaciones disponibles (enteros)
        cantidades (dict, opcional): Diccionario con cantidades disponibles por denominación.
                                    Si no se proporciona, se asume cantidad ilimitada.
        
    Returns:
        int: 0 si el monto se puede formar exactamente, o el menor redondeo necesario hacia arriba
    """
    from math import gcd
    from functools import reduce
    
    monto = int(monto)  # Convertir a entero si viene como Decimal
    
    # Ordenar denominaciones de menor a mayor
    denominaciones_ordenadas = sorted(denominaciones)
    
    # Calcular el MCD (máximo común divisor) de todas las denominaciones
    mcd = reduce(gcd, denominaciones_ordenadas)
    
    # Si el monto no es múltiplo del MCD, nunca se podrá formar
    if monto % mcd != 0:
        # Buscar el menor redondeo que sea múltiplo del MCD
        redondeo = mcd - (monto % mcd)
        return redondeo
    
    # Si solo tenemos cantidades ilimitadas y el monto es múltiplo del MCD,
    # siempre se puede formar (por el teorema de Frobenius para denominaciones con gcd=1,
    # o su generalización cuando gcd>1)
    if cantidades is None:
        # Para dos denominaciones, podemos usar el número de Frobenius
        if len(denominaciones_ordenadas) == 2:
            a, b = denominaciones_ordenadas
            if gcd(a, b) == 1:
                # Número de Frobenius: g(a,b) = ab - a - b
                frobenius = a * b - a - b
                if monto > frobenius:
                    return 0  # Todos los números mayores que Frobenius son alcanzables
        
        # Para el caso general con cantidades ilimitadas, verificamos con DP optimizado
        # Solo hasta el menor valor que garantiza alcanzabilidad
        menor = denominaciones_ordenadas[0]
        limite = menor * denominaciones_ordenadas[-1]
        
        if monto <= limite:
            # DP optimizado: solo guardamos si es posible alcanzar cada valor
            dp = [False] * (monto + 1)
            dp[0] = True
            
            for i in range(1, monto + 1):
                for denom in denominaciones_ordenadas:
                    if i >= denom and dp[i - denom]:
                        dp[i] = True
                        break
            
            if dp[monto]:
                return 0
        else:
            # Para montos muy grandes, asumimos que se puede formar
            return 0
    else:
        # Con cantidades limitadas, usamos DP con backtracking limitado
        # Optimización: usar BFS en lugar de DP completo
        from collections import deque
        
        visitados = {0}
        cola = deque([(0, cantidades.copy())])
        
        # Límite de iteraciones para evitar bucles infinitos
        max_iteraciones = min(10000, monto // min(denominaciones_ordenadas) + 1000)
        iteraciones = 0
        
        while cola and iteraciones < max_iteraciones:
            iteraciones += 1
            valor_actual, cant_restantes = cola.popleft()
            
            if valor_actual == monto:
                return 0
            
            # Probar agregar cada denominación
            for denom in denominaciones_ordenadas:
                if cant_restantes[denom] > 0:
                    nuevo_valor = valor_actual + denom
                    
                    # Solo continuar si no nos pasamos y no lo visitamos
                    if nuevo_valor <= monto and nuevo_valor not in visitados:
                        visitados.add(nuevo_valor)
                        nuevas_cantidades = cant_restantes.copy()
                        nuevas_cantidades[denom] -= 1
                        cola.append((nuevo_valor, nuevas_cantidades))
    
    # Si no se puede formar, buscar el menor redondeo
    menor_denominacion = min(denominaciones_ordenadas)
    
    # Buscar el siguiente múltiplo del MCD que sea alcanzable
    for incremento in range(mcd, mcd * menor_denominacion + 1, mcd):
        monto_redondeado = monto + incremento
        
        # Verificación rápida recursiva con límite
        if incremento <= menor_denominacion * 2:
            resultado = no_redondeado(monto_redondeado, denominaciones, cantidades)
            if resultado == 0:
                return incremento
    
    # Fallback: retornar el MCD como redondeo mínimo
    return mcd

def generar_factura_electronica(transaccion):
    """
    Genera una factura electrónica para una transacción completada.
    
    Args:
        transaccion (Transaccion): Instancia de transacción para la cual generar factura
        
    Returns:
        dict: Diccionario con información de la factura generada
            - 'success': bool indicando si se generó correctamente
            - 'numero_factura': str con el número de factura
            - 'cdc': str con el Código de Control (CDC)
            - 'xml': str con el XML de la factura
            - 'pdf_url': str con la URL del PDF
            - 'error': str con mensaje de error (si aplica)
    """
    
    for numero in range(settings.NUMERO_FACTURACION, 400):
        if not Transaccion.objects.filter(numero_factura=numero).exists():
            transaccion.numero_factura = numero
            transaccion.save()
            break
    # Preparar datos de la factura
    url = f"{settings.FACTURA_SEGURA_API_URL}/misife00/v1/esi"
    
    headers = {
        'accept': 'application/json',
        'Authentication-Token': os.environ.get('AUTHENTICATION_TOKEN'),
        'Content-Type': 'application/json'
    }

    monto_formateado = f"{transaccion.monto:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    # Construir params según especificación de la API
    params = {
        'iTipEmi': '1', #Tipo de emisión
        'iTiDE': '1',
        'dNumTim': '02595733',
        'dFeIniT': '2025-03-27',
        'dEst': '001',
        'dPunExp': '003',
        'dNumDoc': f'0000{transaccion.numero_factura}',
        'dFeEmiDE': timezone.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'iTipTra': '5' if transaccion.tipo == 'venta' else '6',
        'iTImp': '1',
        'cMoneOpe': 'PYG',
        'dCondTiCam': '1',
        'dRucEm': '2595733',
        'dDVEmi': '3',
        'iTipCont': '2',
        'dNomEmi': 'Global Exchange',
        'dDirEmi': 'Asunción, Paraguay',
        'dNumCas': '123',
        'cDepEmi': '1',
        'dDesDepEmi': 'CAPITAL',
        'cCiuEmi': '1',
        'dDesCiuEmi': 'ASUNCION (DISTRITO)',
        'dTelEmi': '0981000001',
        'dEmailE': os.environ.get('EMAIL_HOST_USER'),
        'iIndPres': '1',
        'gActEco': [
            {
                "cActEco": "62010",
                "dDesActEco": "Actividades de programación informática"
            }
        ],
        'cPaisRec': 'PRY',
        **(
            {
                'dRucRec': transaccion.cliente.numero_documento[:-1],
                'dDVRec': transaccion.cliente.numero_documento[-1],
                'iTiContRec': '1' if transaccion.cliente.tipo == 'F' else '2'
            } if transaccion.cliente.tipo_documento == 'RUC' else {
                'iTipIDRec': '1',
                'dDTipIDRec': 'Cédula paraguaya',
                'dNumIDRec': transaccion.cliente.numero_documento
            }
        ),
        'dNomRec': transaccion.cliente.nombre,
        'dCelRec': transaccion.cliente.telefono,
        'dEmailRec': transaccion.cliente.correo_electronico,
        'iNatRec': '1' if transaccion.cliente.tipo_documento == 'RUC' else '2',
        'iTiOpe': '2',
        'iCondOpe': '1',
        'gPaConEIni': [
            {
                'iTiPago': '1',
                'dMonTiPag': str(transaccion.precio_final),
                'cMoneTiPag': 'PYG'
            }
        ],
        'gCamItem': [
            {
                'dCodInt': '1',
                'dDesProSer': f'Operación de {transaccion.tipo} de {monto_formateado} {transaccion.moneda.simbolo} ({transaccion.moneda.nombre})',
                'cUniMed': '77',
                'dCantProSer': '1',
                'dPUniProSer': str(transaccion.precio_final),
                'dTotBruOpeItem': str(transaccion.precio_final),
                'dDescItem': '0',
                'dDescGloItem': '0',
                "iAfecIVA": "3",
                'dAntPreUniIt': '0',
                'dAntGloPreUniIt': '0',
                'dPropIVA': "0",
                'dTasaIVA': "0"
            }
        ],
        'dTotGralOpe': str(transaccion.precio_final),
        'CDC': '0',
        'dCodSeg': '0',
        'dDVId': '0',
        'dSisFact': '1'
    }
    # Payload completo con estructura operation y params
    payload = {
        "operation": "calcular_de",
        "params": {
            "DE": params
        }
    }
    # Realizar petición a la API
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    # Convertir la respuesta a diccionario
    response_data = response.json()
    print("Respuesta de calcular_de:")
    print(response_data)

    # Extraer el campo 'results'
    results = response_data.get('results')

    # Si 'results' es una lista, tomar el primer elemento
    if isinstance(results, list) and len(results) > 0:
        de_data = results[0].get('DE', {})
    elif isinstance(results, dict):
        de_data = results.get('DE', {})
    else:
        de_data = {}
    
    payload = {
        "operation": "generar_de",
        "params": {
            "DE": de_data
        }
    }
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    response_data = response.json()
    print("Respuesta de generar_de:")
    print(response_data)
    if response_data.get('description') == 'OK':
        # Extraer el campo 'results'
        results = response_data.get('results')

        # Si 'results' es una lista, tomar el primer elemento
        if isinstance(results, list) and len(results) > 0:
            cdc_data = results[0].get('CDC', {})
        elif isinstance(results, dict):
            cdc_data = results.get('CDC', {})
        else:
            cdc_data = {}
        transaccion.factura = cdc_data
        transaccion.save()
        print(f"Factura electrónica generada exitosamente")
        
        # Enviar factura por correo electrónico
        try:
            # Descargar el PDF de la factura
            resultado_descarga = descargar_factura(cdc_data)
            
            if resultado_descarga.get('success'):
                # Preparar el correo electrónico
                asunto = f'Factura Electrónica - Global Exchange'
                mensaje = f"""
Estimado/a {transaccion.cliente.nombre},

Adjuntamos la factura electrónica correspondiente a su transacción de {transaccion.tipo} realizada el {transaccion.fecha_hora.strftime('%d/%m/%Y %H:%M')}.

Detalles de la transacción:
- Tipo: {transaccion.tipo.title()}
- Moneda: {transaccion.moneda.nombre} ({transaccion.moneda.simbolo})
- Monto: {monto_formateado} {transaccion.moneda.simbolo}
- Total: {transaccion.precio_final} Gs.
- CDC: {cdc_data}

Gracias por confiar en Global Exchange.

Saludos cordiales,
Global Exchange
"""
                
                # Crear el correo electrónico
                email = EmailMessage(
                    subject=asunto,
                    body=mensaje,
                    from_email=settings.EMAIL_HOST_USER,
                    to=[transaccion.usuario.email]
                )
                
                # Adjuntar el PDF
                email.attach(
                    resultado_descarga['filename'],
                    resultado_descarga['content'],
                    resultado_descarga['content_type']
                )
                
                # Enviar el correo
                email.send(fail_silently=False)
                print(f"Factura enviada por correo a {transaccion.usuario.email}")
            else:
                print(f"Error al descargar la factura: {resultado_descarga.get('error')}")
                
        except Exception as e:
            print(f"Error al enviar factura por correo: {str(e)}")
    
    return response_data

def verificar_factura(CDC):
    """
    Verifica el estado de una factura electrónica mediante su CDC.
    
    Args:
        CDC (str): Código de Control de la factura
        dRucEm (str): RUC del emisor de la factura
        
    Returns:
        dict: Diccionario con información de la factura verificada
            - 'success': bool indicando si la verificación fue exitosa
            - 'factura': dict con detalles de la factura
            - 'error': str con mensaje de error (si aplica)
    """
    url = f"{settings.FACTURA_SEGURA_API_URL}/misife00/v1/esi"
    
    headers = {
        'accept': 'application/json',
        'Authentication-Token': os.environ.get('AUTHENTICATION_TOKEN'),
        'Content-Type': 'application/json'
    }
    
    payload = {
        "operation": "get_estado_sifen",
        "params": {
            "CDC": CDC,
            "dRucEm": '2595733'
        }
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    response_data = response.json()
    print(response_data)
    
    return response_data

def descargar_factura(CDC):
    """
    Descarga el XML y PDF de una factura electrónica mediante su CDC.
    
    Args:
        CDC (str): Código de Control de la factura
        dRucEm (str): RUC del emisor de la factura
        
    Returns:
        dict: Diccionario con el contenido del PDF para descarga
            - 'success': bool indicando si la descarga fue exitosa
            - 'content': bytes con el contenido del PDF
            - 'filename': str con el nombre sugerido para el archivo
            - 'content_type': str con el tipo MIME del archivo
            - 'error': str con mensaje de error (si aplica)
    """
    url = f"{settings.FACTURA_SEGURA_API_URL}/misife00/v1/esi/dwn_kude/2595733/{CDC}"
    
    headers = {
        'Authentication-Token': os.environ.get('AUTHENTICATION_TOKEN')
    }
    
    response = requests.get(url, headers=headers, timeout=30, stream=True)
    response.raise_for_status()
    
    # Obtener el contenido completo del PDF
    pdf_content = b''
    for chunk in response.iter_content(chunk_size=8192):
        pdf_content += chunk
    
    # Nombre del archivo basado en el CDC
    filename = f"factura_{CDC}.pdf"
    
    print(f"PDF descargado exitosamente: {filename}")
    return {
        'success': True, 
        'content': pdf_content,
        'filename': filename,
        'content_type': 'application/pdf'
    }