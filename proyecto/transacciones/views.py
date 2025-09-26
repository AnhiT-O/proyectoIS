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

from django.shortcuts import render, redirect, get_object_or_404
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
from datetime import datetime, timedelta
from django.db import models


def generar_token_transaccion(transaccion_id):
    """
    Genera un token único de seguridad para transacciones específicas.
    
    Se utiliza para transacciones con medios de pago que requieren verificación
    adicional como Efectivo o Cheque. El token tiene una validez de 5 minutos.
    
    Args:
        transaccion_id (int): ID de la transacción para la cual generar el token
    
    Returns:
        dict: Diccionario con 'token' (str) y 'datos' (dict) de la transacción
        
    Raises:
        ValueError: Si la transacción no existe
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
    
    # Obtener el medio de pago seleccionado actualmente (si hay uno)
    medio_pago_seleccionado = None
    if compra_datos.get('medio_pago'):
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
        - Creación de registro de transacción en base de datos
        - Generación de token para medios específicos
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
    # Recuperar los datos de la sesión
    try:
        moneda = Moneda.objects.get(id=compra_datos['moneda'])
        monto = Decimal(compra_datos['monto'])
        medio_pago = compra_datos['medio_pago']
        medio_cobro = compra_datos.get('medio_cobro', 'No seleccionado')
    except (Moneda.DoesNotExist, ValueError, KeyError):
        messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
        return redirect('transacciones:compra_monto_moneda')
    
    # Crear la transacción en la base de datos
    try:
        print(f"Intentando crear transacción de compra con usuario: {request.user}")
        transaccion = Transaccion.objects.create(
            cliente=request.user.cliente_activo,
            tipo='compra',
            moneda=moneda,
            monto=monto,
            medio_pago=medio_pago,
            medio_cobro=medio_cobro,
            usuario=request.user
        )
        print(f"Transacción creada con ID: {transaccion.id}")
        # Generar token si el medio de pago es Efectivo o Cheque
        if medio_pago in ['Efectivo', 'Cheque']:
            try:
                token_data = generar_token_transaccion(transaccion.id)
                
                # Guardar el token en la sesión para su posterior uso
                request.session['token_transaccion'] = token_data

                messages.success(request, f'Transacción creada. Token generado: {token_data["token"][:8]}... (válido por 5 minutos)')

            except Exception as e:
                messages.error(request, 'Error al generar token de transacción. Intente nuevamente.')
                return redirect('transacciones:compra_medio_cobro')
        else:
            messages.success(request, 'Transacción creada exitosamente.')
            
    except Exception as e:
        messages.error(request, 'Error al crear la transacción. Intente nuevamente.')
        return redirect('transacciones:compra_medio_cobro')
    
    context = {
        'moneda': moneda,
        'monto': monto,
        'medio_pago': medio_pago,
        'medio_cobro': medio_cobro,
        'cliente_activo': request.user.cliente_activo,
        'transaccion': transaccion,  # Agregar la transacción al contexto
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
    
    Muestra confirmación de que la transacción ha sido procesada
    exitosamente y limpia los datos de sesión relacionados con
    el proceso de compra.
    
    Args:
        request (HttpRequest): Petición HTTP
        
    Returns:
        HttpResponse: Página de éxito
        
    Template:
        transacciones/exito.html
    """
    # Limpiar los datos de la sesión relacionados con la compra
    if 'compra_datos' in request.session:
        del request.session['compra_datos']
    
    return render(request, 'transacciones/exito.html')

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
        medio_descripcion = f"Billetera - {billetera.get_tipo_billetera_display()} ({billetera.telefono})"
        medios_cobro_disponibles.append(medio_descripcion)

    # Obtener el medio de cobro seleccionado actualmente (si hay uno)
    medio_cobro_seleccionado = None
    if venta_datos.get('medio_cobro'):
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
    # Recuperar los datos de la sesión
    try:
        moneda = Moneda.objects.get(id=venta_datos['moneda'])
        monto = Decimal(venta_datos['monto'])
        medio_pago = venta_datos['medio_pago']
        medio_cobro = venta_datos.get('medio_cobro', 'No seleccionado')
    except (Moneda.DoesNotExist, ValueError, KeyError):
        messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
        return redirect('transacciones:venta_monto_moneda')
    
    # Crear la transacción en la base de datos
    try:
        print(f"Intentando crear transacción de venta con usuario: {request.user}")
        transaccion = Transaccion.objects.create(
            cliente=request.user.cliente_activo,
            tipo='venta',
            moneda=moneda,
            monto=monto,
            medio_pago=medio_pago,
            medio_cobro=medio_cobro,
            usuario=request.user
        )
        print(f"Transacción creada con ID: {transaccion.id}")
        
        # Generar token si el medio de pago es Efectivo
        if medio_pago == 'Efectivo':
            try:
                token_data = generar_token_transaccion(transaccion.id)
                
                # Guardar el token en la sesión para su posterior uso
                request.session['token_transaccion'] = token_data
                messages.success(request, f'Transacción creada. Token generado: {token_data["token"][:8]}... (válido por 5 minutos)')

            except Exception as e:
                messages.error(request, 'Error al generar token de transacción. Intente nuevamente.')
                return redirect('transacciones:venta_medio_cobro')
        else:
            messages.success(request, 'Transacción creada exitosamente.')
            
    except Exception as e:
        messages.error(request, 'Error al crear la transacción. Intente nuevamente.')
        return redirect('transacciones:venta_medio_cobro')
    
    context = {
        'moneda': moneda,
        'monto': monto,
        'medio_pago': medio_pago,
        'medio_cobro': medio_cobro,
        'cliente_activo': request.user.cliente_activo,
        'transaccion': transaccion,  # Agregar la transacción al contexto
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
    
    Muestra confirmación de que la transacción de venta ha sido procesada
    exitosamente y limpia los datos de sesión relacionados con
    el proceso de venta.
    
    Args:
        request (HttpRequest): Petición HTTP
        
    Returns:
        HttpResponse: Página de éxito
        
    Template:
        transacciones/exito.html
    """
    # Limpiar los datos de la sesión relacionados con la venta
    if 'venta_datos' in request.session:
        del request.session['venta_datos']

    return render(request, 'transacciones/exito.html')

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
    messages.warning(request, 'La transacción ha sido cancelada por tiempo de espera excedido.')
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
            return redirect('monedas:listar_limites')
            
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