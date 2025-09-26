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


# ============================================================================
# DECORADORES PERSONALIZADOS PARA CONTROL DE PERMISOS
# ============================================================================

def tiene_algun_permiso(view_func):
    """
    Decorador que verifica si el usuario tiene al menos uno de los permisos necesarios
    para administrar monedas: gestión o activación.
    
    Este decorador permite acceso a vistas que requieren permisos relacionados con monedas
    pero no requieren un permiso específico, sino cualquiera de los permisos disponibles.
    
    Args:
        view_func (function): Función de vista a decorar
        
    Returns:
        function: Vista decorada con verificación de permisos
        
    Raises:
        PermissionDenied: Si el usuario no tiene ninguno de los permisos requeridos
        
    Example:
        @tiene_algun_permiso
        def mi_vista(request):
            return render(request, 'template.html')
            
    Note:
        - Redirige a login si el usuario no está autenticado
        - Verifica permisos: 'monedas.gestion' y 'monedas.activacion'
        - Útil para vistas que pueden ser accedidas por diferentes tipos de usuarios
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Verificar autenticación
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        # Permisos requeridos para administrar monedas
        permisos_requeridos = [
            'monedas.gestion',       # Permiso para gestionar monedas
            'monedas.activacion'     # Permiso para activar/desactivar monedas
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
    Decorador que verifica si el usuario tiene permisos para editar monedas.
    
    Este decorador permite acceso a vistas de edición que requieren permisos
    específicos para modificar datos de monedas o sus cotizaciones.
    
    Args:
        view_func (function): Función de vista a decorar
        
    Returns:
        function: Vista decorada con verificación de permisos de edición
        
    Raises:
        PermissionDenied: Si el usuario no tiene permisos de edición
        
    Example:
        @puede_editar
        def editar_moneda(request, pk):
            return render(request, 'monedas/editar.html')
            
    Note:
        - Redirige a login si el usuario no está autenticado
        - Verifica permisos: 'monedas.gestion' y 'monedas.cotizacion'
        - Usado para vistas que modifican datos de monedas
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Verificar autenticación
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        # Permisos requeridos para editar monedas
        permisos_requeridos = [
            'monedas.gestion',       # Permiso para editar monedas
            'monedas.cotizacion'     # Permiso para cambiar la tasa base de una moneda
        ]
        
        # Verificar si el usuario tiene al menos uno de los permisos
        for permiso in permisos_requeridos:
            if request.user.has_perm(permiso):
                return view_func(request, *args, **kwargs)
        
        # Si no tiene ningún permiso, denegar acceso
        raise PermissionDenied()

    return _wrapped_view


# ============================================================================
# VISTAS PARA GESTIÓN DE MONEDAS
# ============================================================================

@login_required
@permission_required('monedas.gestion', raise_exception=True)
def moneda_crear(request):
    """
    Vista para crear una nueva moneda en el sistema.
    
    Permite a usuarios con permisos de gestión crear nuevas monedas
    con sus respectivas configuraciones de tasas y comisiones.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP
        
    Returns:
        HttpResponse: Formulario de creación (GET) o redirección (POST exitoso)
        
    Template:
        monedas/moneda_form.html
        
    Context:
        - form: Instancia del formulario MonedaForm
        
    Note:
        - Requiere permiso 'monedas.gestion'
        - Muestra mensaje de éxito al crear la moneda
        - Redirige a lista de monedas después de creación exitosa
    """
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
    """
    Vista para listar y gestionar las monedas del sistema.
    
    Proporciona una interfaz para visualizar todas las monedas con funcionalidades
    de búsqueda, filtrado y cambio de estado (activar/desactivar). Incluye
    estadísticas resumidas del estado de las monedas.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP
        
    Returns:
        HttpResponse: Lista de monedas con funcionalidades de gestión
        
    Template:
        monedas/moneda_lista.html
        
    Context:
        - monedas: QuerySet de monedas (filtradas si hay búsqueda)
        - monedas_activas: Número de monedas activas en el filtro actual
        - monedas_inactivas: Número de monedas inactivas en el filtro actual
        - busqueda: Término de búsqueda actual
        - total_monedas_sistema: Total de monedas sin filtros
        
    POST Parameters:
        - cambiar_estado: Flag para indicar cambio de estado
        - moneda_id: ID de la moneda a cambiar de estado
        - next: URL de redirección opcional después del cambio
        
    GET Parameters:
        - busqueda: Término para filtrar monedas por nombre o símbolo
        
    Note:
        - Permite cambio de estado (activar/desactivar) mediante POST
        - Búsqueda en nombre y símbolo de monedas
        - Muestra estadísticas de monedas activas e inactivas
        - Ordena las monedas alfabéticamente por nombre
    """
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
    
    # Obtener todas las monedas para estadísticas globales
    todas_las_monedas = Moneda.objects.all()
    monedas = todas_las_monedas
    
    # Manejar búsqueda por nombre o símbolo
    busqueda = request.GET.get('busqueda', '').strip()
    if busqueda:
        monedas = monedas.filter(
            Q(nombre__icontains=busqueda) | 
            Q(simbolo__icontains=busqueda)
        )
    
    # Ordenar por nombre para mejor UX
    monedas = monedas.order_by('nombre')
    
    # Calcular estadísticas para el set filtrado
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
    """
    Vista para editar una moneda existente.
    
    Permite la modificación de datos de moneda con control de permisos
    granular que limita los campos editables según los permisos del usuario.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP
        pk (int): Clave primaria de la moneda a editar
        
    Returns:
        HttpResponse: Formulario de edición (GET) o redirección (POST exitoso)
        
    Template:
        monedas/moneda_form.html
        
    Context:
        - form: Instancia del formulario MonedaForm (con campos limitados según permisos)
        - moneda: Instancia de la moneda siendo editada
        
    Note:
        - Si usuario no tiene permiso 'monedas.gestion': solo puede editar tasa_base
        - Si usuario tiene 'monedas.gestion': puede editar todos los campos
        - Control granular de permisos mediante modificación dinámica del formulario
    """
    moneda = get_object_or_404(Moneda, pk=pk)
    
    # Instancia el formulario normalmente
    if request.method == 'POST':
        form = MonedaForm(request.POST, instance=moneda)
    else:
        form = MonedaForm(instance=moneda)

    # Control granular de permisos - eliminar campos según permisos del usuario
    if not request.user.has_perm('monedas.gestion'):
        # Usuario solo con permiso de cotización: solo puede editar tasa_base
        form.fields.pop('nombre')
        form.fields.pop('simbolo')
        form.fields.pop('decimales')

    # Procesar el formulario si es POST
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
    """
    Vista para mostrar los detalles completos de una moneda.
    
    Proporciona información detallada de una moneda incluyendo precios
    calculados de compra y venta sin aplicar beneficios de cliente.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP
        pk (int): Clave primaria de la moneda a mostrar
        
    Returns:
        HttpResponse: Página de detalles de la moneda
        
    Template:
        monedas/moneda_detalles.html
        
    Context:
        - moneda: Instancia de la moneda
        - precio_compra: Precio de compra sin beneficios
        - precio_venta: Precio de venta sin beneficios
        
    Note:
        - Calcula precios sin beneficios (cliente=None)
        - Útil para administradores que necesitan ver precios base
    """
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
    """
    Vista para listar todos los límites globales configurados en el sistema.
    
    Proporciona una interfaz administrativa para gestionar los límites globales
    que restringen las transacciones de todos los clientes. Muestra el historial
    de límites y destaca el límite actualmente vigente.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP
        
    Returns:
        HttpResponse: Lista de límites globales
        
    Template:
        monedas/lista_limites.html
        
    Context:
        - title: Título de la página
        - limites: QuerySet de todos los límites ordenados por fecha de inicio
        - limite_vigente: Instancia del límite actualmente activo
        
    Note:
        - Requiere permiso 'monedas.gestion'
        - Ordena límites por fecha de inicio descendente
        - Identifica visualmente el límite vigente
    """
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
    """
    Vista para crear un nuevo límite global.
    
    Permite a administradores crear nuevos límites que definirán las
    restricciones de transacciones para todos los clientes del sistema.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP
        
    Returns:
        HttpResponse: Formulario de creación (GET) o redirección (POST exitoso)
        
    Template:
        monedas/limite_form.html
        
    Context:
        - title: Título de la página
        - form: Instancia del formulario LimiteGlobalForm
        - accion: Texto descriptivo de la acción ('Crear Límite')
        
    Note:
        - Requiere permiso 'monedas.gestion'
        - Valida que los límites sean coherentes (diario <= mensual)
        - Muestra mensajes de éxito/error apropiados
    """
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
    """
    Vista para editar un límite global existente.
    
    Permite modificar los valores de un límite global ya configurado.
    Útil para ajustar límites según cambios en regulaciones o políticas
    institucionales.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP
        pk (int): Clave primaria del límite a editar
        
    Returns:
        HttpResponse: Formulario de edición (GET) o redirección (POST exitoso)
        
    Template:
        monedas/limite_form.html
        
    Context:
        - title: Título de la página
        - form: Instancia del formulario con datos actuales del límite
        - accion: Texto descriptivo de la acción ('Actualizar Límite')
        - limite: Instancia del límite siendo editado
        
    Note:
        - Requiere permiso 'monedas.gestion'
        - Mantiene las validaciones de coherencia entre límites
        - Útil para ajustar límites sin crear nuevos registros
    """
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
    """
    Vista para activar un límite específico y desactivar todos los demás.
    
    Permite cambiar el límite vigente en el sistema. Como solo puede haber
    un límite activo al mismo tiempo, esta función desactiva automáticamente
    todos los otros límites al activar el seleccionado.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP
        pk (int): Clave primaria del límite a activar
        
    Returns:
        HttpResponse: Redirección a la lista de límites
        
    POST Parameters:
        - Requiere método POST para confirmar la acción
        
    Note:
        - Requiere permiso 'monedas.gestion'
        - Solo permite POST para evitar activaciones accidentales
        - Usa transacción atómica para garantizar consistencia
        - Desactiva todos los demás límites automáticamente
    """
    if request.method == 'POST':
        limite = get_object_or_404(LimiteGlobal, pk=pk)
        
        try:
            with transaction.atomic():
                # Desactivar todos los demás límites
                LimiteGlobal.objects.exclude(pk=pk).update(activo=False)
                
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
    """
    API AJAX para consultar los límites disponibles de un cliente específico.
    
    Endpoint que proporciona información en tiempo real sobre el estado
    de los límites de un cliente, incluyendo consumos actuales y disponibilidades.
    Usado por interfaces que necesitan mostrar límites antes de procesar transacciones.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP (debe ser GET)
        
    Returns:
        JsonResponse: Respuesta JSON con información de límites
        
    GET Parameters:
        - cliente_id: ID del cliente para consultar límites
        
    Response Format:
        Success (200):
        {
            'success': True,
            'data': {
                'cliente': {'id': int, 'nombre': str},
                'limites': {
                    'limite_diario': int,
                    'limite_mensual': int,
                    'consumo_diario': int,
                    'consumo_mensual': int,
                    'disponible_diario': int,
                    'disponible_mensual': int,
                    'porcentaje_uso_diario': float,
                    'porcentaje_uso_mensual': float
                }
            }
        }
        
        Error (400):
        {
            'success': False,
            'error': 'Descripción del error'
        }
        
    Note:
        - Requiere autenticación
        - Solo acepta método GET
        - Útil para validaciones en tiempo real en formularios
        - Maneja errores de cliente no encontrado
    """
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
    """
    API AJAX para validar si una transacción puede realizarse sin superar límites.
    
    Endpoint que realiza validaciones previas de límites sin procesar la transacción real.
    Útil para validaciones en tiempo real en formularios de transacciones, permitiendo
    informar al usuario si su transacción será aprobada antes de enviarla.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP (debe ser POST)
        
    Returns:
        JsonResponse: Respuesta JSON con resultado de validación
        
    POST Parameters:
        - cliente_id: ID del cliente que realizará la transacción
        - moneda_id: ID de la moneda de la transacción
        - tipo_transaccion: 'COMPRA' o 'VENTA'
        - monto: Monto de la transacción en la moneda especificada
        
    Response Format:
        Success (200):
        {
            'success': True,
            'data': {
                'valida': True,
                'monto_guaranies': int,
                'limites_actualizados': {límites disponibles después de la transacción}
            }
        }
        
        Error (400):
        {
            'success': False,
            'error': 'Descripción del error'
        }
        
    Note:
        - Requiere autenticación
        - Solo acepta método POST
        - NO procesa la transacción, solo valida límites
        - Convierte montos a guaraníes para validación
        - Retorna límites actualizados proyectados
    """
    if request.method == 'POST':
        try:
            # Obtener y validar parámetros requeridos
            cliente_id = request.POST.get('cliente_id')
            moneda_id = request.POST.get('moneda_id')
            tipo_transaccion = request.POST.get('tipo_transaccion')
            monto = request.POST.get('monto')
            
            # Validar que todos los parámetros estén presentes
            if not all([cliente_id, moneda_id, tipo_transaccion, monto]):
                return JsonResponse({
                    'success': False,
                    'error': 'Todos los parámetros son requeridos'
                })
            
            # Obtener objetos del modelo
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
            
            # Validar límites (sin procesar la transacción real)
            monto_guaranies = LimiteService.convertir_a_guaranies(
                monto, moneda, tipo_transaccion, cliente
            )
            
            LimiteService.validar_limite_transaccion(cliente, monto_guaranies)
            
            # Si llegamos aquí, la transacción es válida
            limites_restantes = LimiteService.obtener_limites_disponibles(cliente)
            
            return JsonResponse({
                'success': True,
                'data': {
                    'valida': True,
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