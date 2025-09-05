from django.shortcuts import redirect, render
from django.http import HttpResponseForbidden
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from clientes.models import Cliente

from .forms import LoginForm

from cotizacion.models import Cotizacion
from monedas.models import Moneda
from django.utils import timezone
from datetime import timedelta
from django.db.models import Max

def inicio(request):
    """Vista para la página de inicio"""
    context = {}
    
    # Obtener las monedas activas
    monedas_activas = Moneda.objects.filter(activa=True)
    
    # Obtener las últimas cotizaciones del día para cada moneda
    fecha_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Si el usuario está autenticado y tiene un cliente activo
    if request.user.is_authenticated and hasattr(request.user, 'cliente_activo') and request.user.cliente_activo:
        cliente = request.user.cliente_activo
        # Obtener cotizaciones según el segmento del cliente
        cotizaciones = []
        for moneda in monedas_activas:
            ultima_cotizacion = (Cotizacion.objects
                               .filter(id_moneda=moneda, 
                                     fecha_cotizacion__gte=fecha_inicio)
                               .order_by('-fecha_cotizacion')
                               .first())
            if ultima_cotizacion:
                precios = ultima_cotizacion.get_precios_cliente(cliente)
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