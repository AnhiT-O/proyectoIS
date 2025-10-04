from datetime import timedelta, timezone
from django.shortcuts import redirect, render
from django.http import HttpResponseForbidden
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .forms import LoginForm, SimuladorForm
from monedas.models import Moneda
from django.http import JsonResponse
from transacciones.models import Transaccion, calcular_conversion, redondear_efectivo

def inicio(request):
    """
    Vista para la página de inicio. Muestra las cotizaciones de las monedas activas.
    -   Si el usuario es un operador con un cliente seleccionado, muestra los precios personalizados.
    -   Si el usuario es un administrador, puede seleccionar un segmento para ver precios con beneficios específicos.
    -   Si el usuario no está autenticado, muestra los precios base sin beneficios.
    """
    context = {}
    # Obtener las monedas activas
    monedas_activas = Moneda.objects.filter(activa=True)
    
    # Obtener todas las segmentaciones disponibles
    segmentaciones_lista = {
        'minorista': 0,
        'corporativo': 5,
        'vip': 10
    }
    
    # Obtener el segmento seleccionado
    segmento_seleccionado = None
    porcentaje_beneficio_admin = 0
    if request.user.has_perm('monedas.cotizacion'):
        segmento_id = request.GET.get('segmento')
        if segmento_id and segmento_id in ['minorista', 'corporativo', 'vip']:
            segmento_seleccionado = segmento_id
            porcentaje_beneficio_admin = segmentaciones_lista[segmento_seleccionado]
        context['segmento_seleccionado'] = segmento_seleccionado
    
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
    """
    if request.method == 'GET':
        form = SimuladorForm()
        
        return render(request, 'simulador.html', {
            'form': form
        })

    elif request.method == 'POST':
        try:
            # Obtener el cliente activo si el usuario está autenticado
            cliente = None
            if request.user.is_authenticated and hasattr(request.user, 'cliente_activo'):
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