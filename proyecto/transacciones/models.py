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
import socket
import requests
from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone
import stripe
from monedas.models import Moneda, StockGuaranies, Denominacion
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

class Tauser(models.Model):
    puerto = models.SmallIntegerField(unique=True)
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
    token = models.CharField(max_length=8, blank=True, null=True, unique=True)  
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

def calcular_conversion(monto, moneda, operacion, pago='Efectivo', cobro='Efectivo', segmentacion='minorista'):
    """
    Returns:
        monto_original (Decimal): Monto de la divisa que el cliente ingresó inicialmente en el formulario de operaciones
        redondeo_efectivo_monto (Decimal): Monto de redondeo aplicado si la divisa será pagada o cobrada en efectivo
        redondeo_efectivo_precio_final (int): Monto de redondeo aplicado si el monto en guaraníes final será pagado o cobrado en efectivo
        cotizacion (int): Cotización de la moneda según el tipo de operación
        precio_base (int): Monto en guaraníes sin considerar recargos o beneficios por segmento
        porc_beneficio_segmento (str): Porcentaje de beneficio aplicado según el segmento del cliente
        beneficio_segmento (int): Beneficio aplicado en la operación según el segmento del cliente
        monto_recargo_pago (int): Monto del recargo aplicado según el medio de pago
        porc_recargo_pago (str): Porcentaje del recargo aplicado según el medio de pago
        monto_recargo_cobro (int): Monto del recargo aplicado según el medio de cobro
        porc_recargo_cobro (str): Porcentaje del recargo aplicado según el medio
        monto (Decimal): Monto de la divisa después de aplicar redondeos si corresponde
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
    # Se guarda el monto original
    monto_original = monto
    # Calculos para compra
    if operacion == 'compra':
        # La compra siempre tendrá como medio de cobro efectivo, por lo que se debe redondear el monto hacia arriba
        redondeo_efectivo_monto = redondear_efectivo(monto, Denominacion.objects.filter(moneda=moneda).values_list('valor', flat=True))
        monto += redondeo_efectivo_monto
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
            monto_recargo_pago =  Decimal(precio_final) * (Decimal(Recargos.objects.get(marca=dict_pago['brand']).recargo) / Decimal(100))
            porc_recargo_pago = Recargos.objects.get(marca=dict_pago['brand']).recargo
        # Si el pago es con billetera electrónica
        elif dict_pago in Recargos.objects.filter(medio='Billetera Electrónica').values_list('marca', flat=True):
            monto_recargo_pago =  Decimal(precio_final) * (Decimal(Recargos.objects.get(marca=dict_pago).recargo) / Decimal(100))
            porc_recargo_pago = Recargos.objects.get(marca=dict_pago).recargo
        # Si el pago es en efectivo, cheque o transferencia, no hay recargo
        else:
            monto_recargo_pago = 0
            porc_recargo_pago = 0
        # Calculo del monto en guaraníes a pagar con recargos
        precio_final += monto_recargo_pago
        # Si el pago es en efectivo, se redondea el monto a pagar hacia abajo
        if dict_pago == 'Efectivo':
            redondeo_efectivo_precio_final = redondear_efectivo(precio_final, Denominacion.objects.filter(moneda=None).values_list('valor', flat=True))
            precio_final += redondeo_efectivo_precio_final
        else:
            redondeo_efectivo_precio_final = 0
        # No hay recargo por medio de cobro ya que siempre es en efectivo
        monto_recargo_cobro = 0
        porc_recargo_cobro = 0
    # Calculos para venta
    else:
        # Calculo de redondeo si el pago es en efectivo, sino no hay redondeo
        if dict_pago == 'Efectivo':
            redondeo_efectivo_monto = redondear_efectivo(monto, Denominacion.objects.filter(moneda=None).values_list('valor', flat=True))
            monto += redondeo_efectivo_monto
        else:
            redondeo_efectivo_monto = 0
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
            monto_recargo_pago =  Decimal(precio_final) * (Decimal(Recargos.objects.get(marca=dict_pago['brand']).recargo) / Decimal(100))
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
        # Si el cobro es en efectivo, se redondea el monto a cobrar hacia abajo
        if dict_cobro == 'Efectivo':
            redondeo_efectivo_precio_final = redondear_efectivo(precio_final, Denominacion.objects.filter(moneda=moneda).values_list('valor', flat=True))
            precio_final += redondeo_efectivo_precio_final
        else:
            redondeo_efectivo_precio_final = 0
            
    return {
        'cotizacion': int(cotizacion),
        'precio_base': int(precio_base),
        'beneficio_segmento': int(beneficio_segmento),
        'porc_beneficio_segmento': f'{porc_beneficio_segmento}%',
        'redondeo_efectivo_monto': redondeo_efectivo_monto,
        'redondeo_efectivo_precio_final': int(redondeo_efectivo_precio_final),
        'monto_recargo_pago': int(monto_recargo_pago),
        'porc_recargo_pago': f'{porc_recargo_pago}%',
        'monto_recargo_cobro': int(monto_recargo_cobro),
        'porc_recargo_cobro': f'{porc_recargo_cobro}%',
        'monto_original': monto_original,
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
    adicional como Efectivo o Cheque. El token tiene una validez de 5 minutos.
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
    transaccion.save()

    return {
        'token': token,
        'datos': datos_token
    }

def verificar_cambio_cotizacion_sesion(request, tipo_transaccion='compra'):
    """
    Verifica si ha habido cambios en la cotización durante el proceso de transacción.
    
    Compara los precios almacenados en la sesión al iniciar la transacción con los precios actuales.
    
    Args:
        request (HttpRequest): Petición HTTP con datos de sesión
        tipo_transaccion (str): 'compra' o 'venta'
        
    Returns:
        dict: Diccionario con información de cambios o None si no hay cambios
            - 'hay_cambios': boolean indicando si hubo cambios
            - 'valores_anteriores': dict con precio_compra y precio_venta originales
            - 'valores_actuales': dict con precio_compra y precio_venta actuales
            - 'moneda': instancia de la moneda
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
            return {
                'hay_cambios': True,
                'valores_anteriores': {
                    'precio_compra': precio_compra_inicial,
                    'precio_venta': precio_venta_inicial
                },
                'valores_actuales': {
                    'precio_compra': precio_compra_actual,
                    'precio_venta': precio_venta_actual
                },
                'moneda': moneda
            }
        
        return {'hay_cambios': False}
        
    except Exception:
        return None
    
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

def redondear_efectivo(monto, denominaciones):
    """
    Redondea un monto al múltiplo más cercano según las denominaciones disponibles.
    
    Args:
        monto (Decimal): Monto a redondear
        denominaciones (list): Lista de denominaciones disponibles (enteros)
        
    Returns:
        Decimal: Monto redondeado
    """
    redondeo = denominaciones[0]
    for i in denominaciones:
        if monto % i == 0:
            redondeo = 0
            break
        elif i - (monto % i) < redondeo:
            redondeo = i - (monto % i)
    return redondeo
