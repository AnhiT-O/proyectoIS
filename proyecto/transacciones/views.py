from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from monedas.models import Moneda
from monedas.services import LimiteService
from .forms import SeleccionMonedaMontoForm
from decimal import Decimal
from clientes.models import Cliente

def extraer_mensaje_error(validation_error):
    """
    Función auxiliar para extraer el mensaje de error de un ValidationError
    sin los corchetes que Django puede agregar.
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
    Función auxiliar para obtener información de límites del cliente
    para mostrar en las plantillas.
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

# PROCESO DE COMPRA

@login_required
def compra_monto_moneda(request):
    """
    Vista para el primer paso del proceso de compra de monedas.
    Permite al usuario seleccionar la moneda y el monto que desea comprar.
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

# Vista para el segundo paso del proceso de compra
@login_required
def compra_medio_pago(request):
    """
    Vista para el segundo paso del proceso de compra.
    Permite seleccionar el medio de pago del cliente activo.
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
        medios_pago_disponibles.append('Tarjeta de Crédito')
    
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
    Vista para el tercer paso del proceso de compra.
    Permite seleccionar el medio de cobro del cliente activo para realizar el pago.
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
        monto = Decimal(compra_datos['monto'])
        medio_pago = compra_datos['medio_pago']
    except (Moneda.DoesNotExist, ValueError, KeyError):
        messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
        return redirect('transacciones:compra_monto_moneda')
    
    return render(request, 'transacciones/seleccion_medio_cobro.html')

@login_required
def compra_confirmacion(request):
    """
    Vista para el último paso del proceso de compra.
    Muestra un resumen de la transacción antes de confirmarla.
    """
    # Verificar que el usuario tenga un cliente activo
    if not request.user.cliente_activo:
        messages.error(request, 'Debe tener un cliente activo seleccionado para continuar.')
        return redirect('inicio')
    # Verificar que existan datos del paso anterior
    compra_datos = request.session.get('compra_datos')
    if not compra_datos or compra_datos.get('paso_actual') != 3:
        messages.error(request, 'Debe completar el tercer paso antes de continuar.')
        return redirect('transacciones:compra_medio_cobro')
    # Recuperar los datos de la sesión
    try:
        moneda = Moneda.objects.get(id=compra_datos['moneda'])
        monto = Decimal(compra_datos['monto'])
        medio_pago = compra_datos['medio_pago']
    except (Moneda.DoesNotExist, ValueError, KeyError):
        messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
        return redirect('transacciones:compra_monto_moneda')
    
    return render(request, 'transacciones/confirmacion.html')

@login_required
def compra_exito(request):
    """
    Vista que muestra el mensaje de éxito tras completar la compra.
    """
    # Limpiar los datos de la sesión relacionados con la compra
    if 'compra_datos' in request.session:
        del request.session['compra_datos']
    
    return render(request, 'transacciones/exito.html')

# PROCESO DE VENTA

@login_required
def venta_monto_moneda(request):
    """
    Vista para el primer paso del proceso de venta de monedas.
    Permite al usuario seleccionar la moneda y el monto que desea vender.
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
    Vista para el segundo paso del proceso de venta.
    Permite seleccionar el medio de pago del cliente activo para recibir el pago.
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
        medios_pago_disponibles.append('Tarjeta de Crédito')

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
    Vista para el tercer paso del proceso de venta.
    Permite seleccionar el medio de cobro del cliente activo para realizar el pago.
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
        monto = Decimal(venta_datos['monto'])
        medio_pago = venta_datos['medio_pago']
    except (Moneda.DoesNotExist, ValueError, KeyError):
        messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
        return redirect('transacciones:venta_monto_moneda')
    
    return render(request, 'transacciones/seleccion_medio_cobro.html')

@login_required
def venta_confirmacion(request):
    """
    Vista para el último paso del proceso de venta.
    Muestra un resumen de la transacción antes de confirmarla.
    """
    # Verificar que el usuario tenga un cliente activo
    if not request.user.cliente_activo:
        messages.error(request, 'Debe tener un cliente activo seleccionado para continuar.')
        return redirect('inicio')
    # Verificar que existan datos del paso anterior
    venta_datos = request.session.get('venta_datos')
    if not venta_datos or venta_datos.get('paso_actual') != 3:
        messages.error(request, 'Debe completar el tercer paso antes de continuar.')
        return redirect('transacciones:venta_medio_cobro')
    # Recuperar los datos de la sesión
    try:
        moneda = Moneda.objects.get(id=venta_datos['moneda'])
        monto = Decimal(venta_datos['monto'])
        medio_pago = venta_datos['medio_pago']
    except (Moneda.DoesNotExist, ValueError, KeyError):
        messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
        return redirect('transacciones:venta_monto_moneda')
    
    return render(request, 'transacciones/confirmacion.html')

@login_required
def venta_exito(request):
    """
    Vista que muestra el mensaje de éxito tras completar la venta.
    """
    # Limpiar los datos de la sesión relacionados con la venta
    if 'venta_datos' in request.session:
        del request.session['venta_datos']

    return render(request, 'transacciones/exito.html')

@login_required
def obtener_limites_cliente(request):
    """
    Vista AJAX para obtener información de límites del cliente activo.
    Útil para mostrar información dinámica en las plantillas.
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
    Vista AJAX para simular una transacción y verificar límites sin procesarla.
    Útil para validaciones en tiempo real.
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