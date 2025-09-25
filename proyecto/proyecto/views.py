from django.shortcuts import redirect, render
from django.http import HttpResponseForbidden
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from clientes.models import Cliente
from .forms import LoginForm, SimuladorForm
from monedas.models import Moneda
from decimal import Decimal
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

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
    cotizaciones = []
    for moneda in monedas_activas:
        if hasattr(request.user, 'cliente_activo') and request.user.cliente_activo:
            # Usuario u operador con cliente seleccionado
            cliente = request.user.cliente_activo
            precios = moneda.get_precios_cliente(cliente)
        elif segmento_seleccionado:
            # Administrador con segmento seleccionado - usar porcentaje de beneficio específico
            precios = {
                'precio_compra': moneda.calcular_precio_compra(porcentaje_beneficio_admin),
                'precio_venta': moneda.calcular_precio_venta(porcentaje_beneficio_admin)
            }
        else:
            # Administrador sin segmento seleccionado o usuario sin cliente - mostrar precios base
            precios = {
                'precio_compra': moneda.calcular_precio_compra(0),
                'precio_venta': moneda.calcular_precio_venta(0)
            }
        
        cotizaciones.append({
            'moneda': moneda,
            'simbolo': moneda.simbolo,
            'precio_compra': precios['precio_compra'],
            'precio_venta': precios['precio_venta'],
            'fecha': moneda.fecha_cotizacion
        })
    cotizaciones.sort(key=lambda x: x['fecha'], reverse=True)
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

def simular(request):
    if request.method == 'GET':
        monedas = Moneda.objects.filter(activa=True)
        # Obtener el cliente activo si el usuario está autenticado
        cliente = None
        if request.user.is_authenticated and hasattr(request.user, 'cliente_activo'):
            cliente = request.user.cliente_activo
        
        # Crear el formulario para pasar las opciones de recargo
        form = SimuladorForm(cliente=cliente)
        
        return render(request, 'simulador.html', {
            'monedas': monedas,
            'form': form
        })

    elif request.method == 'POST':
        try:
            # Obtener el cliente activo si el usuario está autenticado
            cliente = None
            if request.user.is_authenticated and hasattr(request.user, 'cliente_activo'):
                cliente = request.user.cliente_activo
            
            # Crear el formulario con los datos POST y el cliente
            form = SimuladorForm(request.POST, cliente=cliente)
            
            if form.is_valid():
                # Si el formulario es válido, realizar la conversión
                resultado = form.realizar_conversion()
                return JsonResponse(resultado)
            else:
                # Si hay errores de validación, devolverlos
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'Ocurrió un error al procesar la conversión.'
            })