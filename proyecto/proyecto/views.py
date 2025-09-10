from django.shortcuts import redirect, render
from django.http import HttpResponseForbidden
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from clientes.models import Cliente

from .forms import LoginForm

from cotizacion.models import Cotizacion
from monedas.models import Moneda

def inicio(request):
    """Vista para la página de inicio"""
    context = {}
    
    # Obtener las monedas activas
    monedas_activas = Moneda.objects.filter(activa=True)
    
    # Obtener todas las segmentaciones disponibles
    segmentaciones_lista = []
    for key, value in Cliente.BENEFICIOS_SEGMENTO.items():
        segmentaciones_lista.append({
            'id': key,
            'nombre': key.title(),
            'porcentaje_beneficio': value
        })
    context['segmentaciones'] = segmentaciones_lista
    
    # Obtener el segmento seleccionado (solo para administradores)
    segmento_seleccionado = None
    porcentaje_beneficio_admin = 0
    if request.user.has_perm('monedas.cotizacion'):
        segmento_id = request.GET.get('segmento')
        if segmento_id and segmento_id in Cliente.BENEFICIOS_SEGMENTO:
            segmento_seleccionado = segmento_id
            porcentaje_beneficio_admin = Cliente.BENEFICIOS_SEGMENTO[segmento_id]
        context['segmento_seleccionado'] = segmento_seleccionado
    
    # Si el usuario está autenticado
    if request.user.is_authenticated:
        cotizaciones = []
        for moneda in monedas_activas:
            ultima_cotizacion = (Cotizacion.objects
                               .filter(id_moneda=moneda)
                               .order_by('-fecha_cotizacion')
                               .first())
            
            if ultima_cotizacion:
                if hasattr(request.user, 'cliente_activo') and request.user.cliente_activo:
                    # Usuario u operador con cliente seleccionado
                    cliente = request.user.cliente_activo
                    precios = ultima_cotizacion.get_precios_cliente(cliente)
                elif segmento_seleccionado:
                    # Administrador con segmento seleccionado - usar porcentaje de beneficio específico
                    precios = {
                        'precio_compra': ultima_cotizacion.calcular_precio_compra(porcentaje_beneficio_admin),
                        'precio_venta': ultima_cotizacion.calcular_precio_venta(porcentaje_beneficio_admin)
                    }
                else:
                    # Administrador sin segmento seleccionado o usuario sin cliente - mostrar precios base
                    precios = {
                        'precio_compra': ultima_cotizacion.calcular_precio_compra(0),
                        'precio_venta': ultima_cotizacion.calcular_precio_venta(0)
                    }
                
                cotizaciones.append({
                    'moneda': moneda,
                    'simbolo': moneda.simbolo,
                    'precio_compra': precios['precio_compra'],
                    'precio_venta': precios['precio_venta'],
                    'fecha': ultima_cotizacion.fecha_cotizacion
                })
        context['cotizaciones'] = cotizaciones
    
    return render(request, 'inicio.html', context)

def custom_permission_denied_view(request, exception):
    """
    Vista personalizada para manejar errores 403 (Permission Denied)
    Se renderiza cuando un usuario autenticado no tiene permisos para acceder a una vista
    """
    return HttpResponseForbidden(render(request, '403.html').content)

def login_usuario(request):
    if request.user.is_authenticated:
        return redirect('usuarios:perfil')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido a Global Exchange, {user.first_name}!')
                next_page = request.GET.get('next', 'inicio')
                return redirect(next_page)
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})

def logout_usuario(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('inicio')