from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.db import transaction
from django.http import JsonResponse
from .models import Moneda, LimiteGlobal, ConsumoLimiteCliente
from .forms import MonedaForm, LimiteGlobalForm
from .services import LimiteService


def tiene_algun_permiso(view_func):
    """
    Decorador que verifica si el usuario tiene al menos uno de los permisos necesarios
    para administrar monedas: creación, edición o activación.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        # Permisos requeridos para administrar monedas
        permisos_requeridos = [
            'monedas.gestion',
            'monedas.activacion'    # Permiso para activar/desactivar monedas
        ]
        
        # Verificar si el usuario tiene al menos uno de los permisos
        for permiso in permisos_requeridos:
            if request.user.has_perm(permiso):
                return view_func(request, *args, **kwargs)
        
        # Si no tiene ningún permiso, denegar acceso
        raise PermissionDenied()

    return _wrapped_view

def puede_editar(view_func):
    """
    Decorador que verifica si el usuario tiene al menos uno de los permisos necesarios
    para administrar monedas: creación, edición o activación.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        # Permisos requeridos para administrar monedas
        permisos_requeridos = [
            'monedas.gestion',       # Permiso para editar monedas
            'monedas.cotizacion'  # Permiso para cambiar la tasa base de una moneda
        ]
        
        # Verificar si el usuario tiene al menos uno de los permisos
        for permiso in permisos_requeridos:
            if request.user.has_perm(permiso):
                return view_func(request, *args, **kwargs)
        
        # Si no tiene ningún permiso, denegar acceso
        raise PermissionDenied()

    return _wrapped_view

@login_required
@permission_required('monedas.gestion', raise_exception=True)
def moneda_crear(request):
    if request.method == 'POST':
        form = MonedaForm(request.POST)
        if form.is_valid():
            moneda = form.save()
            messages.success(request, f'Moneda "{moneda.nombre}" creada exitosamente.')
            return redirect('monedas:lista_monedas')
    else:
        form = MonedaForm()
    return render(request, 'monedas/moneda_form.html', {'form': form,})

@login_required
@tiene_algun_permiso
def moneda_lista(request):
    # Manejar cambio de estado si se envía POST
    if request.method == 'POST' and 'cambiar_estado' in request.POST:
        
        try:
            moneda_id = request.POST.get('moneda_id')
            moneda = get_object_or_404(Moneda, pk=moneda_id)
            
            # Cambiar el estado de la moneda
            moneda.activa = not moneda.activa
            moneda.save()
            
            estado_texto = "activada" if moneda.activa else "desactivada"
            messages.success(request, f'Moneda "{moneda.nombre}" {estado_texto} exitosamente.')
            
            # Comprobar si hay un parámetro next para redirección
            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url)
                
        except Exception as e:
            messages.error(request, 'Error al cambiar el estado de la moneda.')
    
    # Obtener todas las monedas
    todas_las_monedas = Moneda.objects.all()
    monedas = todas_las_monedas
    
    # Manejar búsqueda
    busqueda = request.GET.get('busqueda', '').strip()
    if busqueda:
        monedas = monedas.filter(
            Q(nombre__icontains=busqueda) | 
            Q(simbolo__icontains=busqueda)
        )
    
    # Ordenar por nombre
    monedas = monedas.order_by('nombre')
    
    # Calcular estadísticas
    monedas_activas = monedas.filter(activa=True).count()
    monedas_inactivas = monedas.filter(activa=False).count()
    
    # Total de monedas en el sistema (sin filtrar)
    total_monedas_sistema = todas_las_monedas.count()
    
    context = {
        'monedas': monedas,
        'monedas_activas': monedas_activas,
        'monedas_inactivas': monedas_inactivas,
        'busqueda': busqueda,
        'total_monedas_sistema': total_monedas_sistema,
    }
    return render(request, 'monedas/moneda_lista.html', context)

@login_required
@puede_editar
def moneda_editar(request, pk):
    moneda = get_object_or_404(Moneda, pk=pk)
    # Instancia el formulario normalmente
    if request.method == 'POST':
        form = MonedaForm(request.POST, instance=moneda)
    else:
        form = MonedaForm(instance=moneda)

    if not request.user.has_perm('monedas.gestion'):
    # Elimina campos según permisos
        form.fields.pop('nombre')
        form.fields.pop('simbolo')
        form.fields.pop('decimales')

    # Procesa el formulario
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f'Moneda \"{moneda.nombre}\" editada exitosamente.')
            return redirect('monedas:lista_monedas')
        else:
            messages.error(request, 'Error al actualizar la moneda.')
    return render(request, 'monedas/moneda_form.html', {'form': form, 'moneda': moneda,})

@login_required
@tiene_algun_permiso
def moneda_detalle(request, pk):
    """Vista para mostrar los detalles completos de una moneda"""
    moneda = get_object_or_404(Moneda, pk=pk)
    
    # Calcular precios sin beneficios (cliente None)
    precios = moneda.get_precios_cliente(None)
    
    context = {
        'moneda': moneda,
        'precio_compra': precios['precio_compra'],
        'precio_venta': precios['precio_venta'],
    }
    return render(request, 'monedas/moneda_detalles.html', context)


# ============================================================================
# VISTAS PARA GESTIÓN DE LÍMITES
# ============================================================================

@login_required
@permission_required('monedas.gestion', raise_exception=True)
def lista_limites(request):
    """Vista para listar todos los límites globales"""
    limites = LimiteGlobal.objects.all().order_by('-fecha_inicio')
    limite_vigente = LimiteGlobal.obtener_limite_vigente()
    
    context = {
        'title': 'Gestión de Límites Globales',
        'limites': limites,
        'limite_vigente': limite_vigente,
    }
    return render(request, 'monedas/lista_limites.html', context)


@login_required
@permission_required('monedas.gestion', raise_exception=True)
def crear_limite(request):
    """Vista para crear un nuevo límite global"""
    if request.method == 'POST':
        form = LimiteGlobalForm(request.POST)
        if form.is_valid():
            limite = form.save()
            messages.success(request, f'Límite global creado exitosamente.')
            return redirect('monedas:lista_limites')
        else:
            messages.error(request, 'Error al crear el límite global.')
    else:
        form = LimiteGlobalForm()
    
    context = {
        'title': 'Crear Nuevo Límite Global',
        'form': form,
        'accion': 'Crear Límite'
    }
    return render(request, 'monedas/limite_form.html', context)


@login_required
@permission_required('monedas.gestion', raise_exception=True)
def editar_limite(request, pk):
    """Vista para editar un límite global existente"""
    limite = get_object_or_404(LimiteGlobal, pk=pk)
    
    if request.method == 'POST':
        form = LimiteGlobalForm(request.POST, instance=limite)
        if form.is_valid():
            form.save()
            messages.success(request, f'Límite global actualizado exitosamente.')
            return redirect('monedas:lista_limites')
        else:
            messages.error(request, 'Error al actualizar el límite global.')
    else:
        form = LimiteGlobalForm(instance=limite)
    
    context = {
        'title': 'Editar Límite Global',
        'form': form,
        'accion': 'Actualizar Límite',
        'limite': limite
    }
    return render(request, 'monedas/limite_form.html', context)


@login_required
@permission_required('monedas.gestion', raise_exception=True)
def activar_limite(request, pk):
    """Vista para activar un límite específico (desactiva todos los demás)"""
    if request.method == 'POST':
        limite = get_object_or_404(LimiteGlobal, pk=pk)
        
        try:
            with transaction.atomic():
                # Desactivar todos los límites
                LimiteGlobal.objects.all().update(activo=False)
                # Activar el límite seleccionado
                limite.activo = True
                limite.save()
                
            messages.success(request, f'Límite activado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al activar el límite: {str(e)}')
    
    return redirect('monedas:lista_limites')


# ============================================================================
# APIS AJAX PARA LÍMITES
# ============================================================================

@login_required
def consultar_limites_cliente(request):
    """API AJAX para consultar límites disponibles de un cliente"""
    if request.method == 'GET':
        cliente_id = request.GET.get('cliente_id')
        
        if not cliente_id:
            return JsonResponse({
                'success': False,
                'error': 'ID de cliente requerido'
            })
        
        try:
            from clientes.models import Cliente
            cliente = Cliente.objects.get(id=cliente_id)
            limites_info = LimiteService.obtener_limites_disponibles(cliente)
            
            return JsonResponse({
                'success': True,
                'data': {
                    'cliente': {
                        'id': cliente.id,
                        'nombre': cliente.nombre
                    },
                    'limites': limites_info
                }
            })
            
        except Cliente.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Cliente no encontrado'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    })


@login_required
def validar_transaccion_limite(request):
    """API AJAX para validar si una transacción puede realizarse"""
    if request.method == 'POST':
        try:
            cliente_id = request.POST.get('cliente_id')
            moneda_id = request.POST.get('moneda_id')
            tipo_transaccion = request.POST.get('tipo_transaccion')
            monto = request.POST.get('monto')
            
            # Validar parámetros requeridos
            if not all([cliente_id, moneda_id, tipo_transaccion, monto]):
                return JsonResponse({
                    'success': False,
                    'error': 'Todos los parámetros son requeridos'
                })
            
            # Obtener objetos
            from clientes.models import Cliente
            cliente = Cliente.objects.get(id=cliente_id)
            moneda = Moneda.objects.get(id=moneda_id)
            monto = int(monto)
            
            # Validar tipo de transacción
            if tipo_transaccion not in ['COMPRA', 'VENTA']:
                return JsonResponse({
                    'success': False,
                    'error': 'Tipo de transacción inválido'
                })
            
            # Validar límites (sin procesar la transacción)
            monto_guaranies = LimiteService.convertir_a_guaranies(
                monto, moneda, tipo_transaccion, cliente
            )
            
            LimiteService.validar_limite_transaccion(cliente, monto_guaranies)
            
            # Si llegamos aquí, la transacción es válida
            limites_restantes = LimiteService.obtener_limites_disponibles(cliente)
            
            return JsonResponse({
                'success': True,
                'data': {
                    'monto_original': monto,
                    'monto_guaranies': monto_guaranies,
                    'cliente': cliente.nombre,
                    'moneda': moneda.simbolo,
                    'tipo_transaccion': tipo_transaccion,
                    'limites_restantes': limites_restantes
                }
            })
            
        except (Cliente.DoesNotExist, Moneda.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'Cliente o moneda no encontrados'
            })
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error inesperado: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    })


# ===== VISTAS PARA GESTIÓN DE LÍMITES =====

@login_required
@permission_required('monedas.gestion', raise_exception=True)
def lista_limites(request):
    """
    Vista para listar todos los límites globales configurados
    """
    limites = LimiteGlobal.objects.all().order_by('-fecha_inicio')
    limite_vigente = LimiteGlobal.obtener_limite_vigente()
    
    context = {
        'limites': limites,
        'limite_vigente': limite_vigente,
        'title': 'Gestión de Límites Globales'
    }
    return render(request, 'monedas/lista_limites.html', context)


@login_required
@permission_required('monedas.gestion', raise_exception=True)
def crear_limite(request):
    """
    Vista para crear un nuevo límite global
    """
    if request.method == 'POST':
        form = LimiteGlobalForm(request.POST)
        if form.is_valid():
            # Si se marca como activo, desactivar otros límites
            if form.cleaned_data['activo']:
                LimiteGlobal.objects.filter(activo=True).update(activo=False)
            
            form.save()
            messages.success(request, 'Límite global creado exitosamente.')
            return redirect('monedas:lista_limites')
        else:
            messages.error(request, 'Error al crear el límite. Revise los datos.')
    else:
        form = LimiteGlobalForm()
    
    context = {
        'form': form,
        'title': 'Crear Límite Global',
        'accion': 'Crear'
    }
    return render(request, 'monedas/limite_form.html', context)


@login_required
@permission_required('monedas.gestion', raise_exception=True)
def editar_limite(request, pk):
    """
    Vista para editar un límite global existente
    """
    limite = get_object_or_404(LimiteGlobal, pk=pk)
    
    if request.method == 'POST':
        form = LimiteGlobalForm(request.POST, instance=limite)
        if form.is_valid():
            # Si se marca como activo, desactivar otros límites
            if form.cleaned_data['activo']:
                LimiteGlobal.objects.exclude(pk=pk).update(activo=False)
            
            form.save()
            messages.success(request, 'Límite global actualizado exitosamente.')
            return redirect('monedas:lista_limites')
        else:
            messages.error(request, 'Error al actualizar el límite. Revise los datos.')
    else:
        form = LimiteGlobalForm(instance=limite)
    
    context = {
        'form': form,
        'limite': limite,
        'title': 'Editar Límite Global',
        'accion': 'Actualizar'
    }
    return render(request, 'monedas/limite_form.html', context)


@login_required
@permission_required('monedas.gestion', raise_exception=True)
def activar_limite(request, pk):
    """
    Vista para activar un límite global específico
    """
    if request.method == 'POST':
        limite = get_object_or_404(LimiteGlobal, pk=pk)
        
        # Desactivar todos los demás límites
        LimiteGlobal.objects.exclude(pk=pk).update(activo=False)
        
        # Activar el límite seleccionado
        limite.activo = True
        limite.save()
        
        messages.success(request, f'Límite activado exitosamente.')
        return redirect('monedas:lista_limites')
    
    return redirect('monedas:lista_limites')


@login_required
def consultar_limites_cliente(request):
    """
    Vista AJAX para consultar los límites disponibles de un cliente
    """
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cliente_id = request.GET.get('cliente_id')
        
        if not cliente_id:
            return JsonResponse({'error': 'ID de cliente requerido'}, status=400)
        
        try:
            from clientes.models import Cliente
            cliente = get_object_or_404(Cliente, pk=cliente_id)
            
            limites_info = LimiteService.obtener_limites_disponibles(cliente)
            
            if 'error' in limites_info:
                return JsonResponse({'error': limites_info['error']}, status=400)
            
            return JsonResponse({
                'success': True,
                'data': {
                    'cliente': {
                        'id': cliente.id,
                        'nombre': cliente.nombre,
                    },
                    'limites': limites_info
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def validar_transaccion_limite(request):
    """
    Vista AJAX para validar si una transacción puede realizarse sin superar límites
    """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Obtener datos del request
            cliente_id = request.POST.get('cliente_id')
            moneda_id = request.POST.get('moneda_id')
            tipo_transaccion = request.POST.get('tipo_transaccion')
            monto = request.POST.get('monto')
            
            # Validar datos requeridos
            if not all([cliente_id, moneda_id, tipo_transaccion, monto]):
                return JsonResponse({
                    'error': 'Faltan datos requeridos: cliente_id, moneda_id, tipo_transaccion, monto'
                }, status=400)
            
            # Obtener instancias
            from clientes.models import Cliente
            cliente = get_object_or_404(Cliente, pk=cliente_id)
            moneda = get_object_or_404(Moneda, pk=moneda_id)
            monto = int(monto)
            
            # Validar la transacción
            resultado = LimiteService.validar_y_procesar_transaccion(
                cliente=cliente,
                moneda=moneda,
                tipo_transaccion=tipo_transaccion.upper(),
                monto_original=monto
            )
            
            return JsonResponse({
                'success': True,
                'data': resultado
            })
            
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def verificar_cambios_precios(request, moneda_id):
    """API para verificar cambios en los precios de una moneda"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            moneda = Moneda.objects.get(pk=moneda_id)
            cliente = request.user.cliente_activo
            
            # Obtener precios actuales
            precios_actuales = moneda.get_precios_cliente(cliente)
            
            # Obtener precios iniciales de la sesión
            precio_compra_inicial = request.session.get('precio_compra_inicial')
            precio_venta_inicial = request.session.get('precio_venta_inicial')
            
            if precio_compra_inicial is None or precio_venta_inicial is None:
                # Si no hay precios iniciales, guardarlos
                request.session['precio_compra_inicial'] = precios_actuales['precio_compra']
                request.session['precio_venta_inicial'] = precios_actuales['precio_venta']
                return JsonResponse({'hubo_cambio': False})
            
            # Verificar si hubo cambios
            hubo_cambio = (precio_compra_inicial != precios_actuales['precio_compra'] or 
                          precio_venta_inicial != precios_actuales['precio_venta'])
            
            return JsonResponse({
                'hubo_cambio': hubo_cambio,
                'precios_anteriores': {
                    'compra': precio_compra_inicial,
                    'venta': precio_venta_inicial
                },
                'precios_actuales': {
                    'compra': precios_actuales['precio_compra'],
                    'venta': precios_actuales['precio_venta']
                }
            })
            
        except Moneda.DoesNotExist:
            return JsonResponse({'error': 'Moneda no encontrada'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Solicitud inválida'}, status=400)