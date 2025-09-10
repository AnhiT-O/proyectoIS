from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from .models import Moneda
from .forms import MonedaForm
from decimal import Decimal
from django.http import JsonResponse
from django.utils import formats

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
def simular(request):
    if request.method == 'GET':
        monedas = Moneda.objects.filter(activa=True)
        return render(request, 'monedas/simulador.html', {'monedas': monedas})

    elif request.method == 'POST':
        try:
            moneda_id = request.POST.get('moneda')
            monto_str = request.POST.get('monto', '').strip()
            operacion = request.POST.get('operacion')

            # Validaciones simples
            errores = {}
            
            # Validar moneda requerida
            if not moneda_id:
                errores['moneda'] = ['Debe seleccionar una moneda.']
            else:
                try:
                    moneda = Moneda.objects.get(id=moneda_id, activa=True)
                except Moneda.DoesNotExist:
                    errores['moneda'] = ['La moneda seleccionada no es válida.']
            
            # Validar monto requerido y mínimo
            if not monto_str:
                errores['monto'] = ['El monto es obligatorio.']
            else:
                try:
                    monto = Decimal(monto_str)
                    if monto <= 0:
                        errores['monto'] = ['El monto debe ser mayor a 0.']
                    elif operacion == 'compra':
                        # Para compra (PYG), no permitir decimales
                        if '.' in monto_str and monto_str.split('.')[1] != '0':
                            errores['monto'] = ['Para compra, ingrese solo números enteros (guaraníes).']
                        elif monto < 1:
                            errores['monto'] = ['El monto mínimo para compra es 1 guaraní.']
                    elif operacion == 'venta':
                        # Para venta, usar los decimales de la moneda seleccionada
                        if 'moneda' in locals():
                            monto_minimo = Decimal('1') / (Decimal('10') ** moneda.decimales)
                            if monto < monto_minimo:
                                errores['monto'] = [f'El monto mínimo para venta es {monto_minimo} {moneda.simbolo}.']
                        else:
                            # Fallback si no se puede obtener la moneda
                            if monto < Decimal('0.01'):
                                errores['monto'] = ['El monto mínimo para venta es 0.01.']
                except (ValueError, TypeError):
                    errores['monto'] = ['Por favor, ingrese un monto válido.']
            
            # Si hay errores, devolverlos
            if errores:
                return JsonResponse({
                    'success': False,
                    'errors': errores
                })

            # Si todo está bien, realizar la conversión
            monto = Decimal(monto_str)
            
            # Obtener el cliente activo si el usuario está autenticado
            cliente = None
            if request.user.is_authenticated and hasattr(request.user, 'cliente_activo'):
                cliente = request.user.cliente_activo

            # Obtener precios según la segmentación del cliente
            precios = moneda.get_precios_cliente(cliente) if cliente else {
                'precio_compra': moneda.calcular_precio_compra(),
                'precio_venta': moneda.calcular_precio_venta()
            }

            # Realizar la conversión según el tipo de operación
            if operacion == 'venta':
                # Venta: moneda extranjera a PYG
                resultado = monto * precios['precio_compra']
                return JsonResponse({
                    'success': True,
                    'resultado_numerico': int(resultado),
                    'tipo_resultado': 'guaranies'
                })
            else:  # compra
                # Compra: PYG a moneda extranjera
                resultado = monto / precios['precio_venta']
                return JsonResponse({
                    'success': True,
                    'resultado_numerico': float(resultado),
                    'decimales': moneda.decimales,
                    'simbolo': moneda.simbolo,
                    'tipo_resultado': 'moneda_extranjera'
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'Ocurrió un error al procesar la conversión.'
            })