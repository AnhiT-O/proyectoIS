from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Moneda, Denominacion, HistorialCotizacion
from .forms import MonedaForm


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
            'monedas.activacion',
            'monedas.cotizacion'   # Permiso para activar/desactivar monedas
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
        form.fields.pop('denominaciones')

    # Procesa el formulario
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f'Moneda \"{moneda.nombre}\" editada exitosamente.')
            return redirect('monedas:lista_monedas')
    return render(request, 'monedas/moneda_form.html', {'form': form, 'moneda': moneda,})

@login_required
@tiene_algun_permiso
def moneda_detalle(request, pk):
    """Vista para mostrar los detalles completos de una moneda"""
    moneda = get_object_or_404(Moneda, pk=pk)
    denominaciones = Denominacion.objects.filter(moneda=moneda).order_by('valor')
    
    context = {
        'moneda': moneda,
        'denominaciones': denominaciones
    }
    return render(request, 'monedas/moneda_detalles.html', context)


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

@login_required
def evolucion_cotizacion(request, pk):
    """
    Vista para mostrar la evolución de las cotizaciones de una moneda específica
    """
    moneda = get_object_or_404(Moneda, pk=pk)
    
    # Obtener datos históricos de los últimos 12 meses
    fecha_limite = timezone.now().date() - timedelta(days=365)
    historial = HistorialCotizacion.objects.filter(
        moneda=moneda,
        fecha__gte=fecha_limite
    ).order_by('fecha')
    
    # Si no hay historial, crear algunos datos de ejemplo para demostración
    if not historial.exists():
        # Generar algunos datos de ejemplo para los últimos 30 días
        datos_ejemplo = []
        for i in range(30, 0, -1):
            fecha = timezone.now().date() - timedelta(days=i)
            # Variación pequeña en las tasas para simular evolución
            variacion = (i % 5) * 10  # Pequeña variación
            tasa_base = moneda.tasa_base + variacion
            
            datos_ejemplo.append({
                'fecha': fecha,
                'tasa_base': tasa_base,
                'comision_compra': moneda.comision_compra,
                'comision_venta': moneda.comision_venta,
                'precio_compra': tasa_base - moneda.comision_compra,
                'precio_venta': tasa_base + moneda.comision_venta
            })
        
        # Agregar datos actuales
        datos_ejemplo.append({
            'fecha': timezone.now().date(),
            'tasa_base': moneda.tasa_base,
            'comision_compra': moneda.comision_compra,
            'comision_venta': moneda.comision_venta,
            'precio_compra': moneda.tasa_base - moneda.comision_compra,
            'precio_venta': moneda.tasa_base + moneda.comision_venta
        })
        
        context = {
            'moneda': moneda,
            'historial': datos_ejemplo,
            'datos_json': datos_ejemplo  # Para JavaScript
        }
    else:
        # Convertir QuerySet a lista de diccionarios para JSON
        datos_json = []
        for registro in historial:
            datos_json.append({
                'fecha': registro.fecha.strftime('%Y-%m-%d'),
                'precio_compra': registro.precio_compra,
                'precio_venta': registro.precio_venta
            })
        
        context = {
            'moneda': moneda,
            'historial': historial,
            'datos_json': datos_json
        }
    
    return render(request, 'monedas/evolucion_cotizacion.html', context)

@login_required
def api_evolucion_cotizacion(request, pk):
    """
    API para obtener datos de evolución en formato JSON para gráficos
    """
    moneda = get_object_or_404(Moneda, pk=pk)
    
    # Obtener parámetro de rango temporal
    rango = request.GET.get('rango', 'mes')
    
    # Calcular fecha límite según el rango
    if rango == 'semana':
        fecha_limite = timezone.now().date() - timedelta(days=7)
    elif rango == 'mes':
        fecha_limite = timezone.now().date() - timedelta(days=30)
    elif rango == '6meses':
        fecha_limite = timezone.now().date() - timedelta(days=180)
    elif rango == 'año':
        fecha_limite = timezone.now().date() - timedelta(days=365)
    else:
        fecha_limite = timezone.now().date() - timedelta(days=30)
    
    # Obtener historial filtrado
    historial = HistorialCotizacion.objects.filter(
        moneda=moneda,
        fecha__gte=fecha_limite
    ).order_by('fecha')
    
    # Si no hay historial, generar datos de ejemplo
    if not historial.exists():
        datos = []
        dias = 7 if rango == 'semana' else (30 if rango == 'mes' else (180 if rango == '6meses' else 365))
        
        for i in range(dias, 0, -1):
            fecha = timezone.now().date() - timedelta(days=i)
            variacion = (i % 5) * 10
            tasa_base = moneda.tasa_base + variacion
            
            datos.append({
                'fecha': fecha.strftime('%d/%m/%Y'),
                'fecha_iso': fecha.strftime('%Y-%m-%d'),
                'precio_compra': tasa_base - moneda.comision_compra,
                'precio_venta': tasa_base + moneda.comision_venta
            })
        
        # Agregar dato actual
        datos.append({
            'fecha': timezone.now().date().strftime('%d/%m/%Y'),
            'fecha_iso': timezone.now().date().strftime('%Y-%m-%d'),
            'precio_compra': moneda.tasa_base - moneda.comision_compra,
            'precio_venta': moneda.tasa_base + moneda.comision_venta
        })
    else:
        datos = []
        for registro in historial:
            datos.append({
                'fecha': registro.fecha.strftime('%d/%m/%Y'),
                'fecha_iso': registro.fecha.strftime('%Y-%m-%d'),
                'precio_compra': registro.precio_compra,
                'precio_venta': registro.precio_venta
            })
    
    return JsonResponse({
        'moneda': {
            'nombre': moneda.nombre,
            'simbolo': moneda.simbolo
        },
        'datos': datos,
        'rango': rango
    })