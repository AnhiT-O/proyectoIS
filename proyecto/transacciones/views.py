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
Date: 2025
"""

import logging
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.conf import settings
from monedas.models import Moneda, StockGuaranies
from .forms import SeleccionMonedaMontoForm, VariablesForm
from .models import Transaccion, Recargos, LimiteGlobal, Tauser, calcular_conversion, procesar_pago_stripe, procesar_transaccion, verificar_cambio_cotizacion_sesion, generar_token_transaccion
from .utils_2fa import is_2fa_enabled
from decimal import Decimal
from clientes.models import Cliente
import ast
import stripe
import logging
from datetime import date, timedelta
from django.utils import timezone
from django.db import models
import stripe

# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

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
    transacciones_pasadas = Transaccion.objects.filter(usuario=request.user, estado='Pendiente')
    if transacciones_pasadas:
        for t in transacciones_pasadas:
            if t.fecha_hora < timezone.now() - timedelta(minutes=5):
                t.estado = 'Cancelada'
                t.razon = 'Expira el tiempo para confirmar la transacción'
                t.save()
    if request.session.get('transaccion_id'):
        t = Transaccion.objects.filter(id=request.session.get('transaccion_id')).first()
        t.estado = 'Cancelada'
        t.razon = 'Usuario sale del proceso de compra'
        t.save()
        del request.session['transaccion_id']
    if request.method == 'POST':
        form = SeleccionMonedaMontoForm(request.POST)
        if form.is_valid():
            moneda = form.cleaned_data['moneda']
            monto = form.cleaned_data['monto_decimal']
            cliente_activo = request.user.cliente_activo
            
            # Si pasa las validaciones, guardar los datos en la sesión
            request.session['compra_datos'] = {
                'moneda': moneda.id,
                'monto': str(monto),  # Convertir Decimal a string para serialización
                'paso_actual': 2
            }
            # Guardar precios iniciales en la sesión
            precios = moneda.get_precios_cliente(cliente_activo)
            request.session['precio_venta_inicial'] = precios['precio_venta']
            # Redireccionar al siguiente paso sin parámetros en la URL
            return redirect('transacciones:compra_medio_pago')
    else:
        # Verificar si el usuario tiene un cliente activo
        if not request.user.cliente_activo:
            messages.error(request, 'Debes tener un cliente activo para realizar compras.')
            return redirect('inicio')
        if request.user.cliente_activo.ultimo_consumo:
            if request.user.cliente_activo.ultimo_consumo != date.today():
                request.user.cliente_activo.consumo_diario = 0
                request.user.cliente_activo.save()
            if request.user.cliente_activo.ultimo_consumo.month != date.today().month:
                request.user.cliente_activo.consumo_mensual = 0
                request.user.cliente_activo.save()

        # Si cliente_activo.ultimo_consumo es None, no hacemos nada y los consumos
        # se mantienen en 0 (que es el valor inicial/correcto para un nuevo día/mes).
        form = SeleccionMonedaMontoForm()
    
    context = {
        'form': form,
        'disponible_diario': (LimiteGlobal.objects.first().limite_diario - request.user.cliente_activo.consumo_diario),
        'disponible_mensual': (LimiteGlobal.objects.first().limite_mensual - request.user.cliente_activo.consumo_mensual),
        'paso_actual': 1,
        'titulo': 'Selección de Moneda y Monto',
        'tipo_transaccion': 'compra'
    }
    
    return render(request, 'transacciones/seleccion_moneda_monto.html', context)

@login_required
def compra_medio_pago(request):
    """
    Segundo paso del proceso de compra: selección del medio de pago.
    
    Permite al usuario seleccionar cómo va a pagar por la moneda extranjera.
    Las opciones incluyen efectivo, billetera electrónica, transferencia
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
        'Transferencia Bancaria'
    ]
    # Agregar billeteras electrónicas como medio de pago si hay recargos configurados
    recargos_billetera = Recargos.objects.filter(medio='Billetera Electrónica')
    for recargo in recargos_billetera:
        medios_pago_disponibles.append(recargo.marca)
    # Verificar si el cliente tiene tarjetas de crédito activas en Stripe
    if request.user.cliente_activo.tiene_tarjetas_activas():
        for tarjeta in request.user.cliente_activo.obtener_tarjetas_stripe():
            medios_pago_disponibles.append(tarjeta)
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
        'titulo_paso': 'Selección de Medio de Cobro',
        'tipo_transaccion': 'compra'
    }
    
    return render(request, 'transacciones/seleccion_medio_cobro.html', context)

@login_required
def compra_confirmacion(request):
    """
    Cuarto paso del proceso de compra: confirmación y creación de transacción.
    
    Muestra un resumen completo de la transacción y procede a crearla en
    la base de datos. Para medios de pago como Efectivo o Transferencia,
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

    if request.method == 'POST':
        accion = request.POST.get('accion')
        action = request.POST.get('action')
        if accion == 'confirmar':
            cambios = verificar_cambio_cotizacion_sesion(request, 'compra')
            if cambios and cambios.get('hay_cambios'):
                transaccion = Transaccion.objects.filter(id=request.session.get('transaccion_id')).first()
                datos_transaccion = calcular_conversion(transaccion.monto, transaccion.moneda, 'compra', transaccion.medio_pago, transaccion.medio_cobro, request.user.cliente_activo.segmento)
                transaccion.precio_base = datos_transaccion['precio_base']
                transaccion.cotizacion = datos_transaccion['cotizacion']
                transaccion.beneficio_segmento = datos_transaccion['beneficio_segmento']
                transaccion.porc_beneficio_segmento = datos_transaccion['porc_beneficio_segmento']
                transaccion.recargo_pago = datos_transaccion['monto_recargo_pago']
                transaccion.porc_recargo_pago = datos_transaccion['porc_recargo_pago']
                transaccion.recargo_cobro = datos_transaccion['monto_recargo_cobro']
                transaccion.porc_recargo_cobro = datos_transaccion['porc_recargo_cobro']
                transaccion.redondeo_efectivo_monto = datos_transaccion['redondeo_efectivo_monto']
                transaccion.redondeo_efectivo_precio_final = datos_transaccion['redondeo_efectivo_precio_final']
                transaccion.monto_original = datos_transaccion['monto_original']
                transaccion.monto = datos_transaccion['monto']
                transaccion.precio_final = datos_transaccion['precio_final']
                transaccion.save()
                context = {
                    'cambios': cambios,
                    'transaccion': transaccion,
                    'paso_actual': 4,
                    'titulo_paso': 'Confirmación de Compra'
                }
                
                return render(request, 'transacciones/confirmacion.html', context)
            return redirect('transacciones:compra_exito')
        elif accion == 'cancelar':
            messages.info(request, 'Has cancelado la transacción.')
            t = Transaccion.objects.filter(id=request.session.get('transaccion_id')).first()
            if t:
                t.estado = 'Cancelada'
                t.razon = 'Usuario canceló la transacción en el formulario'
                t.save()
                # Limpiar datos de sesión
            if 'compra_datos' in request.session:
                del request.session['compra_datos']
            if 'precio_venta_inicial' in request.session:
                del request.session['precio_venta_inicial']
            if 'transaccion_id' in request.session:
                del request.session['transaccion_id']
            return redirect('inicio')
        elif action == 'aceptar':
            transaccion = Transaccion.objects.get(id=request.session.get('transaccion_id'))
            precios_actuales = transaccion.moneda.get_precios_cliente(request.user.cliente_activo)
            request.session['precio_venta_inicial'] = precios_actuales['precio_venta']
            messages.success(request, 'Precios actualizados. Continuando con la transacción.')
            context = {
                'transaccion': transaccion,
                'paso_actual': 4,
                'titulo_paso': 'Confirmación de Compra',
                'enable_2fa': is_2fa_enabled(),
                'user_email': request.user.email,
                'has_email': bool(request.user.email)
            }
            
            return render(request, 'transacciones/confirmacion.html', context)
        elif action == 'cancelar':
            t = Transaccion.objects.filter(id=request.session.get('transaccion_id')).first()
            if t:
                t.estado = 'Cancelada'
                t.razon = 'Usuario cancela debido a cambios de cotización'
                t.save()
                # Limpiar datos de sesión
            if 'compra_datos' in request.session:
                del request.session['compra_datos']
            if 'precio_venta_inicial' in request.session:
                del request.session['precio_venta_inicial']
            if 'transaccion_id' in request.session:
                del request.session['transaccion_id']
            messages.info(request, 'Transacción cancelada debido a cambios en la cotización.')
            return redirect('inicio')
    else:   
        # Recuperar los datos de la sesión
        try:
            moneda = Moneda.objects.get(id=compra_datos['moneda'])
            monto = Decimal(compra_datos['monto'])
            medio_pago = compra_datos['medio_pago']
            medio_cobro = compra_datos['medio_cobro']
        except (Moneda.DoesNotExist, ValueError, KeyError):
            messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
            return redirect('transacciones:compra_monto_moneda')
        if request.session.get('transaccion_id'):
            transaccion = Transaccion.objects.filter(id=request.session.get('transaccion_id')).first()
            context = {
            'transaccion': transaccion,
            'paso_actual': 4,
            'titulo_paso': 'Confirmación de Compra'
            }
            return render(request, 'transacciones/confirmacion.html', context)
        
        # Crear la transacción en la base de datos
        try:
            if medio_pago.startswith('{'):
                medio_pago_dict = ast.literal_eval(medio_pago)
                str_medio_pago = f'Tarjeta de Crédito (**** **** **** {medio_pago_dict["last4"]})'
            else:
                str_medio_pago = medio_pago
            datos_transaccion = calcular_conversion(monto, moneda, 'compra', medio_pago, medio_cobro, request.user.cliente_activo.segmento)
            if datos_transaccion['precio_final'] > (LimiteGlobal.objects.first().limite_diario - request.user.cliente_activo.consumo_diario) or datos_transaccion['precio_final'] > (LimiteGlobal.objects.first().limite_mensual - request.user.cliente_activo.consumo_mensual):
                messages.warning(request, 'El monto final excede sus límites diarios o mensuales. Reinicie el proceso con un monto menor.')
                return redirect('transacciones:compra_monto_moneda')
            transaccion = Transaccion.objects.create(
                cliente=request.user.cliente_activo,
                tipo='compra',
                moneda=moneda,
                monto=datos_transaccion['monto'],
                monto_original=datos_transaccion['monto_original'],
                cotizacion=datos_transaccion['cotizacion'],
                precio_base=datos_transaccion['precio_base'],
                beneficio_segmento=datos_transaccion['beneficio_segmento'],
                porc_beneficio_segmento=datos_transaccion['porc_beneficio_segmento'],
                recargo_pago=datos_transaccion['monto_recargo_pago'],
                porc_recargo_pago=datos_transaccion['porc_recargo_pago'],
                recargo_cobro=datos_transaccion['monto_recargo_cobro'],
                porc_recargo_cobro=datos_transaccion['porc_recargo_cobro'],
                redondeo_efectivo_monto=datos_transaccion['redondeo_efectivo_monto'],
                redondeo_efectivo_precio_final=datos_transaccion['redondeo_efectivo_precio_final'],
                precio_final=datos_transaccion['precio_final'],
                medio_pago=str_medio_pago,
                medio_cobro=medio_cobro,
                usuario=request.user
            )
            request.session['transaccion_id'] = transaccion.id
                
        except Exception as e:
            messages.error(request, 'Error al crear la transacción. Intente nuevamente.')
            print(e)
            return redirect('transacciones:compra_medio_cobro')
        
        cambios = verificar_cambio_cotizacion_sesion(request, 'compra')
        if cambios and cambios.get('hay_cambios'):
            context = {
                'cambios': cambios,
                'transaccion': transaccion,
                'paso_actual': 4,
                'titulo_paso': 'Confirmación de Compra',
                'enable_2fa': is_2fa_enabled(),
                'user_email': request.user.email,
                'has_email': bool(request.user.email)
            }
            
            return render(request, 'transacciones/confirmacion.html', context)
        
        context = {
            'transaccion': transaccion,
            'paso_actual': 4,
            'titulo_paso': 'Confirmación de Compra',
            'enable_2fa': is_2fa_enabled(),
            'user_email': request.user.email,
            'has_email': bool(request.user.email)
        }
        
        return render(request, 'transacciones/confirmacion.html', context)


@login_required
def compra_exito(request, token=None):
    """
    Página final del proceso de compra: mensaje de éxito.
    
    Verifica si hay cambios en la cotización antes de finalizar la transacción.
    Si hay cambios, muestra el modal de confirmación. Si no hay cambios o el usuario
    acepta los nuevos precios, muestra confirmación de éxito.
    
    Args:
        request (HttpRequest): Petición HTTP
        token (str, optional): Token de la transacción para retorno de la pasarela
        
    Returns:
        HttpResponse: Página de éxito o modal de cambio de cotización
        
    Template:
        transacciones/exito.html o transacciones/cotizacion_cambiada.html
    """
    # Verificar que el usuario tenga un cliente activo
    if not request.user.cliente_activo:
        messages.error(request, 'Debe tener un cliente activo seleccionado para continuar.')
        return redirect('inicio')

    transaccion = None
    # Si viene token desde la pasarela, buscar la transacción por token
    if token:
        try:
            transaccion = Transaccion.objects.get(token=token)
            
            # Si viene desde la pasarela, validar los datos del pago
            if transaccion.estado in ['Pendiente', 'Iniciada'] and request.GET.get('estado') == 'exito':
                # Datos enviados por la pasarela
                try:
                    monto_pago = float(request.GET.get('monto', 0))
                    cuenta_pago = request.GET.get('nro_cuenta')
                    banco_pago = request.GET.get('banco')
                    
                    # Verificación de cuenta/billetera
                    CUENTAS_GLOBAL_EXCHANGE = {
                        'Transferencia Bancaria': 'SUDAMERIS-123456',
                        'Tigo Money': 'TIGO-0981000001-1010101',
                        'Billetera Personal': 'PERSONAL-0982000002-2020202',
                        'Zimple': 'ZIMPLE-0983000003-3030303'
                    }
                    # Mensajes de debug para ver los valores reales
                    # Mensajes de debug para ver los valores reales
                    messages.info(request, f"Pago recibido: monto_pago={monto_pago}, cuenta_pago={cuenta_pago}, banco_pago={banco_pago}")
                    messages.info(request, f"Esperado: precio_final={transaccion.precio_final}, cuenta_esperada={CUENTAS_GLOBAL_EXCHANGE.get(transaccion.medio_pago, '')}")


                    # Verificación del monto
                    monto_valido = monto_pago >= float(transaccion.precio_final)
                    
                    if transaccion.medio_pago == "Transferencia Bancaria":
                        # Para transferencias, el CUENTAS_GLOBAL_EXCHANGE ya tiene banco+cuenta
                        cuenta_valida = f"{banco_pago}-{cuenta_pago}" == CUENTAS_GLOBAL_EXCHANGE.get(transaccion.medio_pago)
                    else:
                        # Para billeteras, la cuenta completa ya incluye el prefijo del banco
                        cuenta_valida = cuenta_pago == CUENTAS_GLOBAL_EXCHANGE.get(transaccion.medio_pago)

                
                    if monto_valido and cuenta_valida:
                        transaccion.estado = 'Confirmada'
                        transaccion.fecha_hora = timezone.now()
                        transaccion.save()
                        messages.success(request, 'Pago confirmado exitosamente')
                    else:
                        transaccion.estado = 'Pendiente'
                        transaccion.razon = f'Error en validación: monto={monto_valido}, cuenta={cuenta_valida}'
                        transaccion.save()
                        # Restaurar datos en sesión para volver a confirmación
                        request.session['compra_datos'] = {
                            'moneda': transaccion.moneda.id,
                            'monto': str(transaccion.monto),
                            'medio_pago': transaccion.medio_pago,
                            'medio_cobro': transaccion.medio_cobro,
                            'paso_actual': 4
                        }
                        request.session['transaccion_id'] = transaccion.id
                        messages.error(request, 'Error en la validación del pago. Por favor, verifique los datos e intente nuevamente.')
                        return redirect('transacciones:compra_confirmacion')
                        
                except (ValueError, TypeError, AttributeError) as e:
                    transaccion.estado = 'Cancelada'
                    transaccion.razon = f'Error procesando datos del pago: {str(e)}'
                    transaccion.save()
                    messages.error(request, 'Error al procesar los datos del pago')
                    return redirect('inicio')
                    
            elif request.GET.get('estado') == 'error':
                transaccion.estado = 'Cancelada'
                transaccion.razon = 'Error reportado por la pasarela de pago'
                transaccion.save()
                messages.error(request, 'Error al procesar el pago')
                
        except Transaccion.DoesNotExist:
            messages.error(request, 'Token de transacción inválido.')
            return redirect('inicio')
    else:
        # Flujo normal: buscar por sesión
        try:
            idt = request.session.get('transaccion_id')
            transaccion = Transaccion.objects.get(id=idt)
        except:
            return redirect('inicio')

    compra_datos = request.session.get('compra_datos')
    if not compra_datos:
        messages.error(request, 'Debe completar el cuarto paso antes de continuar.')
        return redirect('transacciones:compra_medio_cobro')
    try:
        medio_pago = compra_datos['medio_pago']
    except (Moneda.DoesNotExist, ValueError, KeyError):
        messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
        return redirect('transacciones:compra_monto_moneda')

    if transaccion.token is None:
        if medio_pago.startswith('{'):
            medio_pago_dict = ast.literal_eval(medio_pago)
            pago = procesar_pago_stripe(transaccion, medio_pago_dict["id"])
            if pago['success']:
                messages.success(request, 'Pago con tarjeta de crédito procesado exitosamente.')
                procesar_transaccion(transaccion)
                generar_token_transaccion(transaccion)
            else:
                transaccion.estado = 'Cancelada'
                transaccion.razon = 'Error en el procesamiento del pago con tarjeta de crédito'
                transaccion.save()
                messages.error(request, 'Error al procesar el pago con tarjeta de crédito. Intente nuevamente.')
                return redirect('transacciones:compra_monto_moneda')
        else:
            try:
                generar_token_transaccion(transaccion)
                transaccion.fecha_hora = timezone.now()
                transaccion.save()
            except Exception as e:
                messages.error(request, 'Error al generar token de transacción. Intente nuevamente.')
                return redirect('transacciones:compra_medio_cobro')

    # Limpiar sesión
    request.session.pop('transaccion_id', None)

    context = {
        'transaccion': transaccion
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
    transacciones_pasadas = Transaccion.objects.filter(usuario=request.user, estado='Pendiente')
    if transacciones_pasadas:
        for t in transacciones_pasadas:
            if t.fecha_hora < timezone.now() - timedelta(minutes=5):
                t.estado = 'Cancelada'
                t.razon = 'Expira el tiempo para confirmar la transacción'
                t.save()
    if request.session.get('transaccion_id'):
        t = Transaccion.objects.filter(id=request.session.get('transaccion_id')).first()
        t.estado = 'Cancelada'
        t.razon = 'Usuario sale del proceso de compra'
        t.save()
        del request.session['transaccion_id']
    if request.method == 'POST':
        form = SeleccionMonedaMontoForm(request.POST)
        if form.is_valid():
            moneda = form.cleaned_data['moneda']
            monto = form.cleaned_data['monto_decimal']
            cliente_activo = request.user.cliente_activo
            # Si pasa las validaciones, guardar los datos en la sesión
            request.session['venta_datos'] = {
                'moneda': moneda.id,
                'monto': str(monto),  # Convertir Decimal a string para serialización
                'paso_actual': 2
            }
            # Guardar precios iniciales en la sesión
            precios = moneda.get_precios_cliente(cliente_activo)
            request.session['precio_compra_inicial'] = precios['precio_compra']
            # Redireccionar al siguiente paso sin parámetros en la URL
            return redirect('transacciones:venta_medio_pago')
    else:
        # Verificar si el usuario tiene un cliente activo
        if not request.user.cliente_activo:
            messages.error(request, 'Debes tener un cliente activo para realizar compras.')
            return redirect('inicio')
         
        # 1. Verificar si el cliente tiene un último consumo registrado
        if request.user.cliente_activo.ultimo_consumo:
            if request.user.cliente_activo.ultimo_consumo != date.today():
                request.user.cliente_activo.consumo_diario = 0
                request.user.cliente_activo.save()
            if request.user.cliente_activo.ultimo_consumo.month != date.today().month:
                request.user.cliente_activo.consumo_mensual = 0
                request.user.cliente_activo.save()
        # Si cliente_activo.ultimo_consumo es None, no hacemos nada y los consumos
        # se mantienen en 0 (que es el valor inicial/correcto para un nuevo día/mes).
        form = SeleccionMonedaMontoForm()
    
    context = {
        'form': form,
        'disponible_diario': (LimiteGlobal.objects.first().limite_diario - request.user.cliente_activo.consumo_diario),
        'disponible_mensual': (LimiteGlobal.objects.first().limite_mensual - request.user.cliente_activo.consumo_mensual),
        'paso_actual': 1,
        'titulo': 'Selección de Moneda y Monto',
        'tipo_transaccion': 'venta'
    }

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

    if request.method == 'POST':
        accion = request.POST.get('accion')
        action = request.POST.get('action')
        if accion == 'confirmar':
            cambios = verificar_cambio_cotizacion_sesion(request, 'venta')
            if cambios and cambios.get('hay_cambios'):
                transaccion = Transaccion.objects.filter(id=request.session.get('transaccion_id')).first()
                datos_transaccion = calcular_conversion(transaccion.monto, transaccion.moneda, 'venta', transaccion.medio_pago, transaccion.medio_cobro, request.user.cliente_activo.segmento)
                transaccion.precio_base = datos_transaccion['precio_base']
                transaccion.cotizacion = datos_transaccion['cotizacion']
                transaccion.beneficio_segmento = datos_transaccion['beneficio_segmento']
                transaccion.porc_beneficio_segmento = datos_transaccion['porc_beneficio_segmento']
                transaccion.recargo_pago = datos_transaccion['monto_recargo_pago']
                transaccion.porc_recargo_pago = datos_transaccion['porc_recargo_pago']
                transaccion.recargo_cobro = datos_transaccion['monto_recargo_cobro']
                transaccion.porc_recargo_cobro = datos_transaccion['porc_recargo_cobro']
                transaccion.redondeo_efectivo_monto = datos_transaccion['redondeo_efectivo_monto']
                transaccion.redondeo_efectivo_precio_final = datos_transaccion['redondeo_efectivo_precio_final']
                transaccion.monto_original = datos_transaccion['monto_original']
                transaccion.monto = datos_transaccion['monto']
                transaccion.precio_final = datos_transaccion['precio_final']
                transaccion.save()
                context = {
                    'cambios': cambios,
                    'transaccion': Transaccion.objects.get(id=request.session.get('transaccion_id')),
                    'paso_actual': 4,
                    'titulo_paso': 'Confirmación de Venta',
                    'enable_2fa': is_2fa_enabled(),
                    'user_email': request.user.email,
                    'has_email': bool(request.user.email)
                }
                
                return render(request, 'transacciones/confirmacion.html', context)
            return redirect('transacciones:venta_exito')
        elif accion == 'cancelar':
            messages.info(request, 'Has cancelado la transacción.')
            t = Transaccion.objects.filter(id=request.session.get('transaccion_id')).first()
            if t:
                t.estado = 'Cancelada'
                t.razon = 'Usuario canceló la transacción en el formulario'
                t.save()
                # Limpiar datos de sesión
            if 'venta_datos' in request.session:
                del request.session['venta_datos']
            if 'precio_compra_inicial' in request.session:
                del request.session['precio_compra_inicial']
            if 'transaccion_id' in request.session:
                del request.session['transaccion_id']
            return redirect('inicio')
        elif action == 'aceptar':
            transaccion = Transaccion.objects.filter(id=request.session.get('transaccion_id')).first()
            precios_actuales = transaccion.moneda.get_precios_cliente(request.user.cliente_activo)
            request.session['precio_compra_inicial'] = precios_actuales['precio_compra']
            messages.success(request, 'Precios actualizados. Continuando con la transacción.')
            context = {
                'transaccion': transaccion,
                'paso_actual': 4,
                'titulo_paso': 'Confirmación de Venta',
                'enable_2fa': is_2fa_enabled(),
                'user_email': request.user.email,
                'has_email': bool(request.user.email)
            }
            
            return render(request, 'transacciones/confirmacion.html', context)
        elif action == 'cancelar':
            t = Transaccion.objects.filter(id=request.session.get('transaccion_id')).first()
            if t:
                t.estado = 'Cancelada'
                t.razon = 'Usuario cancela debido a cambios de cotización'
                t.save()
                # Limpiar datos de sesión
            if 'venta_datos' in request.session:
                del request.session['venta_datos']
            if 'precio_compra_inicial' in request.session:
                del request.session['precio_compra_inicial']
            if 'transaccion_id' in request.session:
                del request.session['transaccion_id']
            messages.info(request, 'Transacción cancelada debido a cambios en la cotización.')
            return redirect('inicio')
    else:
        # Recuperar los datos de la sesión
        try:
            moneda = Moneda.objects.get(id=venta_datos['moneda'])
            monto = Decimal(venta_datos['monto'])
            medio_pago = venta_datos['medio_pago']
            medio_cobro = venta_datos['medio_cobro']
        except (Moneda.DoesNotExist, ValueError, KeyError):
            messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
            return redirect('transacciones:venta_monto_moneda')
        if request.session.get('transaccion_id'):
            transaccion = Transaccion.objects.filter(id=request.session.get('transaccion_id')).first()
            context = {
            'transaccion': transaccion,
            'paso_actual': 4,
            'titulo_paso': 'Confirmación de Venta',
            'enable_2fa': is_2fa_enabled(),
            'user_email': request.user.email,
            'has_email': bool(request.user.email)
            }
            return render(request, 'transacciones/confirmacion.html', context)
    
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
                
            datos_transaccion = calcular_conversion(monto, moneda, 'venta', medio_pago, medio_cobro, request.user.cliente_activo.segmento)
            if datos_transaccion['precio_final'] > (LimiteGlobal.objects.first().limite_diario - request.user.cliente_activo.consumo_diario) or datos_transaccion['precio_final'] > (LimiteGlobal.objects.first().limite_mensual - request.user.cliente_activo.consumo_mensual):
                messages.warning(request, 'El monto final excede sus límites diarios o mensuales. Reinicie el proceso con un monto menor.')
                return redirect('transacciones:venta_monto_moneda')
            if str_medio_cobro != 'Efectivo':
                if datos_transaccion['precio_final'] > StockGuaranies.objects.first().cantidad:
                    messages.warning(request, 'El monto a recibir excede la disponibilidad actual de guaraníes en el sistema. Reinicie el proceso con un monto menor o diferente medio de cobro.')
                    return redirect('transacciones:venta_monto_moneda')
            transaccion = Transaccion.objects.create(
                cliente=request.user.cliente_activo,
                tipo='venta',
                moneda=moneda,
                monto=datos_transaccion['monto'],
                monto_original=datos_transaccion['monto_original'],
                cotizacion=datos_transaccion['cotizacion'],
                precio_base=datos_transaccion['precio_base'],
                beneficio_segmento=datos_transaccion['beneficio_segmento'],
                porc_beneficio_segmento=datos_transaccion['porc_beneficio_segmento'],
                recargo_pago=datos_transaccion['monto_recargo_pago'],
                porc_recargo_pago=datos_transaccion['porc_recargo_pago'],
                recargo_cobro=datos_transaccion['monto_recargo_cobro'],
                porc_recargo_cobro=datos_transaccion['porc_recargo_cobro'],
                redondeo_efectivo_monto=datos_transaccion['redondeo_efectivo_monto'],
                redondeo_efectivo_precio_final=datos_transaccion['redondeo_efectivo_precio_final'],
                precio_final=datos_transaccion['precio_final'],
                medio_pago=str_medio_pago,
                medio_cobro=str_medio_cobro,
                usuario=request.user
            )
            request.session['transaccion_id'] = transaccion.id
                
        except Exception as e:
            messages.error(request, 'Error al crear la transacción. Intente nuevamente.')
            return redirect('transacciones:venta_medio_cobro')
        
        cambios = verificar_cambio_cotizacion_sesion(request, 'venta')
        if cambios and cambios.get('hay_cambios'):
            transaccion = Transaccion.objects.filter(id=request.session.get('transaccion_id')).first()
            context = {
                'cambios': cambios,
                'transaccion': transaccion,
                'paso_actual': 4,
                'titulo_paso': 'Confirmación de Venta',
                'enable_2fa': is_2fa_enabled(),
                'user_email': request.user.email,
                'has_email': bool(request.user.email)
            }
            
            return render(request, 'transacciones/confirmacion.html', context)
        
        context = {
            'transaccion': transaccion,
            'paso_actual': 4,
            'titulo_paso': 'Confirmación de Venta',
            'enable_2fa': is_2fa_enabled(),
            'user_email': request.user.email,
            'has_email': bool(request.user.email)
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
    try:
        idt = request.session.get('transaccion_id')
        transaccion = Transaccion.objects.get(id=idt)
    except:
        return redirect('inicio')

    venta_datos = request.session.get('venta_datos')
    if not venta_datos:
        messages.error(request, 'Debe completar el cuarto paso antes de continuar.')
        return redirect('transacciones:venta_medio_cobro')
    try:
        medio_pago = venta_datos['medio_pago']
        medio_cobro = venta_datos.get('medio_cobro')
    except (Moneda.DoesNotExist, ValueError, KeyError):
        messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
        return redirect('transacciones:venta_monto_moneda')
    
    if transaccion.token is None:
        if medio_pago.startswith('{'):
            medio_pago_dict = ast.literal_eval(medio_pago)
            if procesar_pago_stripe(transaccion, medio_pago_dict["id"])['success']:
                messages.success(request, 'Pago con tarjeta de crédito procesado exitosamente.')
                procesar_transaccion(transaccion)
                if medio_cobro == 'Efectivo':
                    generar_token_transaccion(transaccion)
            else:
                transaccion.estado = 'Cancelada'
                transaccion.razon = 'Error en la transacción automática de venta'
                transaccion.save()
                messages.error(request, 'Hubo un error de pago o de cobro automático. Intente nuevamente.')
                return redirect('transacciones:venta_monto_moneda')
        else:
            try:
                generar_token_transaccion(transaccion)
                transaccion.fecha_hora = timezone.now()
                transaccion.save()
            except Exception as e:
                messages.error(request, 'Error al generar token de transacción. Intente nuevamente.')
                return redirect('transacciones:venta_medio_cobro')
            
    del request.session['transaccion_id']
    context = {
        'transaccion': transaccion
    }
    
    return render(request, 'transacciones/exito.html', context)

# ============================================================================
# HISTORIAL Y CONSULTA DE TRANSACCIONES
# ============================================================================

@login_required
def historial_transacciones(request, cliente_id):
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
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        transacciones = Transaccion.objects.filter(cliente=cliente).order_by('-fecha_hora')
    except Cliente.DoesNotExist:
        messages.error(request, "Cliente no encontrado")
        return redirect('transacciones:historial')
    if not request.user.clientes_operados.filter(id=cliente.id).exists():
        messages.error(request, "No tienes permiso para ver el historial de este cliente.")
        return redirect('inicio')
    transacciones_pasadas = Transaccion.objects.filter(cliente=cliente, estado='Pendiente')
    if transacciones_pasadas:
        for t in transacciones_pasadas:
            if t.fecha_hora < timezone.now() - timedelta(minutes=5):
                t.estado = 'Cancelada'
                t.razon = 'Expira el tiempo para confirmar la transacción'
                t.save()
    # Obtener parámetros de filtrado
    busqueda = request.GET.get('busqueda', '')
    tipo_operacion = request.GET.get('tipo_operacion', '')
    estado_filtro = request.GET.get('estado', '')
    usuario_filtro = request.GET.get('usuario', '')
    
    # Aplicar filtros según parámetros recibidos
    if busqueda:
        # Buscar por cliente o usuario solo cuando no hay cliente filtrado
        transacciones = transacciones.filter(
            models.Q(cliente__nombre__icontains=busqueda) | 
            models.Q(cliente__numero_documento__icontains=busqueda) |
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
    
    context = {
        'transacciones': transacciones,
        'busqueda': busqueda,
        'tipo_operacion': tipo_operacion,
        'estado_filtro': estado_filtro,
        'usuario_filtro': usuario_filtro,
        'cliente_filtrado': cliente,
        'usuarios_cliente': cliente.usuarios.all(),
    }
    
    return render(request, 'transacciones/historial_transacciones.html', context)

@login_required
def detalle_historial(request, transaccion_id):
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
    transacciones_pasadas = Transaccion.objects.filter(cliente=transaccion.cliente, estado='Pendiente')
    if transacciones_pasadas:
        for t in transacciones_pasadas:
            if t.fecha_hora < timezone.now() - timedelta(minutes=5):
                t.estado = 'Cancelada'
                t.razon = 'Expira el tiempo para confirmar la transacción'
                t.save()
    if transaccion.cliente not in request.user.clientes_operados.all() and not request.user.has_perm('transacciones.visualizacion'):
        messages.error(request, "No tienes permiso para ver el historial de este cliente.")
        return redirect('inicio')
    
    context = {
        'transaccion': transaccion,
    }
    
    return render(request, 'transacciones/detalle_historial.html', context)

@login_required
@permission_required('transacciones.edicion', raise_exception=True)
def ver_variables(request):
    """
    Vista para ver variables de gestión de transacciones.
    """
    context = {
        'limites': LimiteGlobal.objects.first(),
        'recargos': Recargos.objects.all()
    }
    return render(request, 'transacciones/ver_variables.html', context)

@login_required
@permission_required('transacciones.edicion', raise_exception=True)
def editar_variables(request):
    """
    Vista para editar variables de gestión de transacciones.
    """
    if request.method == 'POST':
        form = VariablesForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Variables actualizadas correctamente.')
            return redirect('transacciones:ver_variables')
    else:
        form = VariablesForm()

    context = {
        'form': form
    }
    return render(request, 'transacciones/editar_variables.html', context)

@login_required
@permission_required('transacciones.revision', raise_exception=True)
def revisar_tausers(request):
    """
    Vista para revisar la información de los TAUsers.
    
    Muestra un listado de todos los TAUsers del sistema con su información básica
    incluyendo puerto, estado de activación (detectado dinámicamente) y opciones de acción.
    
    Funcionalidades:
        - Listado completo de TAUsers
        - Búsqueda por puerto
        - Filtrado por estado (activo/inactivo) detectado automáticamente
        - Estadísticas de TAUsers activos e inactivos
        - Opción de ver detalles de cada TAUser
    
    Args:
        request (HttpRequest): Petición HTTP con parámetros de filtro opcionales
        
    Returns:
        HttpResponse: Renderiza listado de TAUsers
        
    Template:
        transacciones/tausers_lista.html
        
    Context:
        - tausers: Lista de TAUsers con estado detectado dinámicamente
        - busqueda: Término de búsqueda aplicado
        - tausers_activos: Cantidad de TAUsers activos
        - tausers_inactivos: Cantidad de TAUsers inactivos
        - total_tausers_sistema: Total de TAUsers en el sistema
        - filtro_estado: Estado seleccionado para filtrar
    """
    # Obtener todos los TAUsers
    todos_los_tausers = Tauser.objects.all()
    tausers_query = todos_los_tausers
    
    # Manejar búsqueda por puerto
    busqueda = request.GET.get('busqueda', '').strip()
    if busqueda:
        tausers_query = tausers_query.filter(puerto__icontains=busqueda)
    
    # Ordenar por puerto
    tausers_query = tausers_query.order_by('puerto')
    
    # Obtener filtro de estado
    filtro_estado = request.GET.get('estado', '')
    
    # Convertir QuerySet a lista y agregar estado dinámico
    tausers_con_estado = []
    tausers_activos_count = 0
    tausers_inactivos_count = 0
    
    for tauser in tausers_query:
        # Detectar estado dinámicamente
        esta_activo = tauser.esta_activo()
        
        # Aplicar filtro de estado si se especifica
        if filtro_estado == 'activo' and not esta_activo:
            continue
        elif filtro_estado == 'inactivo' and esta_activo:
            continue
        
        # Agregar el tauser con su estado detectado
        tauser.activo = esta_activo  # Agregar atributo temporal
        tausers_con_estado.append(tauser)
        
        # Contar para estadísticas
        if esta_activo:
            tausers_activos_count += 1
        else:
            tausers_inactivos_count += 1
    
    # Total de TAUsers en el sistema (sin filtrar)
    total_tausers_sistema = todos_los_tausers.count()
    
    context = {
        'tausers': tausers_con_estado,
        'tausers_activos': tausers_activos_count,
        'tausers_inactivos': tausers_inactivos_count,
        'busqueda': busqueda,
        'filtro_estado': filtro_estado,
        'total_tausers_sistema': total_tausers_sistema,
    }
    return render(request, 'transacciones/tausers_lista.html', context)

@login_required
@permission_required('transacciones.revision', raise_exception=True)
def tauser_detalle(request, pk):
    """
    Vista para mostrar los detalles completos de un TAUser específico.
    
    Muestra información detallada del TAUser incluyendo puerto, estado,
    billetes asociados y sus cantidades disponibles.
    Incluye filtrado por moneda para billetes.
    
    Args:
        request (HttpRequest): Petición HTTP
        pk (int): ID del TAUser a mostrar
        
    Returns:
        HttpResponse: Página de detalle del TAUser
        
    Template:
        transacciones/tauser_detalles.html
        
    Context:
        - tauser: Instancia del TAUser
        - billetes_tauser: QuerySet de billetes asociados al TAUser
        - monedas_disponibles: Lista de monedas que tienen billetes en este TAUser
        - moneda_filtro: Moneda seleccionada para filtrar (si aplica)  
        - totales_por_moneda: Diccionario con totales por moneda
    """
    from .models import BilletesTauser
    from monedas.models import Moneda
    from django.db.models import Sum, F, Count
    
    tauser = get_object_or_404(Tauser, pk=pk)
    
    # Obtener todos los billetes del TAUser (sin filtrar para obtener todas las monedas disponibles)
    todos_billetes_tauser = BilletesTauser.objects.filter(tauser=tauser)
    
    # Calcular totales por moneda
    totales_por_moneda = {}
    
    # Total para guaraníes (denominaciones sin moneda)
    total_guaranies = todos_billetes_tauser.filter(
        denominacion__moneda__isnull=True
    ).aggregate(
        total=Sum(F('cantidad') * F('denominacion__valor'))
    )['total'] or 0
    
    if total_guaranies > 0:
        totales_por_moneda['guarani'] = {
            'nombre': 'Guaraní',
            'total': total_guaranies,
            'simbolo': 'Gs.'
        }
    
    # Totales para monedas extranjeras
    for moneda in Moneda.objects.all():
        total_moneda = todos_billetes_tauser.filter(
            denominacion__moneda=moneda
        ).aggregate(
            total=Sum(F('cantidad') * F('denominacion__valor'))
        )['total']
        
        if total_moneda and total_moneda > 0:
            totales_por_moneda[moneda.id] = {
                'nombre': moneda.nombre,
                'total': total_moneda,
                'simbolo': moneda.simbolo
            }
    
    # Obtener todas las monedas que tienen billetes en este TAUser (antes de aplicar filtros)
    monedas_con_billetes = todos_billetes_tauser.values_list('denominacion__moneda', flat=True).distinct()
    monedas_disponibles = []
    
    # Agregar guaraní si hay billetes sin moneda (denominación de guaraníes)
    if None in monedas_con_billetes:
        monedas_disponibles.append({'id': 'guarani', 'nombre': 'Guaraní'})
    
    # Agregar monedas extranjeras
    for moneda_id in monedas_con_billetes:
        if moneda_id is not None:
            try:
                moneda = Moneda.objects.get(id=moneda_id)
                monedas_disponibles.append({'id': moneda.id, 'nombre': moneda.nombre})
            except Moneda.DoesNotExist:
                pass
    
    # Ahora aplicar el filtro para mostrar los billetes
    billetes_tauser_query = todos_billetes_tauser
    
    # Obtener parámetro de filtro de moneda
    moneda_filtro = request.GET.get('moneda', '')
    
    # Aplicar filtro de moneda si se especifica
    if moneda_filtro:
        if moneda_filtro == 'guarani':
            billetes_tauser_query = billetes_tauser_query.filter(denominacion__moneda__isnull=True)
        else:
            try:
                moneda_id = int(moneda_filtro)
                billetes_tauser_query = billetes_tauser_query.filter(denominacion__moneda_id=moneda_id)
            except (ValueError, TypeError):
                pass
    
    billetes_tauser = billetes_tauser_query.order_by('denominacion__moneda', 'denominacion__valor')
    
    context = {
        'tauser': tauser,
        'billetes_tauser': billetes_tauser,
        'monedas_disponibles': monedas_disponibles,
        'moneda_filtro': moneda_filtro,
        'totales_por_moneda': totales_por_moneda
    }
    return render(request, 'transacciones/tauser_detalles.html', context)

@login_required
@permission_required('transacciones.revision', raise_exception=True) 
def verificar_estado_tauser(request, tauser_id):
    """
    Vista AJAX para verificar el estado de un TAUser específico.
    
    Útil para verificaciones individuales sin recargar toda la página.
    
    Args:
        request (HttpRequest): Petición HTTP (debe ser AJAX)
        tauser_id (int): ID del TAUser a verificar
        
    Returns:
        JsonResponse: Estado del TAUser y información adicional
    """
    from django.http import JsonResponse
    
    try:
        tauser = get_object_or_404(Tauser, pk=tauser_id)
        esta_activo = tauser.esta_activo()
        
        return JsonResponse({
            'success': True,
            'tauser_id': tauser.id,
            'puerto': tauser.puerto,
            'activo': esta_activo,
            'estado_texto': 'Activo' if esta_activo else 'Inactivo',
            'url': f'http://localhost:{tauser.puerto}'
        })
        
    except Tauser.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'TAUser no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

logger = logging.getLogger(__name__)

@csrf_exempt
def recibir_pago(request):
    """Vista para recibir y verificar notificaciones de la pasarela"""
    logger.info("Recibiendo notificación de pago")
    
    if request.method == 'POST':
        try:
            # Log de headers para debug
            logger.info(f"Headers recibidos: {dict(request.headers)}")
            

            data = json.loads(request.body)
            logger.info(f"Datos recibidos: {data}")
            
            estado = data.get('estado')
            monto = data.get('monto')
            tipo_pago = data.get('tipo_pago')
            
            # Validar datos
            if estado not in ['exito', 'error', 'cancelado']:
                logger.error(f"Estado inválido recibido: {estado}")
                return JsonResponse({'status': 'error', 'mensaje': 'Estado inválido'})
            
            if estado != 'cancelado' and not monto:
                logger.error("Monto requerido no recibido")
                return JsonResponse({'status': 'error', 'mensaje': 'Monto requerido'})

            # Procesar según estado
            if estado == 'exito':
                logger.info(f"Pago exitoso procesado: {data}")
                return JsonResponse({'status': 'ok', 'mensaje': 'Pago procesado correctamente'})
            elif estado == 'error':
                logger.warning(f"Error en pago: {data}")
                return JsonResponse({'status': 'error', 'mensaje': 'Error procesando pago'})
            else:
                logger.info(f"Pago cancelado: {data}")
                return JsonResponse({'status': 'ok', 'mensaje': 'Pago cancelado'})

        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON: {str(e)}")
            return JsonResponse({'status': 'error', 'mensaje': 'JSON inválido'}, status=400)
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return JsonResponse({'status': 'error', 'mensaje': str(e)}, status=500)
    
    logger.warning("Método no permitido")
    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)