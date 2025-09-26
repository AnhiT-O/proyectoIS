"""
Vistas para el sistema de transacciones de Global Exchange.

Este módulo contiene todas las vistas necesarias para el procesamiento de transacciones
de compra y venta de monedas extranjeras, incluyendo la gestión del flujo completo
desde la selección inicial hasta la confirmación final.

Funcionalidades principales:
    - Proceso completo de compra de monedas (4 pasos)
    - Proceso completo de venta de monedas (4 pasos)
    - Gestión de recargos por medio de pago
    - Historial y consulta de transacciones
    - Validaciones de límites en tiempo real
    - Generación y gestión de tokens de seguridad

Author: Equipo de desarrollo Global Exchange
Date: 2024
"""

import logging
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from monedas.models import Moneda
from monedas.services import LimiteService
from .forms import SeleccionMonedaMontoForm, RecargoForm
from .models import Transaccion, Recargos
from decimal import Decimal
from clientes.models import Cliente
import secrets
import json
import base64
import ast
from datetime import datetime, timedelta
from django.db import models
import stripe

# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

def realizar_conversion(transaccion_id):
    precios = Moneda.objects.get(id=transaccion_id.moneda_id).get_precios_cliente(Cliente.objects.get(id=transaccion_id.cliente_id))
    if transaccion_id.tipo == 'compra':
        resultado = transaccion_id.monto * precios['precio_venta']
    else:
        resultado = transaccion_id.monto * precios['precio_compra']
    return resultado

def convertir(monto, cliente, moneda, tipo, medio_pago, medio_cobro):
    precios = moneda.get_precios_cliente(cliente)
    if tipo == 'compra':
        if medio_pago in ['Efectivo', 'Cheque']:
            resultado = monto * precios['precio_venta']
        elif Recargos.objects.filter(nombre=medio_pago).exists():
            resultado = monto * precios['precio_venta']
            recargo = Recargos.objects.get(nombre=medio_pago).recargo
            resultado *= (Decimal('1') + (Decimal(str(recargo)) / Decimal('100')))
        else:
            resultado = monto * precios['precio_venta']
            recargo = Recargos.objects.get(nombre='Tarjeta de Crédito').recargo
            resultado *= (Decimal('1') + (Decimal(str(recargo)) / Decimal('100')))
    else:
        if medio_pago == 'Efectivo':
            resultado = monto * precios['precio_compra']
        else:
            resultado = monto * precios['precio_compra']
            recargo = Recargos.objects.get(nombre='Tarjeta de Crédito').recargo
            resultado *= (Decimal('1') - (Decimal(str(recargo)) / Decimal('100')))
        if Recargos.objects.filter(nombre=medio_cobro).exists():
            recargo = Recargos.objects.get(nombre=medio_cobro).recargo
            resultado *= (Decimal('1') - (Decimal(str(recargo)) / Decimal('100')))
    return int(resultado)

def procesar_pago_stripe(transaccion_id, payment_method_id):
    """
    Procesa un pago con Stripe para una transacción dada.
    
    Args:
        transaccion_id (int): ID de la transacción para la cual generar el token
    
    Returns:
        dict: Diccionario con 'token' (str) y 'datos' (dict) de la transacción
        
    Raises:
        ValueError: Si la transacción no existe
    """
    try:
        # Obtener la transacción
        transaccion = Transaccion.objects.get(id=transaccion_id)
        if transaccion.tipo == 'venta':
            monto_recargado = transaccion.monto * (Decimal('1') + (Decimal(str(Recargos.objects.get(nombre='Tarjeta de Crédito').recargo)) / Decimal('100')))
            monto_centavos = int(monto_recargado * 100)
            moneda_stripe = 'usd'  # Cambiar según la moneda
        else:
            a_guaranies = realizar_conversion(transaccion)
            monto_recargado = a_guaranies * (Decimal('1') + (Decimal(str(Recargos.objects.get(nombre='Tarjeta de Crédito').recargo)) / Decimal('100')))
            moneda_stripe = 'pyg'  # Cambiar según la moneda
            monto_centavos = int(monto_recargado)
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
                'transaccion_id': str(transaccion_id),
                'tipo': transaccion.tipo,
                'cliente_id': str(transaccion.cliente.id)
            }
        )

        consumo = LimiteService.obtener_o_crear_consumo(transaccion.cliente_id)
        consumo.consumo_diario += realizar_conversion(transaccion)
        consumo.consumo_mensual += realizar_conversion(transaccion)
        consumo.save()
        
        logger.info(f"Pago Stripe procesado exitosamente para transacción {transaccion_id}. PaymentIntent: {payment_intent.id}")
        
        return {
            'success': True,
            'payment_intent_id': payment_intent.id,
            'status': payment_intent.status,
            'error': None
        }
        
    except Transaccion.DoesNotExist:
        error_msg = f"Transacción {transaccion_id} no encontrada"
        logger.error(error_msg)
        return {
            'success': False,
            'payment_intent_id': None,
            'error': error_msg
        }
        
    except stripe.error.CardError as e:
        # Error con la tarjeta (declined, insufficient funds, etc.)
        error_msg = f"Error con la tarjeta: {e.user_message}"
        logger.error(f"CardError en transacción {transaccion_id}: {str(e)}")
        return {
            'success': False,
            'payment_intent_id': None,
            'error': error_msg
        }
        
    except stripe.error.RateLimitError as e:
        error_msg = "Demasiadas solicitudes. Intente nuevamente en unos minutos."
        logger.error(f"RateLimitError en transacción {transaccion_id}: {str(e)}")
        return {
            'success': False,
            'payment_intent_id': None,
            'error': error_msg
        }
        
    except stripe.error.InvalidRequestError as e:
        error_msg = "Parámetros inválidos en la solicitud de pago."
        logger.error(f"InvalidRequestError en transacción {transaccion_id}: {str(e)}")
        return {
            'success': False,
            'payment_intent_id': None,
            'error': error_msg
        }
        
    except stripe.error.AuthenticationError as e:
        error_msg = "Error de autenticación con Stripe."
        logger.error(f"AuthenticationError en transacción {transaccion_id}: {str(e)}")
        return {
            'success': False,
            'payment_intent_id': None,
            'error': error_msg
        }
        
    except stripe.error.APIConnectionError as e:
        error_msg = "Error de conexión con Stripe. Intente nuevamente."
        logger.error(f"APIConnectionError en transacción {transaccion_id}: {str(e)}")
        return {
            'success': False,
            'payment_intent_id': None,
            'error': error_msg
        }
        
    except stripe.error.StripeError as e:
        error_msg = f"Error de Stripe: {str(e)}"
        logger.error(f"StripeError en transacción {transaccion_id}: {str(e)}")
        return {
            'success': False,
            'payment_intent_id': None,
            'error': error_msg
        }
        
    except Exception as e:
        error_msg = f"Error inesperado al procesar el pago: {str(e)}"
        logger.error(f"Error inesperado en transacción {transaccion_id}: {str(e)}")
        return {
            'success': False,
            'payment_intent_id': None,
            'error': error_msg
        }

def generar_token_transaccion(transaccion_id):
    """
    Genera un token único de seguridad para transacciones específicas.
    
    Se utiliza para transacciones con medios de pago que requieren verificación
    adicional como Efectivo o Cheque. El token tiene una validez de 5 minutos.
    """
    # Generar token único
    token = secrets.token_urlsafe(32)
    
    # Obtener la transacción
    try:
        transaccion = Transaccion.objects.get(id=transaccion_id)
    except Transaccion.DoesNotExist:
        raise ValueError("Transacción no encontrada")
    
    # Crear datos del token
    datos_token = {
        'token': token,
        'transaccion_id': transaccion_id
    }
    
    # Actualizar la transacción con el token y su expiración
    transaccion.establecer_token_con_expiracion(token)
    
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
        
        if not datos_transaccion or precio_compra_inicial is None or precio_venta_inicial is None:
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
            precio_compra_actual != precio_compra_inicial or 
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

def extraer_mensaje_error(validation_error):
    """
    Extrae el mensaje de error limpio de un ValidationError de Django.
    
    Django a veces agrega corchetes y formateo adicional a los mensajes de error.
    Esta función extrae el mensaje principal sin el formateo extra.
    
    Args:
        validation_error (ValidationError): Error de validación de Django
        
    Returns:
        str: Mensaje de error limpio sin formateo adicional
    """
    if hasattr(validation_error, 'message'):
        return validation_error.message
    elif hasattr(validation_error, 'messages') and validation_error.messages:
        # Si hay múltiples mensajes, tomar el primero
        return validation_error.messages[0]
    else:
        # Fallback a conversión string
        mensaje = str(validation_error)
        # Remover corchetes si están presentes
        if mensaje.startswith("['") and mensaje.endswith("']"):
            return mensaje[2:-2]
        return mensaje

def obtener_contexto_limites(cliente):
    """
    Obtiene información completa de límites de transacción para un cliente.
    
    Consulta el servicio de límites para obtener información detallada sobre
    los límites diarios y mensuales del cliente, incluyendo consumo actual
    y porcentajes de uso.
    
    Args:
        cliente (Cliente): Instancia del cliente para consultar límites
        
    Returns:
        dict: Diccionario con información de límites o diccionario vacío si hay error
            - limites_disponibles: Información detallada de límites
            - limite_diario_total: Límite diario configurado
            - limite_mensual_total: Límite mensual configurado
            - consumo_diario: Consumo actual del día
            - consumo_mensual: Consumo actual del mes
            - porcentaje_uso_diario: Porcentaje usado del límite diario
            - porcentaje_uso_mensual: Porcentaje usado del límite mensual
    """
    try:
        limites_info = LimiteService.obtener_limites_disponibles(cliente)
        if 'error' not in limites_info:
            return {
                'limites_disponibles': {
                    'diario': limites_info['disponible_diario'],
                    'mensual': limites_info['disponible_mensual'],
                    'limite_diario_total': limites_info['limite_diario'],
                    'limite_mensual_total': limites_info['limite_mensual'],
                    'consumo_diario': limites_info['consumo_diario'],
                    'consumo_mensual': limites_info['consumo_mensual'],
                    'porcentaje_uso_diario': limites_info['porcentaje_uso_diario'],
                    'porcentaje_uso_mensual': limites_info['porcentaje_uso_mensual']
                }
            }
    except Exception:
        pass
    return {}

# ============================================================================
# PROCESO DE COMPRA DE MONEDAS
# ============================================================================

@login_required
def compra_monto_moneda(request):
    """
    Primer paso del proceso de compra: selección de moneda y monto.
    
    Permite al usuario seleccionar la moneda extranjera que desea comprar
    y especificar el monto. Incluye validaciones de límites de transacción
    antes de proceder al siguiente paso.
    
    Validaciones realizadas:
        - Usuario debe tener un cliente activo
        - Monto debe cumplir con límites diarios y mensuales
        - Moneda debe estar activa en el sistema
    
    Args:
        request (HttpRequest): Petición HTTP con datos del formulario
        
    Returns:
        HttpResponse: Renderiza formulario o redirecciona al siguiente paso
        
    Template:
        transacciones/seleccion_moneda_monto.html
        
    Context:
        - form: Formulario de selección de moneda y monto
        - paso_actual: Número del paso actual (1)
        - total_pasos: Total de pasos en el proceso (4)
        - titulo_paso: Título descriptivo del paso
        - tipo_transaccion: Tipo de operación ('compra')
        - limites_disponibles: Información de límites del cliente
    """
    if request.method == 'POST':
        form = SeleccionMonedaMontoForm(request.POST)
        if form.is_valid():
            moneda = form.cleaned_data['moneda']
            monto = form.cleaned_data['monto_decimal']
            
            # Verificar límites de transacción para compras
            try:
                cliente_activo = request.user.cliente_activo
                
                # Convertir el monto a guaraníes para verificar límites
                monto_guaranies = LimiteService.convertir_a_guaranies(
                    int(monto), moneda, 'COMPRA', cliente_activo
                )
                
                # Validar que no supere los límites (sin actualizar consumo aún)
                LimiteService.validar_limite_transaccion(cliente_activo, monto_guaranies)
                
            except ValidationError as e:
                # Si hay error de límites, mostrar mensaje y no proceder
                messages.error(request, extraer_mensaje_error(e))
                context = {
                    'form': form,
                    'paso_actual': 1,
                    'total_pasos': 4,
                    'titulo_paso': 'Selección de Moneda y Monto',
                    'tipo_transaccion': 'compra'
                }
                # Agregar información de límites al contexto de error
                context.update(obtener_contexto_limites(cliente_activo))
                return render(request, 'transacciones/seleccion_moneda_monto.html', context)
            except Exception as e:
                # Error general del sistema de límites
                messages.error(request, 'Error al verificar límites de transacción. Inténtelo nuevamente.')
                context = {
                    'form': form,
                    'paso_actual': 1,
                    'total_pasos': 4,
                    'titulo_paso': 'Selección de Moneda y Monto',
                    'tipo_transaccion': 'compra'
                }
                # Agregar información de límites al contexto de error
                context.update(obtener_contexto_limites(cliente_activo))
                return render(request, 'transacciones/seleccion_moneda_monto.html', context)
            
            # Si pasa las validaciones, guardar los datos en la sesión
            request.session['compra_datos'] = {
                'moneda': moneda.id,
                'monto': str(monto),  # Convertir Decimal a string para serialización
                'paso_actual': 2
            }
            # Guardar precios iniciales en la sesión
            precios_iniciales = moneda.get_precios_cliente(request.user.cliente_activo)
            request.session['precio_compra_inicial'] = precios_iniciales['precio_compra']
            request.session['precio_venta_inicial'] = precios_iniciales['precio_venta']
            
            # Redireccionar al siguiente paso sin parámetros en la URL
            return redirect('transacciones:compra_medio_pago')
    else:
        # Verificar si el usuario tiene un cliente activo
        if not request.user.cliente_activo:
            messages.error(request, 'Debes tener un cliente activo para realizar compras.')
            return redirect('inicio')
        form = SeleccionMonedaMontoForm()
    
    context = {
        'form': form,
        'paso_actual': 1,
        'total_pasos': 4,
        'titulo_paso': 'Selección de Moneda y Monto',
        'tipo_transaccion': 'compra'  # Agregar contexto para diferenciar en plantilla
    }
    
    # Agregar información de límites si hay cliente activo
    if hasattr(request.user, 'cliente_activo') and request.user.cliente_activo:
        context.update(obtener_contexto_limites(request.user.cliente_activo))
    
    return render(request, 'transacciones/seleccion_moneda_monto.html', context)

@login_required
def compra_medio_pago(request):
    """
    Segundo paso del proceso de compra: selección del medio de pago.
    
    Permite al usuario seleccionar cómo va a pagar por la moneda extranjera.
    Las opciones incluyen efectivo, cheque, billetera electrónica, transferencia
    bancaria y tarjetas de crédito registradas en Stripe.
    
    Validaciones realizadas:
        - Datos del paso anterior deben existir en sesión
        - Usuario debe tener cliente activo
        - Medio de pago debe estar disponible para el cliente
        - Verificación de cambios en cotización
    
    Args:
        request (HttpRequest): Petición HTTP con selección de medio de pago
        
    Returns:
        HttpResponse: Renderiza formulario o redirecciona al siguiente paso
        
    Template:
        transacciones/seleccion_medio_pago.html o transacciones/cotizacion_cambiada.html
        
    Context:
        - moneda: Moneda seleccionada en el paso anterior
        - monto: Monto seleccionado en el paso anterior
        - medios_pago: Lista de medios de pago disponibles
        - medio_pago_seleccionado: Medio actualmente seleccionado
        - cliente_activo: Cliente activo del usuario
        - paso_actual: Número del paso actual (2)
        - total_pasos: Total de pasos en el proceso (4)
        - titulo_paso: Título descriptivo del paso
        - tipo_transaccion: Tipo de operación ('compra')
    """
    # Verificar que el usuario tenga un cliente activo
    if not request.user.cliente_activo:
        messages.error(request, 'Debe tener un cliente activo seleccionado para continuar.')
        return redirect('inicio')
    
    # Verificar que existan datos del paso anterior
    compra_datos = request.session.get('compra_datos')
    if not compra_datos or compra_datos.get('paso_actual') != 2:
        messages.error(request, 'Debe completar el primer paso antes de continuar.')
        return redirect('transacciones:compra_monto_moneda')
    
    # VERIFICAR CAMBIOS DE COTIZACIÓN
    cambios = verificar_cambio_cotizacion_sesion(request, 'compra')
    if cambios and cambios.get('hay_cambios'):
        # Manejar POST del modal de cambio de cotización
        if request.method == 'POST' and request.POST.get('action'):
            action = request.POST.get('action')
            if action == 'aceptar':
                # Usuario acepta los nuevos precios, actualizar precios en sesión
                moneda = cambios['moneda']
                cliente_activo = request.user.cliente_activo
                precios_actuales = moneda.get_precios_cliente(cliente_activo)
                request.session['precio_compra_inicial'] = precios_actuales['precio_compra']
                request.session['precio_venta_inicial'] = precios_actuales['precio_venta']
                messages.success(request, 'Precios actualizados. Continuando con la transacción.')
                # Continuar con el flujo normal
            elif action == 'cancelar':
                # Usuario cancela la transacción
                # Limpiar datos de sesión
                if 'compra_datos' in request.session:
                    del request.session['compra_datos']
                if 'precio_compra_inicial' in request.session:
                    del request.session['precio_compra_inicial']
                if 'precio_venta_inicial' in request.session:
                    del request.session['precio_venta_inicial']
                messages.info(request, 'Transacción cancelada debido a cambios en la cotización.')
                return redirect('inicio')
        else:
            # Mostrar modal de cambio de cotización
            return render(request, 'transacciones/cotizacion_cambiada.html', {
                'cambios': cambios,
                'paso_actual': 2,
                'tipo_transaccion': 'compra'
            })
    
    # Recuperar los datos de la sesión
    try:
        moneda = Moneda.objects.get(id=compra_datos['moneda'])
        monto = Decimal(compra_datos['monto'])
    except (Moneda.DoesNotExist, ValueError, KeyError):
        messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
        return redirect('transacciones:compra_monto_moneda')
    
    if request.method == 'POST':
        # Verificar si es selección de medio de pago o avance al siguiente paso
        accion = request.POST.get('accion')
        
        if accion == 'seleccionar_medio':
            # Manejar la selección de medio de pago
            medio_pago = request.POST.get('medio_pago_id')
            if medio_pago:
                try:
                    # Actualizar los datos de la sesión (sin cambiar el paso_actual)
                    compra_datos.update({
                        'medio_pago': medio_pago
                    })
                    request.session['compra_datos'] = compra_datos
                    if medio_pago.startswith('{'):
                        medio_pago_dict = ast.literal_eval(medio_pago)
                        messages.success(request, f'Medio de pago Tarjeta de Crédito (**** **** **** {medio_pago_dict["last4"]}) seleccionado correctamente.')
                    else:
                        messages.success(request, f'Medio de pago {medio_pago} seleccionado correctamente.')
                    return redirect('transacciones:compra_medio_pago')  # Permanecer en el mismo paso
        
                except Exception as e:
                    messages.error(request, 'Error al seleccionar el medio de pago. Intente nuevamente.')
                    return redirect('transacciones:compra_medio_pago')
        
        elif accion == 'continuar':
            # Verificar que hay un medio de pago seleccionado
            if not compra_datos.get('medio_pago'):
                messages.error(request, 'Debe seleccionar un medio de pago antes de continuar.')
                return redirect('transacciones:compra_medio_pago')
            
            # Actualizar el paso actual y continuar al siguiente paso
            compra_datos['paso_actual'] = 3
            request.session['compra_datos'] = compra_datos
            return redirect('transacciones:compra_medio_cobro')
    
    medios_pago_disponibles = [
        'Efectivo',
        'Cheque',
        'Billetera Electrónica',
        'Transferencia Bancaria'
    ]
    # Verificar si el cliente tiene tarjetas de crédito activas en Stripe
    if request.user.cliente_activo.tiene_tarjetas_activas():
        for tarjeta in request.user.cliente_activo.obtener_tarjetas_stripe():
            medios_pago_disponibles.append(tarjeta)
    for billetera in Recargos.objects.all().exclude(nombre='Tarjeta de Crédito'):
        medios_pago_disponibles.append(billetera.nombre)
    # Obtener el medio de pago seleccionado actualmente (si hay uno)
    medio_pago_seleccionado = None
    if compra_datos.get('medio_pago'):
        if compra_datos['medio_pago'].startswith('{'):
            medio_pago_seleccionado = ast.literal_eval(compra_datos['medio_pago'])
        else:
            medio_pago_seleccionado = compra_datos['medio_pago']

    context = {
        'moneda': moneda,
        'monto': monto,
        'medios_pago': medios_pago_disponibles,
        'medio_pago_seleccionado': medio_pago_seleccionado,
        'cliente_activo': request.user.cliente_activo,
        'paso_actual': 2,
        'total_pasos': 4,
        'titulo_paso': 'Selección de Medio de Pago',
        'tipo_transaccion': 'compra'  # Agregar contexto para diferenciar en plantilla
    }
    
    return render(request, 'transacciones/seleccion_medio_pago.html', context)

@login_required
def compra_medio_cobro(request):
    """
    Tercer paso del proceso de compra: selección del medio de cobro.
    
    Permite al usuario seleccionar cómo va a recibir la moneda extranjera
    que está comprando. Actualmente solo se ofrece la opción de efectivo
    como medio de cobro para las compras.
    
    Validaciones realizadas:
        - Datos de pasos anteriores deben existir en sesión
        - Usuario debe tener cliente activo
        - Medio de cobro debe estar disponible
        - Verificación de cambios en cotización
    
    Args:
        request (HttpRequest): Petición HTTP con selección de medio de cobro
        
    Returns:
        HttpResponse: Renderiza formulario o redirecciona al siguiente paso
        
    Template:
        transacciones/seleccion_medio_cobro.html o transacciones/cotizacion_cambiada.html
        
    Context:
        - moneda: Moneda seleccionada
        - monto: Monto seleccionado
        - medio_pago: Medio de pago seleccionado
        - medios_cobro: Lista de medios de cobro disponibles
        - medio_cobro_seleccionado: Medio de cobro actualmente seleccionado
        - cliente_activo: Cliente activo del usuario
        - paso_actual: Número del paso actual (3)
        - total_pasos: Total de pasos en el proceso (4)
        - titulo_paso: Título descriptivo del paso
        - tipo_transaccion: Tipo de operación ('compra')
    """
    # Verificar que el usuario tenga un cliente activo
    if not request.user.cliente_activo:
        messages.error(request, 'Debe tener un cliente activo seleccionado para continuar.')
        return redirect('inicio')
    
    # Verificar que existan datos del paso anterior
    compra_datos = request.session.get('compra_datos')
    if not compra_datos or compra_datos.get('paso_actual') != 3:
        messages.error(request, 'Debe completar el segundo paso antes de continuar.')
        return redirect('transacciones:compra_medio_pago')
    
    # VERIFICAR CAMBIOS DE COTIZACIÓN
    cambios = verificar_cambio_cotizacion_sesion(request, 'compra')
    if cambios and cambios.get('hay_cambios'):
        # Manejar POST del modal de cambio de cotización
        if request.method == 'POST' and request.POST.get('action'):
            action = request.POST.get('action')
            if action == 'aceptar':
                # Usuario acepta los nuevos precios, actualizar precios en sesión
                moneda = cambios['moneda']
                cliente_activo = request.user.cliente_activo
                precios_actuales = moneda.get_precios_cliente(cliente_activo)
                request.session['precio_compra_inicial'] = precios_actuales['precio_compra']
                request.session['precio_venta_inicial'] = precios_actuales['precio_venta']
                messages.success(request, 'Precios actualizados. Continuando con la transacción.')
                # Continuar con el flujo normal
            elif action == 'cancelar':
                # Usuario cancela la transacción
                # Limpiar datos de sesión
                if 'compra_datos' in request.session:
                    del request.session['compra_datos']
                if 'precio_compra_inicial' in request.session:
                    del request.session['precio_compra_inicial']
                if 'precio_venta_inicial' in request.session:
                    del request.session['precio_venta_inicial']
                messages.info(request, 'Transacción cancelada debido a cambios en la cotización.')
                return redirect('inicio')
        else:
            # Mostrar modal de cambio de cotización
            return render(request, 'transacciones/cotizacion_cambiada.html', {
                'cambios': cambios,
                'paso_actual': 3,
                'tipo_transaccion': 'compra'
            })
    
    # Recuperar los datos de la sesión
    try:
        moneda = Moneda.objects.get(id=compra_datos['moneda'])
        # Guardar valores iniciales de cotización
        request.session['tasa_base_inicial'] = moneda.tasa_base
        request.session['comision_compra_inicial'] = moneda.comision_compra
        request.session['comision_venta_inicial'] = moneda.comision_venta
        monto = Decimal(compra_datos['monto'])
        medio_pago = compra_datos['medio_pago']
    except (Moneda.DoesNotExist, ValueError, KeyError):
        messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
        return redirect('transacciones:compra_monto_moneda')
    if request.method == 'POST':
        # Verificar si es selección de medio de cobro o avance al siguiente paso
        accion = request.POST.get('accion')
        
        if accion == 'seleccionar_medio':
            # Manejar la selección de medio de cobro
            medio_cobro = request.POST.get('medio_cobro_id')
            if medio_cobro:
                try:
                    # Actualizar los datos de la sesión (sin cambiar el paso_actual)
                    compra_datos.update({
                        'medio_cobro': medio_cobro
                    })
                    request.session['compra_datos'] = compra_datos

                    messages.success(request, f'Medio de cobro {medio_cobro} seleccionado correctamente.')
                    return redirect('transacciones:compra_medio_cobro')  # Permanecer en el mismo paso
        
                except Exception as e:
                    messages.error(request, 'Error al seleccionar el medio de cobro. Intente nuevamente.')
                    return redirect('transacciones:compra_medio_cobro')
        
        elif accion == 'continuar':
            # Verificar que hay un medio de cobro seleccionado
            if not compra_datos.get('medio_cobro'):
                messages.error(request, 'Debe seleccionar un medio de cobro antes de continuar.')
                return redirect('transacciones:compra_medio_cobro')
            
            # Actualizar el paso actual y continuar al siguiente paso
            compra_datos['paso_actual'] = 4
            request.session['compra_datos'] = compra_datos
            return redirect('transacciones:compra_confirmacion')
    
    # Construir lista de medios de cobro disponibles
    medios_cobro_disponibles = ['Efectivo']  # Opción fija

    # Obtener el medio de cobro seleccionado actualmente (si hay uno)
    medio_cobro_seleccionado = None
    if compra_datos.get('medio_cobro'):
        medio_cobro_seleccionado = compra_datos['medio_cobro']

    context = {
        'moneda': moneda,
        'monto': monto,
        'medio_pago': medio_pago,
        'medios_cobro': medios_cobro_disponibles,
        'medio_cobro_seleccionado': medio_cobro_seleccionado,
        'cliente_activo': request.user.cliente_activo,
        'paso_actual': 3,
        'total_pasos': 4,
        'titulo_paso': 'Selección de Medio de Cobro',
        'tipo_transaccion': 'compra'
    }
    
    return render(request, 'transacciones/seleccion_medio_cobro.html', context)

@login_required
def compra_confirmacion(request):
    """
    Cuarto paso del proceso de compra: confirmación y creación de transacción.
    
    Muestra un resumen completo de la transacción y procede a crearla en
    la base de datos. Para medios de pago como Efectivo o Cheque,
    genera un token de seguridad con validez de 5 minutos.
    
    Acciones realizadas:
        - Verificación de cambios en cotización
        - Creación de registro de transacción en base de datos
        - Generación de token para medios específicos
        - Configuración del estado inicial como 'Pendiente'
        - Vinculación con cliente y usuario activos
    
    Args:
        request (HttpRequest): Petición HTTP de confirmación
        
    Returns:
        HttpResponse: Renderiza página de confirmación o modal de cambio
        
    Template:
        transacciones/confirmacion.html o transacciones/cotizacion_cambiada.html
        
    Context:
        - moneda: Moneda de la transacción
        - monto: Monto de la transacción
        - medio_pago: Medio de pago seleccionado
        - medio_cobro: Medio de cobro seleccionado
        - cliente_activo: Cliente que realiza la transacción
        - transaccion: Instancia de transacción creada
        - paso_actual: Número del paso actual (4)
        - total_pasos: Total de pasos en el proceso (4)
        - titulo_paso: Título descriptivo del paso
        - tipo_transaccion: Tipo de operación ('compra')
    """
    # Verificar que el usuario tenga un cliente activo
    if not request.user.cliente_activo:
        messages.error(request, 'Debe tener un cliente activo seleccionado para continuar.')
        return redirect('inicio')
    
    # Verificar que existan datos del paso anterior
    compra_datos = request.session.get('compra_datos')
    if not compra_datos or compra_datos.get('paso_actual') != 4:
        messages.error(request, 'Debe completar el tercer paso antes de continuar.')
        return redirect('transacciones:compra_medio_cobro')
    
    cambios = verificar_cambio_cotizacion_sesion(request, 'compra')
    if cambios and cambios.get('hay_cambios'):
        # Manejar POST del modal de cambio de cotización
        if request.method == 'POST' and request.POST.get('action'):
            action = request.POST.get('action')
            if action == 'aceptar':
                # Usuario acepta los nuevos precios, actualizar precios en sesión
                moneda = cambios['moneda']
                cliente_activo = request.user.cliente_activo
                precios_actuales = moneda.get_precios_cliente(cliente_activo)
                request.session['precio_compra_inicial'] = precios_actuales['precio_compra']
                request.session['precio_venta_inicial'] = precios_actuales['precio_venta']
                messages.success(request, 'Precios actualizados. Continuando con la transacción.')
                # Continuar con el flujo normal
            elif action == 'cancelar':
                # Usuario cancela la transacción
                # Limpiar datos de sesión
                if 'compra_datos' in request.session:
                    del request.session['compra_datos']
                if 'precio_compra_inicial' in request.session:
                    del request.session['precio_compra_inicial']
                if 'precio_venta_inicial' in request.session:
                    del request.session['precio_venta_inicial']
                messages.info(request, 'Transacción cancelada debido a cambios en la cotización.')
                return redirect('inicio')
        else:
            # Mostrar modal de cambio de cotización
            return render(request, 'transacciones/cotizacion_cambiada.html', {
                'cambios': cambios,
                'paso_actual': 4,
                'tipo_transaccion': 'compra'
            })
    
    # Recuperar los datos de la sesión
    try:
        moneda = Moneda.objects.get(id=compra_datos['moneda'])
        monto = Decimal(compra_datos['monto'])
        medio_pago = compra_datos['medio_pago']
        medio_cobro = compra_datos['medio_cobro']
    except (Moneda.DoesNotExist, ValueError, KeyError):
        messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
        return redirect('transacciones:compra_monto_moneda')
    
    context = {
        'moneda': moneda,
        'recibir': monto,
        'dar': convertir(monto, request.user.cliente_activo, moneda, 'compra', medio_pago, medio_cobro),
        'medio_pago': ast.literal_eval(medio_pago) if medio_pago.startswith('{') else medio_pago,
        'medio_cobro': medio_cobro,
        'cliente_activo': request.user.cliente_activo,
        'paso_actual': 4,
        'total_pasos': 4,
        'titulo_paso': 'Confirmación de Compra',
        'tipo_transaccion': 'compra'
    }
    
    return render(request, 'transacciones/confirmacion.html', context)

@login_required
def compra_exito(request):
    """
    Página final del proceso de compra: mensaje de éxito.
    
    Verifica si hay cambios en la cotización antes de finalizar la transacción.
    Si hay cambios, muestra el modal de confirmación. Si no hay cambios o el usuario
    acepta los nuevos precios, muestra confirmación de éxito.
    
    Args:
        request (HttpRequest): Petición HTTP
        
    Returns:
        HttpResponse: Página de éxito o modal de cambio de cotización
        
    Template:
        transacciones/exito.html o transacciones/cotizacion_cambiada.html
    """
    # Verificar que el usuario tenga un cliente activo
    if not request.user.cliente_activo:
        messages.error(request, 'Debe tener un cliente activo seleccionado para continuar.')
        return redirect('inicio')
    compra_datos = request.session.get('compra_datos')
    try:
        moneda = Moneda.objects.get(id=compra_datos['moneda'])
        monto = Decimal(compra_datos['monto'])
        medio_pago = compra_datos['medio_pago']
        medio_cobro = compra_datos['medio_cobro']
    except (Moneda.DoesNotExist, ValueError, KeyError):
        messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
        return redirect('transacciones:compra_monto_moneda')
    
    cambios = verificar_cambio_cotizacion_sesion(request, 'compra')
    if cambios and cambios.get('hay_cambios'):
        # Manejar POST del modal de cambio de cotización
        if request.method == 'POST' and request.POST.get('action'):
            action = request.POST.get('action')
            if action == 'aceptar':
                # Usuario acepta los nuevos precios, actualizar precios en sesión
                moneda = cambios['moneda']
                cliente_activo = request.user.cliente_activo
                precios_actuales = moneda.get_precios_cliente(cliente_activo)
                request.session['precio_compra_inicial'] = precios_actuales['precio_compra']
                request.session['precio_venta_inicial'] = precios_actuales['precio_venta']
                messages.success(request, 'Precios actualizados. Continuando con la transacción.')
                # Continuar con el flujo normal
            elif action == 'cancelar':
                # Usuario cancela la transacción
                # Limpiar datos de sesión
                if 'compra_datos' in request.session:
                    del request.session['compra_datos']
                if 'precio_compra_inicial' in request.session:
                    del request.session['precio_compra_inicial']
                if 'precio_venta_inicial' in request.session:
                    del request.session['precio_venta_inicial']
                messages.info(request, 'Transacción cancelada debido a cambios en la cotización.')
                return redirect('inicio')
        else:
            # Mostrar modal de cambio de cotización
            return render(request, 'transacciones/cotizacion_cambiada.html', {
                'cambios': cambios,
                'paso_actual': 4,
                'tipo_transaccion': 'compra'
            })
    # Crear la transacción en la base de datos
    try:
        if medio_pago.startswith('{'):
            medio_pago_dict = ast.literal_eval(medio_pago)
            str_medio_pago = f'Tarjeta de Crédito (**** **** **** {medio_pago_dict["last4"]})'
        else:
            str_medio_pago = medio_pago
        transaccion = Transaccion.objects.create(
            cliente=request.user.cliente_activo,
            tipo='compra',
            moneda=moneda,
            monto=monto,
            medio_pago=str_medio_pago,
            medio_cobro=medio_cobro,
            usuario=request.user
        )

        if medio_pago.startswith('{'):
            medio_pago_dict = ast.literal_eval(medio_pago)
            if procesar_pago_stripe(transaccion.id, medio_pago_dict["id"])['success']:
                messages.success(request, 'Pago con tarjeta de crédito procesado exitosamente.')
                token_data = generar_token_transaccion(transaccion.id)
            else:
                messages.error(request, 'Error al procesar el pago con tarjeta de crédito. Intente nuevamente.')
                return redirect('transacciones:compra_monto_moneda')
        else:
            try:
                token_data = generar_token_transaccion(transaccion.id)
                # Guardar el token en la sesión para su posterior uso
                request.session['token_transaccion'] = token_data

                messages.success(request, f'Transacción creada. Token generado: {token_data["token"][:8]}... (válido por 5 minutos)')

            except Exception as e:
                messages.error(request, 'Error al generar token de transacción. Intente nuevamente.')
                return redirect('transacciones:compra_medio_cobro')
            
    except Exception as e:
        messages.error(request, 'Error al crear la transacción. Intente nuevamente.')
        return redirect('transacciones:compra_medio_cobro')
    
    context = {
        'token': token_data['token'],
        'tipo': 'compra'
    }
    
    return render(request, 'transacciones/exito.html', context)

# ============================================================================
# PROCESO DE VENTA DE MONEDAS
# ============================================================================

@login_required
def venta_monto_moneda(request):
    """
    Primer paso del proceso de venta: selección de moneda y monto.
    
    Permite al usuario seleccionar la moneda extranjera que desea vender
    y especificar el monto. Similar al proceso de compra pero con validaciones
    específicas para operaciones de venta.
    
    Validaciones realizadas:
        - Usuario debe tener un cliente activo
        - Monto debe cumplir con límites diarios y mensuales
        - Moneda debe estar activa en el sistema
    
    Args:
        request (HttpRequest): Petición HTTP con datos del formulario
        
    Returns:
        HttpResponse: Renderiza formulario o redirecciona al siguiente paso
        
    Template:
        transacciones/seleccion_moneda_monto.html
        
    Context:
        - form: Formulario de selección de moneda y monto
        - paso_actual: Número del paso actual (1)
        - total_pasos: Total de pasos en el proceso (4)
        - titulo_paso: Título descriptivo del paso
        - tipo_transaccion: Tipo de operación ('venta')
        - limites_disponibles: Información de límites del cliente
    """
    if request.method == 'POST':
        form = SeleccionMonedaMontoForm(request.POST)
        if form.is_valid():
            moneda = form.cleaned_data['moneda']
            monto = form.cleaned_data['monto_decimal']
            
            # Verificar límites de transacción para ventas
            try:
                cliente_activo = request.user.cliente_activo
                
                # Convertir el monto a guaraníes para verificar límites
                monto_guaranies = LimiteService.convertir_a_guaranies(
                    int(monto), moneda, 'VENTA', cliente_activo
                )
                
                # Validar que no supere los límites (sin actualizar consumo aún)
                LimiteService.validar_limite_transaccion(cliente_activo, monto_guaranies)
                
            except ValidationError as e:
                # Si hay error de límites, mostrar mensaje y no proceder
                messages.error(request, extraer_mensaje_error(e))
                context = {
                    'form': form,
                    'paso_actual': 1,
                    'total_pasos': 4,
                    'titulo_paso': 'Selección de Moneda y Monto',
                    'tipo_transaccion': 'venta'
                }
                # Agregar información de límites al contexto de error
                context.update(obtener_contexto_limites(cliente_activo))
                return render(request, 'transacciones/seleccion_moneda_monto.html', context)
            except Exception as e:
                # Error general del sistema de límites
                messages.error(request, 'Error al verificar límites de transacción. Inténtelo nuevamente.')
                context = {
                    'form': form,
                    'paso_actual': 1,
                    'total_pasos': 4,
                    'titulo_paso': 'Selección de Moneda y Monto',
                    'tipo_transaccion': 'venta'
                }
                # Agregar información de límites al contexto de error
                context.update(obtener_contexto_limites(cliente_activo))
                return render(request, 'transacciones/seleccion_moneda_monto.html', context)
            
            # Si pasa las validaciones, guardar los datos en la sesión
            request.session['venta_datos'] = {
                'moneda': moneda.id,
                'monto': str(monto),  # Convertir Decimal a string para serialización
                'paso_actual': 2
            }
            # Guardar precios iniciales en la sesión
            precios_iniciales = moneda.get_precios_cliente(request.user.cliente_activo)
            request.session['precio_compra_inicial'] = precios_iniciales['precio_compra']
            request.session['precio_venta_inicial'] = precios_iniciales['precio_venta']
            
            # Redireccionar al siguiente paso sin parámetros en la URL
            return redirect('transacciones:venta_medio_pago')
    else:
        # Verificar si el usuario tiene un cliente activo
        if not request.user.cliente_activo:
            messages.error(request, 'Debes tener un cliente activo para realizar ventas.')
            return redirect('inicio')
        form = SeleccionMonedaMontoForm()
    
    context = {
        'form': form,
        'paso_actual': 1,
        'total_pasos': 4,
        'titulo_paso': 'Selección de Moneda y Monto',
        'tipo_transaccion': 'venta'  # Agregar contexto para diferenciar en plantilla
    }
    
    # Agregar información de límites si hay cliente activo
    if hasattr(request.user, 'cliente_activo') and request.user.cliente_activo:
        context.update(obtener_contexto_limites(request.user.cliente_activo))
    
    return render(request, 'transacciones/seleccion_moneda_monto.html', context)

@login_required
def venta_medio_pago(request):
    """
    Segundo paso del proceso de venta: selección del medio de pago.
    
    Permite al usuario seleccionar cómo va a recibir el pago por la moneda
    extranjera que está vendiendo. Para ventas, principalmente se ofrece
    efectivo, y para USD también tarjetas de crédito registradas.
    
    Validaciones realizadas:
        - Datos del paso anterior deben existir en sesión
        - Usuario debe tener cliente activo
        - Para tarjetas: solo disponibles para USD y clientes con tarjetas activas
    
    Args:
        request (HttpRequest): Petición HTTP con selección de medio de pago
        
    Returns:
        HttpResponse: Renderiza formulario o redirecciona al siguiente paso
        
    Template:
        transacciones/seleccion_medio_pago.html
        
    Context:
        - moneda: Moneda seleccionada en el paso anterior
        - monto: Monto seleccionado en el paso anterior
        - medios_pago: Lista de medios de pago disponibles
        - medio_pago_seleccionado: Medio actualmente seleccionado
        - cliente_activo: Cliente activo del usuario
        - paso_actual: Número del paso actual (2)
        - tipo_transaccion: Tipo de operación ('venta')
    """
    # Verificar que el usuario tenga un cliente activo
    if not request.user.cliente_activo:
        messages.error(request, 'Debe tener un cliente activo seleccionado para continuar.')
        return redirect('inicio')
    
    # Verificar que existan datos del paso anterior
    venta_datos = request.session.get('venta_datos')
    if not venta_datos or venta_datos.get('paso_actual') != 2:
        messages.error(request, 'Debe completar el primer paso antes de continuar.')
        return redirect('transacciones:venta_monto_moneda')
    
    # VERIFICAR CAMBIOS DE COTIZACIÓN
    cambios = verificar_cambio_cotizacion_sesion(request, 'venta')
    if cambios and cambios.get('hay_cambios'):
        # Manejar POST del modal de cambio de cotización
        if request.method == 'POST' and request.POST.get('action'):
            action = request.POST.get('action')
            if action == 'aceptar':
                # Usuario acepta los nuevos precios, actualizar precios en sesión
                moneda = cambios['moneda']
                cliente_activo = request.user.cliente_activo
                precios_actuales = moneda.get_precios_cliente(cliente_activo)
                request.session['precio_compra_inicial'] = precios_actuales['precio_compra']
                request.session['precio_venta_inicial'] = precios_actuales['precio_venta']
                messages.success(request, 'Precios actualizados. Continuando con la transacción.')
                # Continuar con el flujo normal
            elif action == 'cancelar':
                # Usuario cancela la transacción
                # Limpiar datos de sesión
                if 'venta_datos' in request.session:
                    del request.session['venta_datos']
                if 'precio_compra_inicial' in request.session:
                    del request.session['precio_compra_inicial']
                if 'precio_venta_inicial' in request.session:
                    del request.session['precio_venta_inicial']
                messages.info(request, 'Transacción cancelada debido a cambios en la cotización.')
                return redirect('inicio')
        else:
            # Mostrar modal de cambio de cotización
            return render(request, 'transacciones/cotizacion_cambiada.html', {
                'cambios': cambios,
                'paso_actual': 2,
                'tipo_transaccion': 'venta'
            })
    
    # Recuperar los datos de la sesión
    try:
        moneda = Moneda.objects.get(id=venta_datos['moneda'])
        monto = Decimal(venta_datos['monto'])
    except (Moneda.DoesNotExist, ValueError, KeyError):
        messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
        return redirect('transacciones:venta_monto_moneda')
    
    if request.method == 'POST':
        # Verificar si es selección de medio de pago o avance al siguiente paso
        accion = request.POST.get('accion')
        
        if accion == 'seleccionar_medio':
            # Manejar la selección de medio de pago
            medio_pago = request.POST.get('medio_pago_id')
            if medio_pago:
                try:
                    
                    # Actualizar los datos de la sesión (sin cambiar el paso_actual)
                    venta_datos.update({
                        'medio_pago': medio_pago
                    })
                    request.session['venta_datos'] = venta_datos
                    if medio_pago.startswith('{'):
                        medio_pago_dict = ast.literal_eval(medio_pago)
                        messages.success(request, f'Medio de pago Tarjeta de Crédito (**** **** **** {medio_pago_dict["last4"]}) seleccionado correctamente.')
                    else:
                        messages.success(request, f'Medio de pago {medio_pago} seleccionado correctamente.')
                    return redirect('transacciones:venta_medio_pago')  # Permanecer en el mismo paso
        
                except Exception as e:
                    messages.error(request, 'Error al seleccionar el medio de pago. Intente nuevamente.')
                    return redirect('transacciones:venta_medio_pago')
        
        elif accion == 'continuar':
            # Verificar que hay un medio de pago seleccionado
            if not venta_datos.get('medio_pago'):
                messages.error(request, 'Debe seleccionar un medio de pago antes de continuar.')
                return redirect('transacciones:venta_medio_pago')
            
            # Actualizar el paso actual y continuar al siguiente paso
            venta_datos['paso_actual'] = 3
            request.session['venta_datos'] = venta_datos
            return redirect('transacciones:venta_medio_cobro')
    
    medios_pago_disponibles = [
        'Efectivo',
    ]
    # Para ventas, verificar tarjetas activas solo para USD
    if moneda.simbolo == 'USD' and request.user.cliente_activo.tiene_tarjetas_activas():
        for tarjeta in request.user.cliente_activo.obtener_tarjetas_stripe():
            medios_pago_disponibles.append(tarjeta)

    # Obtener el medio de pago seleccionado actualmente (si hay uno)
    medio_pago_seleccionado = None
    if venta_datos.get('medio_pago'):
        if venta_datos['medio_pago'].startswith('{'):
            medio_pago_seleccionado = ast.literal_eval(venta_datos['medio_pago'])
        else:
            medio_pago_seleccionado = venta_datos['medio_pago']

    context = {
        'moneda': moneda,
        'monto': monto,
        'medios_pago': medios_pago_disponibles,
        'medio_pago_seleccionado': medio_pago_seleccionado,
        'cliente_activo': request.user.cliente_activo,
        'paso_actual': 2,
        'total_pasos': 4,
        'titulo_paso': 'Selección de Medio de Pago',
        'tipo_transaccion': 'venta'  # Agregar contexto para diferenciar en plantilla
    }
    
    return render(request, 'transacciones/seleccion_medio_pago.html', context)

@login_required
def venta_medio_cobro(request):
    """
    Tercer paso del proceso de venta: selección del medio de cobro.
    
    Permite al usuario seleccionar cómo va a entregar la moneda extranjera
    que está vendiendo. Incluye opciones como efectivo, cuentas bancarias
    registradas y billeteras electrónicas del cliente.
    
    Validaciones realizadas:
        - Datos de pasos anteriores deben existir en sesión
        - Usuario debe tener cliente activo
        - Medios disponibles según configuración del cliente
    
    Args:
        request (HttpRequest): Petición HTTP con selección de medio de cobro
        
    Returns:
        HttpResponse: Renderiza formulario o redirecciona al siguiente paso
        
    Template:
        transacciones/seleccion_medio_cobro.html
        
    Context:
        - moneda: Moneda seleccionada
        - monto: Monto seleccionado
        - medio_pago: Medio de pago seleccionado
        - medios_cobro: Lista de medios de cobro disponibles (efectivo, cuentas, billeteras)
        - medio_cobro_seleccionado: Medio de cobro actualmente seleccionado
        - cliente_activo: Cliente activo del usuario
        - paso_actual: Número del paso actual (3)
        - tipo_transaccion: Tipo de operación ('venta')
    """
    # Verificar que el usuario tenga un cliente activo
    if not request.user.cliente_activo:
        messages.error(request, 'Debe tener un cliente activo seleccionado para continuar.')
        return redirect('inicio')
    # Verificar que existan datos del paso anterior
    venta_datos = request.session.get('venta_datos')
    if not venta_datos or venta_datos.get('paso_actual') != 3:
        messages.error(request, 'Debe completar el segundo paso antes de continuar.')
        return redirect('transacciones:venta_medio_pago')

    # VERIFICAR CAMBIOS DE COTIZACIÓN
    cambios = verificar_cambio_cotizacion_sesion(request, 'venta')
    if cambios and cambios.get('hay_cambios'):
        # Manejar POST del modal de cambio de cotización
        if request.method == 'POST' and request.POST.get('action'):
            action = request.POST.get('action')
            if action == 'aceptar':
                # Usuario acepta los nuevos precios, actualizar precios en sesión
                moneda = cambios['moneda']
                cliente_activo = request.user.cliente_activo
                precios_actuales = moneda.get_precios_cliente(cliente_activo)
                request.session['precio_compra_inicial'] = precios_actuales['precio_compra']
                request.session['precio_venta_inicial'] = precios_actuales['precio_venta']
                messages.success(request, 'Precios actualizados. Continuando con la transacción.')
                # Continuar con el flujo normal
            elif action == 'cancelar':
                # Usuario cancela la transacción
                # Limpiar datos de sesión
                if 'venta_datos' in request.session:
                    del request.session['venta_datos']
                if 'precio_compra_inicial' in request.session:
                    del request.session['precio_compra_inicial']
                if 'precio_venta_inicial' in request.session:
                    del request.session['precio_venta_inicial']
                messages.info(request, 'Transacción cancelada debido a cambios en la cotización.')
                return redirect('inicio')
        else:
            # Mostrar modal de cambio de cotización
            return render(request, 'transacciones/cotizacion_cambiada.html', {
                'cambios': cambios,
                'paso_actual': 3,
                'tipo_transaccion': 'venta'
            })
    # Recuperar los datos de la sesión
    try:
        moneda = Moneda.objects.get(id=venta_datos['moneda'])
        # Guardar valores iniciales de cotización
        request.session['tasa_base_inicial'] = moneda.tasa_base
        request.session['comision_compra_inicial'] = moneda.comision_compra
        request.session['comision_venta_inicial'] = moneda.comision_venta
        monto = Decimal(venta_datos['monto'])
        medio_pago = venta_datos['medio_pago']
    except (Moneda.DoesNotExist, ValueError, KeyError):
        messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
        return redirect('transacciones:venta_monto_moneda')
    
    if request.method == 'POST':
        # Verificar si es selección de medio de cobro o avance al siguiente paso
        accion = request.POST.get('accion')
        
        if accion == 'seleccionar_medio':
            # Manejar la selección de medio de cobro
            medio_cobro = request.POST.get('medio_cobro_id')
            if medio_cobro:
                try:
                    # Actualizar los datos de la sesión (sin cambiar el paso_actual)
                    venta_datos.update({
                        'medio_cobro': medio_cobro
                    })
                    request.session['venta_datos'] = venta_datos
                    if medio_cobro.startswith('{'):
                        medio_cobro_dict = ast.literal_eval(medio_cobro)
                        messages.success(request, f'Medio de cobro {medio_cobro_dict["tipo_billetera"]} seleccionado correctamente.')
                    else:
                        messages.success(request, f'Medio de cobro {medio_cobro} seleccionado correctamente.')
                    return redirect('transacciones:venta_medio_cobro')  # Permanecer en el mismo paso
        
                except Exception as e:
                    messages.error(request, 'Error al seleccionar el medio de cobro. Intente nuevamente.')
                    return redirect('transacciones:venta_medio_cobro')
        
        elif accion == 'continuar':
            # Verificar que hay un medio de cobro seleccionado
            if not venta_datos.get('medio_cobro'):
                messages.error(request, 'Debe seleccionar un medio de cobro antes de continuar.')
                return redirect('transacciones:venta_medio_cobro')
            
            # Actualizar el paso actual y continuar al siguiente paso
            venta_datos['paso_actual'] = 4
            request.session['venta_datos'] = venta_datos
            return redirect('transacciones:venta_confirmacion')
    
    # Construir lista de medios de cobro disponibles
    medios_cobro_disponibles = ['Efectivo']  # Opción fija
    
    # Agregar cuentas bancarias si las hay
    cuentas_bancarias = request.user.cliente_activo.cuentas_bancarias.all()
    for cuenta in cuentas_bancarias:
        medio_descripcion = f"Cuenta bancaria - {cuenta.get_banco_display()} ({cuenta.numero_cuenta})"
        medios_cobro_disponibles.append(medio_descripcion)
    
    # Agregar billeteras si las hay
    billeteras = request.user.cliente_activo.billeteras.all()
    for billetera in billeteras:
        billetera_dict = {
            'id': billetera.id,
            'tipo_billetera': billetera.get_tipo_billetera_display(),
            'telefono': billetera.telefono,
            'nombre_titular': billetera.nombre_titular,
            'nro_documento': billetera.nro_documento
        }
        medios_cobro_disponibles.append(billetera_dict)

    # Obtener el medio de cobro seleccionado actualmente (si hay uno)
    medio_cobro_seleccionado = None
    if venta_datos.get('medio_cobro'):
        if venta_datos['medio_cobro'].startswith('{'):
            medio_cobro_seleccionado = ast.literal_eval(venta_datos['medio_cobro'])
        else:
            medio_cobro_seleccionado = venta_datos['medio_cobro']

    context = {
        'moneda': moneda,
        'monto': monto,
        'medio_pago': medio_pago,
        'medios_cobro': medios_cobro_disponibles,
        'medio_cobro_seleccionado': medio_cobro_seleccionado,
        'cliente_activo': request.user.cliente_activo,
        'paso_actual': 3,
        'total_pasos': 4,
        'titulo_paso': 'Selección de Medio de Cobro',
        'tipo_transaccion': 'venta'
    }
    
    return render(request, 'transacciones/seleccion_medio_cobro.html', context)

@login_required
def venta_confirmacion(request):
    """
    Cuarto paso del proceso de venta: confirmación y creación de transacción.
    
    Muestra un resumen completo de la transacción de venta y procede a crearla
    en la base de datos. Para ventas en efectivo, genera un token de seguridad
    con validez de 5 minutos.
    
    Acciones realizadas:
        - Creación de registro de transacción en base de datos
        - Generación de token para pagos en efectivo
        - Configuración del estado inicial como 'Pendiente'
        - Vinculación con cliente y usuario activos
    
    Args:
        request (HttpRequest): Petición HTTP de confirmación
        
    Returns:
        HttpResponse: Renderiza página de confirmación
        
    Template:
        transacciones/confirmacion.html
        
    Context:
        - moneda: Moneda de la transacción
        - monto: Monto de la transacción
        - medio_pago: Medio de pago seleccionado
        - medio_cobro: Medio de cobro seleccionado
        - cliente_activo: Cliente que realiza la transacción
        - transaccion: Instancia de transacción creada
        - paso_actual: Número del paso actual (4)
        - tipo_transaccion: Tipo de operación ('venta')
    """
    # Verificar que el usuario tenga un cliente activo
    if not request.user.cliente_activo:
        messages.error(request, 'Debe tener un cliente activo seleccionado para continuar.')
        return redirect('inicio')
    # Verificar que existan datos del paso anterior
    venta_datos = request.session.get('venta_datos')
    if not venta_datos or venta_datos.get('paso_actual') != 4:
        messages.error(request, 'Debe completar el tercer paso antes de continuar.')
        return redirect('transacciones:venta_medio_cobro')
    
    # VERIFICAR CAMBIOS DE COTIZACIÓN
    cambios = verificar_cambio_cotizacion_sesion(request, 'venta')
    if cambios and cambios.get('hay_cambios'):
        # Manejar POST del modal de cambio de cotización
        if request.method == 'POST' and request.POST.get('action'):
            action = request.POST.get('action')
            if action == 'aceptar':
                # Usuario acepta los nuevos precios, actualizar precios en sesión
                moneda = cambios['moneda']
                cliente_activo = request.user.cliente_activo
                precios_actuales = moneda.get_precios_cliente(cliente_activo)
                request.session['precio_compra_inicial'] = precios_actuales['precio_compra']
                request.session['precio_venta_inicial'] = precios_actuales['precio_venta']
                messages.success(request, 'Precios actualizados. Continuando con la transacción.')
                # Continuar con el flujo normal
            elif action == 'cancelar':
                # Usuario cancela la transacción
                # Limpiar datos de sesión
                if 'venta_datos' in request.session:
                    del request.session['venta_datos']
                if 'precio_compra_inicial' in request.session:
                    del request.session['precio_compra_inicial']
                if 'precio_venta_inicial' in request.session:
                    del request.session['precio_venta_inicial']
                messages.info(request, 'Transacción cancelada debido a cambios en la cotización.')
                return redirect('inicio')
        else:
            # Mostrar modal de cambio de cotización
            return render(request, 'transacciones/cotizacion_cambiada.html', {
                'cambios': cambios,
                'paso_actual': 4,
                'tipo_transaccion': 'venta'
            })
    # Recuperar los datos de la sesión
    try:
        moneda = Moneda.objects.get(id=venta_datos['moneda'])
        monto = Decimal(venta_datos['monto'])
        medio_pago = venta_datos['medio_pago']
        medio_cobro = venta_datos['medio_cobro']
    except (Moneda.DoesNotExist, ValueError, KeyError):
        messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
        return redirect('transacciones:venta_monto_moneda')
    
    context = {
        'moneda': moneda,
        'recibir': convertir(monto, request.user.cliente_activo, moneda, 'venta', medio_pago, medio_cobro),
        'dar': monto,
        'medio_pago': ast.literal_eval(medio_pago) if medio_pago.startswith('{') else medio_pago,
        'medio_cobro': ast.literal_eval(medio_cobro) if medio_cobro.startswith('{') else medio_cobro,
        'cliente_activo': request.user.cliente_activo,
        'paso_actual': 4,
        'total_pasos': 4,
        'titulo_paso': 'Confirmación de Venta',
        'tipo_transaccion': 'venta'
    }
    
    return render(request, 'transacciones/confirmacion.html', context)

@login_required
def venta_exito(request):
    """
    Página final del proceso de venta: mensaje de éxito.
    
    Verifica si hay cambios en la cotización antes de finalizar la transacción.
    Si hay cambios, muestra el modal de confirmación. Si no hay cambios o el usuario
    acepta los nuevos precios, muestra confirmación de éxito.
    
    Args:
        request (HttpRequest): Petición HTTP
        
    Returns:
        HttpResponse: Página de éxito o modal de cambio de cotización
        
    Template:
        transacciones/exito.html o transacciones/cotizacion_cambiada.html
    """
    # Verificar que el usuario tenga un cliente activo
    if not request.user.cliente_activo:
        messages.error(request, 'Debe tener un cliente activo seleccionado para continuar.')
        return redirect('inicio')
    # Verificar que existan datos del paso anterior
    venta_datos = request.session.get('venta_datos')
    try:
        moneda = Moneda.objects.get(id=venta_datos['moneda'])
        monto = Decimal(venta_datos['monto'])
        medio_pago = venta_datos['medio_pago']
        medio_cobro = venta_datos.get('medio_cobro', 'No seleccionado')
    except (Moneda.DoesNotExist, ValueError, KeyError):
        messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
        return redirect('transacciones:venta_monto_moneda')

    # VERIFICAR CAMBIOS DE COTIZACIÓN
    cambios = verificar_cambio_cotizacion_sesion(request, 'venta')
    if cambios and cambios.get('hay_cambios'):
        # Manejar POST del modal de cambio de cotización
        if request.method == 'POST' and request.POST.get('action'):
            action = request.POST.get('action')
            if action == 'aceptar':
                # Usuario acepta los nuevos precios, actualizar precios en sesión
                moneda = cambios['moneda']
                cliente_activo = request.user.cliente_activo
                precios_actuales = moneda.get_precios_cliente(cliente_activo)
                request.session['precio_compra_inicial'] = precios_actuales['precio_compra']
                request.session['precio_venta_inicial'] = precios_actuales['precio_venta']
                messages.success(request, 'Precios actualizados. Continuando con la transacción.')
                # Continuar con el flujo normal
            elif action == 'cancelar':
                # Usuario cancela la transacción
                # Limpiar datos de sesión
                if 'venta_datos' in request.session:
                    del request.session['venta_datos']
                if 'precio_compra_inicial' in request.session:
                    del request.session['precio_compra_inicial']
                if 'precio_venta_inicial' in request.session:
                    del request.session['precio_venta_inicial']
                messages.info(request, 'Transacción cancelada debido a cambios en la cotización.')
                return redirect('inicio')
        else:
            # Mostrar modal de cambio de cotización
            return render(request, 'transacciones/cotizacion_cambiada.html', {
                'cambios': cambios,
                'tipo_transaccion': 'venta'
            })
    # Crear la transacción en la base de datos
    try:
        if medio_pago.startswith('{'):
            medio_pago_dict = ast.literal_eval(medio_pago)
            str_medio_pago = f'Tarjeta de Crédito (**** **** **** {medio_pago_dict["last4"]})'
        else:
            str_medio_pago = medio_pago
        if medio_cobro.startswith('{'):
            medio_cobro_dict = ast.literal_eval(medio_cobro)
            str_medio_cobro = f'{medio_cobro_dict["tipo_billetera"]} ({medio_cobro_dict["telefono"]})'
        else:
            str_medio_cobro = medio_cobro
        transaccion = Transaccion.objects.create(
            cliente=request.user.cliente_activo,
            tipo='venta',
            moneda=moneda,
            monto=monto,
            medio_pago=str_medio_pago,
            medio_cobro=str_medio_cobro,
            usuario=request.user
        )
        print(f"Transacción creada con ID: {transaccion.id}")
        
        # Generar token si el medio de pago es Efectivo
        if medio_pago.startswith('{'):
            medio_pago_dict = ast.literal_eval(medio_pago)
            if procesar_pago_stripe(transaccion.id, medio_pago_dict["id"])['success']:
                messages.success(request, 'Pago con tarjeta de crédito procesado exitosamente.')
                if medio_cobro == 'Efectivo':
                    token_data = generar_token_transaccion(transaccion.id)
                    transaccion.estado = 'Confirmada'
                    transaccion.save()
                else:
                    consumo = LimiteService.obtener_o_crear_consumo(transaccion.cliente)
                    consumo.consumo_diario += convertir(monto, request.user.cliente_activo, moneda, 'venta', medio_pago, medio_cobro)
                    consumo.consumo_mensual += convertir(monto, request.user.cliente_activo, moneda, 'venta', medio_pago, medio_cobro)
                    consumo.save()
                    transaccion.estado = 'Completa'
                    transaccion.save()
            else:
                messages.error(request, 'Error al procesar el pago con tarjeta de crédito. Intente nuevamente.')
                return redirect('transacciones:venta_monto_moneda')
            context = {
            'tipo': 'venta',
            'medio_cobro': medio_cobro,
        }
        else:
            try:
                token_data = generar_token_transaccion(transaccion.id)
                
                # Guardar el token en la sesión para su posterior uso
                request.session['token_transaccion'] = token_data

                context = {
                'token': token_data['token'],
                'tipo': 'venta',
                'medio_cobro': medio_cobro,
            }

            except Exception as e:
                messages.error(request, 'Error al generar token de transacción. Intente nuevamente.')
                return redirect('transacciones:venta_medio_cobro')
            
    except Exception as e:
        messages.error(request, 'Error al crear la transacción. Intente nuevamente.')
        return redirect('transacciones:venta_medio_cobro')
    # Limpiar los datos de la sesión relacionados con la venta
    if 'venta_datos' in request.session:
        del request.session['venta_datos']

    return render(request, 'transacciones/exito.html', context)

# ============================================================================
# VISTAS AUXILIARES Y APIs
# ============================================================================

@login_required
def obtener_limites_cliente(request):
    """
    API AJAX para consultar límites de transacción del cliente activo.
    
    Devuelve información detallada sobre los límites diarios y mensuales
    del cliente, incluyendo consumo actual y disponibilidad restante.
    Útil para mostrar información dinámica en las interfaces de usuario.
    
    Args:
        request (HttpRequest): Petición AJAX
        
    Returns:
        JsonResponse: Información de límites en formato JSON
            - limite_diario: Límite diario total
            - limite_mensual: Límite mensual total
            - consumo_diario: Consumo actual del día
            - consumo_mensual: Consumo actual del mes
            - disponible_diario: Disponible restante hoy
            - disponible_mensual: Disponible restante este mes
            - porcentaje_uso_diario: Porcentaje usado del límite diario
            - porcentaje_uso_mensual: Porcentaje usado del límite mensual
            
    Status Codes:
        - 200: Información obtenida exitosamente
        - 400: No hay cliente activo
        - 500: Error interno del servidor
    """
    if not request.user.cliente_activo:
        return JsonResponse({
            'error': 'No hay cliente activo'
        }, status=400)
    
    try:
        limites_info = LimiteService.obtener_limites_disponibles(request.user.cliente_activo)
        
        if 'error' in limites_info:
            return JsonResponse({
                'error': limites_info['error']
            }, status=500)
        
        return JsonResponse({
            'limite_diario': limites_info['limite_diario'],
            'limite_mensual': limites_info['limite_mensual'],
            'consumo_diario': limites_info['consumo_diario'],
            'consumo_mensual': limites_info['consumo_mensual'],
            'disponible_diario': limites_info['disponible_diario'],
            'disponible_mensual': limites_info['disponible_mensual'],
            'porcentaje_uso_diario': limites_info['porcentaje_uso_diario'],
            'porcentaje_uso_mensual': limites_info['porcentaje_uso_mensual']
        })
        
    except Exception as e:
        return JsonResponse({
            'error': 'Error al obtener información de límites'
        }, status=500)

@login_required
def simular_transaccion_limites(request):
    """
    API AJAX para simular transacciones y validar límites en tiempo real.
    
    Permite verificar si una transacción propuesta cumple con los límites
    del cliente sin procesarla realmente. Útil para validaciones dinámicas
    en formularios antes de proceder con la transacción real.
    
    Args:
        request (HttpRequest): Petición AJAX con datos de simulación
            - moneda_id: ID de la moneda a simular
            - monto: Monto en la moneda seleccionada
            - tipo_transaccion: 'COMPRA' o 'VENTA'
        
    Returns:
        JsonResponse: Resultado de la simulación
            - valida (bool): Si la transacción es válida según límites
            - monto_guaranies: Monto convertido a guaraníes
            - mensaje: Mensaje descriptivo del resultado
            - error: Mensaje de error si la transacción no es válida
            
    Status Codes:
        - 200: Simulación realizada exitosamente
        - 400: Parámetros faltantes o cliente inactivo
        - 404: Moneda no encontrada
        - 405: Método no permitido (solo POST)
        - 500: Error interno del servidor
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    if not request.user.cliente_activo:
        return JsonResponse({'error': 'No hay cliente activo'}, status=400)
    
    try:
        moneda_id = request.POST.get('moneda_id')
        monto = request.POST.get('monto')
        tipo_transaccion = request.POST.get('tipo_transaccion', '').upper()
        
        if not all([moneda_id, monto, tipo_transaccion]):
            return JsonResponse({
                'error': 'Faltan parámetros requeridos'
            }, status=400)
        
        if tipo_transaccion not in ['COMPRA', 'VENTA']:
            return JsonResponse({
                'error': 'Tipo de transacción inválido'
            }, status=400)
        
        moneda = Moneda.objects.get(id=moneda_id)
        monto_decimal = Decimal(monto)
        
        # Convertir a guaraníes
        monto_guaranies = LimiteService.convertir_a_guaranies(
            int(monto_decimal), moneda, tipo_transaccion, request.user.cliente_activo
        )
        
        # Validar límites
        LimiteService.validar_limite_transaccion(request.user.cliente_activo, monto_guaranies)
        
        # Si llega aquí, la transacción es válida
        return JsonResponse({
            'valida': True,
            'monto_guaranies': monto_guaranies,
            'mensaje': 'La transacción es válida según los límites establecidos'
        })
        
    except Moneda.DoesNotExist:
        return JsonResponse({
            'error': 'Moneda no encontrada'
        }, status=404)
    except ValidationError as e:
        return JsonResponse({
            'valida': False,
            'error': str(e)
        })
    except Exception as e:
        return JsonResponse({
            'error': 'Error interno del servidor'
        }, status=500)

def cancelar_por_timeout(request):
    """
    Vista que maneja la cancelación automática por timeout
    """
    # Verificar si hay una transacción activa en la sesión y cancelarla
    token_data = request.session.get('token_transaccion')
    if token_data:
        try:
            transaccion_id = token_data.get('datos', {}).get('transaccion_id')
            if transaccion_id:
                transaccion = Transaccion.objects.get(id=transaccion_id)
                transaccion.delete()
                messages.warning(request, 'La transacción ha sido cancelada automáticamente por tiempo de espera excedido.')
            else:
                messages.warning(request, 'Tiempo de espera excedido.')
        except Transaccion.DoesNotExist:
            messages.warning(request, 'Tiempo de espera excedido.')
        except Exception:
            messages.warning(request, 'Tiempo de espera excedido.')
        
        # Limpiar datos de sesión
        if 'compra_datos' in request.session:
            del request.session['compra_datos']
        if 'venta_datos' in request.session:
            del request.session['venta_datos']
        if 'token_transaccion' in request.session:
            del request.session['token_transaccion']
    else:
        messages.warning(request, 'Tiempo de espera excedido.')
    
    return redirect('inicio')

# ============================================================================
# GESTIÓN DE RECARGOS
# ============================================================================

@login_required
@permission_required('transacciones.edicion', raise_exception=True)
def editar_recargos(request):
    """
    Vista para la gestión y edición de recargos por medio de pago.
    
    Permite a usuarios con permisos administrativos modificar los porcentajes
    de recargo aplicables a diferentes medios de pago en las transacciones.
    Los recargos se aplican como porcentajes adicionales al monto base.
    
    Validaciones:
        - Usuario debe tener permiso 'transacciones.edicion'
        - Recargos deben estar en rango 0-100%
        - Valores deben ser numéricos enteros
    
    Args:
        request (HttpRequest): Petición HTTP con datos del formulario
        
    Returns:
        HttpResponse: Formulario de edición o redirecciona tras guardar
        
    Template:
        transacciones/editar_recargos.html
        
    Context:
        - form: Formulario base para validaciones
        - recargos: QuerySet con todos los recargos existentes
    """
    from .models import Recargos
    
    if request.method == 'POST':
        # Procesar cada recargo individualmente
        try:
            recargos_actualizados = 0
            for key, value in request.POST.items():
                if key.startswith('recargo_') and value:
                    recargo_id = key.replace('recargo_', '')
                    try:
                        recargo = Recargos.objects.get(id=int(recargo_id))
                        nuevo_valor = int(value)
                        if 0 <= nuevo_valor <= 100:  # Validar rango
                            recargo.recargo = nuevo_valor
                            recargo.save()
                            recargos_actualizados += 1
                        else:
                            messages.error(request, f'El recargo para {recargo.nombre} debe estar entre 0 y 100%.')
                            return redirect('transacciones:editar_recargos')
                    except (Recargos.DoesNotExist, ValueError) as e:
                        messages.error(request, f'Error al actualizar recargo: {str(e)}')
                        return redirect('transacciones:editar_recargos')
            
            if recargos_actualizados > 0:
                messages.success(request, f'Se actualizaron los recargos correctamente.')
            else:
                messages.warning(request, 'No se actualizó ningún recargo.')
            return redirect('monedas:lista_limites')
            
        except Exception as e:
            messages.error(request, f'Error al procesar los recargos: {str(e)}')
            return redirect('transacciones:editar_recargos')
    
    # Obtener todos los recargos para mostrar en el formulario
    recargos = Recargos.objects.all()
    
    # Crear un formulario base para validaciones
    form = RecargoForm()

    return render(request, 'transacciones/editar_recargos.html', {
        'form': form,
        'recargos': recargos
    })


# ============================================================================
# HISTORIAL Y CONSULTA DE TRANSACCIONES
# ============================================================================

@login_required
def historial_transacciones(request, cliente_id=None):
    """
    Vista principal para el historial y consulta de transacciones.
    
    Muestra un listado completo de transacciones con capacidades de filtrado
    avanzado por cliente, usuario, tipo de operación y estado. Si se proporciona
    un cliente_id específico, filtra solo las transacciones de ese cliente.
    
    Filtros disponibles:
        - Búsqueda por nombre/documento de cliente o usuario
        - Tipo de operación (compra/venta)
        - Estado de transacción (pendiente/completada/etc.)
        - Usuario específico que procesó la transacción
    
    Args:
        request (HttpRequest): Petición HTTP con parámetros de filtro
        cliente_id (int, optional): ID específico de cliente para filtrar
        
    Returns:
        HttpResponse: Listado de transacciones filtrado
        
    Template:
        transacciones/historial_transacciones.html
        
    Context:
        - transacciones: QuerySet de transacciones filtradas
        - busqueda: Término de búsqueda aplicado
        - tipo_operacion: Filtro de tipo aplicado
        - estado_filtro: Filtro de estado aplicado
        - cliente_filtrado: Cliente específico si aplica
        - usuario_filtro: Usuario específico si aplica
        - usuarios_cliente: Usuarios asociados al cliente (si aplica)
    """
    # Obtener parámetros de filtrado
    busqueda = request.GET.get('busqueda', '')
    tipo_operacion = request.GET.get('tipo_operacion', '')
    estado_filtro = request.GET.get('estado', '')
    usuario_filtro = request.GET.get('usuario', '')
    
    # Obtener todas las transacciones (o aplicar filtros)
    transacciones = Transaccion.objects.all().order_by('-fecha_hora')
    
    # Si hay un cliente_id, filtrar transacciones solo para ese cliente
    if cliente_id:
        try:
            from clientes.models import Cliente
            cliente = Cliente.objects.get(id=cliente_id)
            transacciones = transacciones.filter(cliente=cliente)
            cliente_filtrado = cliente
            # Obtener usuarios asociados al cliente
            usuarios_cliente = cliente.usuarios.all()
        except Cliente.DoesNotExist:
            messages.error(request, "Cliente no encontrado")
            return redirect('transacciones:historial')
    else:
        cliente_filtrado = None
        usuarios_cliente = None
    
    # Aplicar filtros según parámetros recibidos
    if busqueda and not cliente_filtrado:
        # Buscar por cliente o usuario solo cuando no hay cliente filtrado
        transacciones = transacciones.filter(
            models.Q(cliente__nombre__icontains=busqueda) | 
            models.Q(cliente__docCliente__icontains=busqueda) |
            models.Q(cliente__usuarios__username__icontains=busqueda)
        )
    
    if tipo_operacion:
        transacciones = transacciones.filter(tipo=tipo_operacion)
    
    if estado_filtro:
        transacciones = transacciones.filter(estado__iexact=estado_filtro)
    
    # Filtrar por usuario si se especifica
    if usuario_filtro:
        try:
            usuario_id = int(usuario_filtro)
            transacciones = transacciones.filter(usuario_id=usuario_id)
        except (ValueError, TypeError):
            pass
    
    # Procesar cada transacción para obtener información de tarjetas y calcular montos
    for transaccion in transacciones:
        # Calcular montos de origen y destino
        if transaccion.tipo == 'compra':
            transaccion.monto_origen = int(transaccion.monto * transaccion.moneda.calcular_precio_venta(
                transaccion.cliente.beneficio_segmento
            ))
            transaccion.monto_destino = float(transaccion.monto)
        else:  # venta
            transaccion.monto_origen = float(transaccion.monto)
            transaccion.monto_destino = int(transaccion.monto * transaccion.moneda.calcular_precio_compra(
                transaccion.cliente.beneficio_segmento
            ))
        
        # Obtener información de tarjetas de Stripe para el cliente
        tarjetas_cliente = transaccion.cliente.obtener_tarjetas_stripe()
        
        # Formatear medio de pago (las tarjetas solo pueden ser medio de pago)
        transaccion.medio_pago_formateado = transaccion.medio_pago
        for tarjeta in tarjetas_cliente:
            if tarjeta['id'] == transaccion.medio_pago:
                transaccion.medio_pago_formateado = f"Tarjeta {tarjeta['brand']} **** **** **** {tarjeta['last4']}"
                break
    
    context = {
        'transacciones': transacciones,
        'busqueda': busqueda,
        'tipo_operacion': tipo_operacion,
        'estado_filtro': estado_filtro,
        'cliente_filtrado': cliente_filtrado,
        'usuario_filtro': usuario_filtro,
        'usuarios_cliente': usuarios_cliente
    }
    
    return render(request, 'transacciones/historial_transacciones.html', context)

@login_required
def detalle_transaccion(request, transaccion_id):
    """
    Vista de detalle para una transacción específica.
    
    Muestra información completa y detallada de una transacción individual,
    incluyendo todos los datos relevantes como montos calculados, medios
    de pago/cobro, información del cliente y estado actual.
    
    Cálculos realizados:
        - Para compras: Convierte monto extranjero a guaraníes usando precio de venta
        - Para ventas: Convierte monto extranjero a guaraníes usando precio de compra
        - Aplica beneficios del segmento del cliente
    
    Args:
        request (HttpRequest): Petición HTTP
        transaccion_id (int): ID de la transacción a mostrar
        
    Returns:
        HttpResponse: Página de detalle o redirecciona si no existe
        
    Template:
        transacciones/detalle_transaccion.html
        
    Context:
        - transaccion: Instancia de la transacción
        - monto_origen: Monto en moneda de origen (guaraníes o extranjera)
        - monto_destino: Monto en moneda de destino (extranjera o guaraníes)
    """
    try:
        transaccion = Transaccion.objects.get(id=transaccion_id)
    except Transaccion.DoesNotExist:
        messages.error(request, 'La transacción solicitada no existe.')
        return redirect('transacciones:historial')
    
    # Calcular montos en guaraníes para mostrar
    if transaccion.tipo == 'compra':
        monto_origen = int(transaccion.monto * transaccion.moneda.calcular_precio_venta(
            transaccion.cliente.beneficio_segmento
        ))
        monto_destino = float(transaccion.monto)
    else:  # venta
        monto_origen = float(transaccion.monto)
        monto_destino = int(transaccion.monto * transaccion.moneda.calcular_precio_compra(
            transaccion.cliente.beneficio_segmento
        ))
    
    context = {
        'transaccion': transaccion,
        'monto_origen': monto_origen,
        'monto_destino': monto_destino
    }
    
    return render(request, 'transacciones/detalle_transaccion.html', context)

@login_required
def editar_transaccion(request, transaccion_id):
    """
    Vista para editar transacciones existentes (funcionalidad pendiente).
    
    Actualmente solo permite editar transacciones que se encuentren en estado
    'pendiente'. Para otras transacciones redirecciona al historial del usuario.
    La lógica de edición está pendiente de implementación.
    
    Restricciones:
        - Solo transacciones en estado 'pendiente' pueden ser editadas
        - Otros estados son inmutables por seguridad
    
    Args:
        request (HttpRequest): Petición HTTP
        transaccion_id (int): ID de la transacción a editar
        
    Returns:
        HttpResponse: Redirecciona al historial del usuario
        
    TODO: Implementar lógica completa de edición de transacciones
    """
    try:
        transaccion = Transaccion.objects.get(id=transaccion_id)
        
        # Verificar que la transacción esté pendiente
        if transaccion.estado.lower() != 'pendiente':
            messages.error(request, 'Solo se pueden editar transacciones en estado pendiente.')
            return redirect(f'transacciones:historial?usuario={transaccion.usuario.id}')
            
        # Aquí implementar lógica para editar la transacción
        # Por ahora, solo redireccionar al historial del usuario
        return redirect(f'transacciones:historial?usuario={transaccion.usuario.id}')
        
    except Transaccion.DoesNotExist:
        messages.error(request, 'La transacción solicitada no existe.')
        return redirect('transacciones:historial')