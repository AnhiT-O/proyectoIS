from datetime import timedelta
from django.utils import timezone
from django.shortcuts import redirect, render
from django.http import HttpResponseForbidden
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .forms import LoginForm, SimuladorForm
from monedas.models import Moneda
from django.http import JsonResponse
from transacciones.models import Transaccion, calcular_conversion

def inicio(request):
    """
    Vista para la página de inicio. 

    - Para usuarios no autenticados muestra las cotizaciones base de las monedas activas y un simulador de conversiones.

    - Para usuarios autenticados con un cliente seleccionado se le muestra además las cotizaciones personalizadas según el cliente y la opción de operar con divisas.

    - Para usuarios con permiso de gestionar cotizaciones se le muestra un selector de segmentaciones para ver las cotizaciones según el segmento seleccionado 
    (Minorista, Corporativo, VIP).

    Note:
        La barra de navegación se muestra todo el tiempo, pero con diferentes opciones según el estado de autenticación y permisos del usuario.

        - Usuarios no autenticados: opciones para iniciar sesión o registrarse.

        - Usuarios autenticados sin permisos especiales: opciones para ver perfil, ver clientes y cerrar sesión.

        - Usuarios con permisos especiales: panel de gestiones según sus permisos.
    """
    context = {}
    # Obtener las monedas activas
    monedas_activas = Moneda.objects.filter(activa=True)
    
    # Preparar lista de segmentaciones para el template
    segmentaciones= [
        {'segmento': 'Minorista', 'porcentaje_beneficio': 0},
        {'segmento': 'Corporativo', 'porcentaje_beneficio': 5},
        {'segmento': 'VIP', 'porcentaje_beneficio': 10}
    ]
    
    # Obtener el segmento seleccionado
    segmento_seleccionado = None
    if request.user.has_perm('monedas.cotizacion'):
        segmento_id = request.GET.get('segmento')
        if segmento_id in ['Minorista', 'Corporativo', 'VIP']:
            segmento_seleccionado = segmento_id
        context['segmento_seleccionado'] = segmento_seleccionado
        context['segmentaciones_listas'] = segmentaciones
    
    cotizaciones = []
    for moneda in monedas_activas:
        if request.user.is_authenticated and request.user.cliente_activo:
            # Usuario u operador con cliente seleccionado
            precios = moneda.get_precios_cliente(request.user.cliente_activo)
        elif segmento_seleccionado:
            # Administrador con segmento seleccionado - usar segmento específico
            precios = {
                'precio_compra': moneda.calcular_precio_compra(segmento_seleccionado.lower()),
                'precio_venta': moneda.calcular_precio_venta(segmento_seleccionado.lower())
            }
        else:
            # Administrador sin segmento seleccionado o usuario sin cliente - mostrar precios base
            precios = {
                'precio_compra': moneda.calcular_precio_compra(),
                'precio_venta': moneda.calcular_precio_venta()
            }
        
        cotizaciones.append({
            'moneda': moneda,
            'precio_compra': precios['precio_compra'],
            'precio_venta': precios['precio_venta'],
        })
    cotizaciones.sort(key=lambda x: x['moneda'].fecha_cotizacion, reverse=True)
    context['cotizaciones'] = cotizaciones
    
    return render(request, 'inicio.html', context)

def custom_permission_denied_view(request, exception=None):
    """
    Vista personalizada para manejar errores 403 (Permission Denied). 
    Se renderiza cuando un usuario autenticado no tiene permisos para acceder a una vista
    """
    return HttpResponseForbidden(render(request, '403.html').content)

def login_usuario(request):
    """
    Vista para manejar el inicio de sesión de usuarios.
    """
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
                transacciones_pasadas = Transaccion.objects.filter(usuario=request.user, estado='Pendiente')
                if transacciones_pasadas:
                    for t in transacciones_pasadas:
                        if t.fecha_hora < timezone.now() - timedelta(minutes=5):
                            t.estado = 'Cancelada'
                            t.razon = 'Expira el tiempo para confirmar la transacción'
                            t.save()
                messages.success(request, f'¡Bienvenido a Global Exchange, {user.first_name}!')
                next_page = request.GET.get('next', 'inicio')
                return redirect(next_page)
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})

def logout_usuario(request):
    """
    Vista para manejar el cierre de sesión de usuarios.
    """
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('inicio')

def simular(request):
    """
    Vista para manejar el simulador de conversiones de moneda. 
    Se maneja tanto la visualización del formulario como el procesamiento de las solicitudes AJAX para realizar las conversiones.
    """
    if request.method == 'GET':
        form = SimuladorForm()
        return render(request, 'simulador.html', {'form': form})

    elif request.method == 'POST':
        try:
            # Obtener el cliente activo si el usuario está autenticado
            cliente = None
            if request.user.is_authenticated and request.user.cliente_activo:
                cliente = request.user.cliente_activo

            # Crear el formulario con los datos POST
            form = SimuladorForm(request.POST)
            if form.is_valid():
                # Si el formulario es válido, realizar la conversión
                monto = form.cleaned_data['monto']
                moneda = form.cleaned_data['moneda']
                operacion = form.cleaned_data['operacion']
                medio_pago = form.cleaned_data['medio_pago']
                medio_cobro = form.cleaned_data['medio_cobro']

                resultado = calcular_conversion(monto, moneda, operacion, medio_pago, medio_cobro, cliente.segmento if cliente is not None else 'minorista')
                respuesta = {
                    'success': True,
                    'precio_base': float(resultado['precio_base']),
                    'beneficio_segmento': float(resultado['beneficio_segmento']),
                    'monto_recargo_pago': float(resultado['monto_recargo_pago']),
                    'monto_recargo_cobro': float(resultado['monto_recargo_cobro']),
                    'monto_final': float(resultado['monto']),
                    'redondeo_monto': True if resultado['redondeo_efectivo_monto'] > 0 else False,
                    'redondeo_precio_final': True if resultado['redondeo_efectivo_precio_final'] > 0 else False,
                    'precio_final': float(resultado['precio_final'])
                }

                return JsonResponse(respuesta)
            else:
                # Si hay errores de validación, devolverlos
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })