from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from monedas.models import Moneda
from .forms import SeleccionMonedaMontoForm
from decimal import Decimal

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
            
            # Guardar los datos en la sesión
            request.session['compra_datos'] = {
                'moneda_id': moneda.id,
                'moneda_nombre': moneda.nombre,
                'moneda_simbolo': moneda.simbolo,
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
        moneda = Moneda.objects.get(id=compra_datos['moneda_id'])
        monto = Decimal(compra_datos['monto'])
    except (Moneda.DoesNotExist, ValueError, KeyError):
        messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
        return redirect('transacciones:compra_monto_moneda')
    
    if request.method == 'POST':
        # Verificar si es selección de medio de pago o avance al siguiente paso
        accion = request.POST.get('accion')
        
        if accion == 'seleccionar_medio':
            # Manejar la selección de medio de pago
            medio_pago_id = request.POST.get('medio_pago_id')
            if medio_pago_id:
                try:
                    from medios_pago.models import MedioPago
                    medio_pago = MedioPago.objects.get(
                        id=medio_pago_id,
                        activo=True
                    )
                    
                    # Actualizar los datos de la sesión (sin cambiar el paso_actual)
                    compra_datos.update({
                        'medio_pago_id': medio_pago.id,
                        'medio_pago_nombre': medio_pago.get_tipo_display(),
                        'medio_pago_tipo': medio_pago.tipo
                    })
                    request.session['compra_datos'] = compra_datos

                    messages.success(request, f'Medio de pago {medio_pago.get_tipo_display()} seleccionado correctamente.')
                    return redirect('transacciones:compra_medio_pago')  # Permanecer en el mismo paso
        
                except Exception as e:
                    messages.error(request, 'Error al seleccionar el medio de pago. Intente nuevamente.')
                    return redirect('transacciones:compra_medio_pago')
        
        elif accion == 'continuar':
            # Verificar que hay un medio de pago seleccionado
            if not compra_datos.get('medio_pago_id'):
                messages.error(request, 'Debe seleccionar un medio de pago antes de continuar.')
                return redirect('transacciones:compra_medio_pago')
            
            # Actualizar el paso actual y continuar al siguiente paso
            compra_datos['paso_actual'] = 3
            request.session['compra_datos'] = compra_datos
            
            messages.success(request, 'Continuando al siguiente paso...')
            # Aquí redirigiríamos al siguiente paso (paso 3)
            # return redirect('transacciones:compra_medio_cobro')
            return redirect('transacciones:compra_medio_pago')  # Por ahora redirijo al mismo paso
    
    # Obtener los medios de pago que soportan la moneda seleccionada
    from medios_pago.models import MedioPago
    medios_pago_disponibles = MedioPago.objects.filter(
        activo=True
    ).distinct()
    
    # Obtener el medio de pago seleccionado actualmente (si hay uno)
    medio_pago_seleccionado = None
    if compra_datos.get('medio_pago_id'):
        try:
            medio_pago_seleccionado = MedioPago.objects.get(
                id=compra_datos['medio_pago_id']
            )
        except MedioPago.DoesNotExist:
            pass
    
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
            
            # Guardar los datos en la sesión
            request.session['venta_datos'] = {
                'moneda_id': moneda.id,
                'moneda_nombre': moneda.nombre,
                'moneda_simbolo': moneda.simbolo,
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
        moneda = Moneda.objects.get(id=venta_datos['moneda_id'])
        monto = Decimal(venta_datos['monto'])
    except (Moneda.DoesNotExist, ValueError, KeyError):
        messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
        return redirect('transacciones:venta_monto_moneda')
    
    if request.method == 'POST':
        # Verificar si es selección de medio de pago o avance al siguiente paso
        accion = request.POST.get('accion')
        
        if accion == 'seleccionar_medio':
            # Manejar la selección de medio de pago
            medio_pago_id = request.POST.get('medio_pago_id')
            if medio_pago_id:
                try:
                    from medios_pago.models import MedioPago
                    medio_pago = MedioPago.objects.get(
                        id=medio_pago_id,
                        activo=True
                    )
                    
                    # Actualizar los datos de la sesión (sin cambiar el paso_actual)
                    venta_datos.update({
                        'medio_pago_id': medio_pago.id,
                        'medio_pago_nombre': medio_pago.get_tipo_display(),
                        'medio_pago_tipo': medio_pago.tipo
                    })
                    request.session['venta_datos'] = venta_datos

                    messages.success(request, f'Medio de pago {medio_pago.get_tipo_display()} seleccionado correctamente.')
                    return redirect('transacciones:venta_medio_pago')  # Permanecer en el mismo paso
        
                except Exception as e:
                    messages.error(request, 'Error al seleccionar el medio de pago. Intente nuevamente.')
                    return redirect('transacciones:venta_medio_pago')
        
        elif accion == 'continuar':
            # Verificar que hay un medio de pago seleccionado
            if not venta_datos.get('medio_pago_id'):
                messages.error(request, 'Debe seleccionar un medio de pago antes de continuar.')
                return redirect('transacciones:venta_medio_pago')
            
            # Actualizar el paso actual y continuar al siguiente paso
            venta_datos['paso_actual'] = 3
            request.session['venta_datos'] = venta_datos
            
            messages.success(request, 'Continuando al siguiente paso...')
            # Aquí redirigiríamos al siguiente paso (paso 3)
            # return redirect('transacciones:venta_medio_cobro')
            return redirect('transacciones:venta_medio_pago')  # Por ahora redirijo al mismo paso
    
    # Obtener los medios de pago que soportan la moneda seleccionada
    from medios_pago.models import MedioPago
    medios_pago_disponibles = MedioPago.objects.filter(
        activo=True,
        monedas=moneda  # Filtrar solo los medios de pago que soportan esta moneda
    ).distinct()
    
    # Obtener el medio de pago seleccionado actualmente (si hay uno)
    medio_pago_seleccionado = None
    if venta_datos.get('medio_pago_id'):
        try:
            medio_pago_seleccionado = MedioPago.objects.get(
                id=venta_datos['medio_pago_id']
            )
        except MedioPago.DoesNotExist:
            pass
    
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
