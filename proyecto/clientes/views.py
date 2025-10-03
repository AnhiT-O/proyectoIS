"""
Módulo de vistas para la gestión de clientes.

Este módulo contiene todas las vistas necesarias para el CRUD de clientes,
incluyendo funcionalidades de creación, listado, detalle, edición y gestión
de medios de pago y acreditación. También incluye funciones de utilidad
para el control de acceso y navegación.

Autor: Equipo de desarrollo
Fecha: 2025
"""

from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q
from django.conf import settings
from .models import Cliente
from .forms import ClienteForm, AgregarTarjetaForm
from medios_acreditacion.models import CuentaBancaria, Billetera
from medios_acreditacion.forms import CuentaBancariaForm, BilleteraForm
from transacciones.models import Transaccion
from django.db import models
import stripe
import logging

# Configurar Stripe y logging
stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

def verificar_acceso_cliente(user, cliente):
    """
    Verifica si un usuario tiene acceso para operar con un cliente específico.

    Esta función implementa un sistema de acceso híbrido que permite el acceso
    a un cliente a través de dos mecanismos:
    1. Permisos administrativos globales (clientes.gestion)
    2. Asociación directa usuario-cliente

    Args:
        user: Instancia del usuario que solicita acceso
        cliente: Instancia del cliente al que se solicita acceso

    Returns:
        bool: True si el usuario tiene acceso, False en caso contrario

    Examples:
        >>> usuario_admin = Usuario.objects.get(id=1)  # Con permisos admin
        >>> usuario_operador = Usuario.objects.get(id=2)  # Sin permisos admin
        >>> cliente = Cliente.objects.get(id=1)
        >>> verificar_acceso_cliente(usuario_admin, cliente)  # True
        >>> verificar_acceso_cliente(usuario_operador, cliente)  # Depende de asociación
    """
    return (user.has_perm('clientes.gestion') or 
            cliente in user.clientes_operados.all())

def get_cliente_detalle_redirect(request, cliente_pk):
    """
    Determina la URL correcta de redirección según el tipo de usuario.

    Esta función analiza el contexto del usuario y su origen de navegación
    para determinar la vista de detalle de cliente apropiada, proporcionando
    una experiencia de navegación coherente.

    Args:
        request: Objeto HttpRequest con información de la petición
        cliente_pk: Clave primaria del cliente

    Returns:
        HttpResponseRedirect: Redirección a la vista apropiada

    Logic:
        - Si viene de la sección usuarios o no tiene permisos admin: vista de usuario
        - Si tiene permisos admin y viene de gestión: vista administrativa

    Examples:
        >>> # Usuario operador sin permisos admin
        >>> redirect_response = get_cliente_detalle_redirect(request, 1)
        >>> # Redirige a: /usuarios/cliente/1/
        
        >>> # Usuario administrador
        >>> redirect_response = get_cliente_detalle_redirect(request, 1)
        >>> # Redirige a: /clientes/1/
    """
    referer = request.META.get('HTTP_REFERER', '')
    if 'usuarios/cliente' in referer or not request.user.has_perm('clientes.gestion'):
        return redirect('usuarios:detalle_cliente', cliente_id=cliente_pk)
    else:
        return redirect('clientes:cliente_detalle', pk=cliente_pk)

def get_cliente_detalle_url(request, cliente_pk):
    """
    Determina la URL correcta de detalle del cliente para uso en templates.

    Similar a get_cliente_detalle_redirect, pero retorna la URL como string
    para ser utilizada en enlaces y formularios dentro de templates.

    Args:
        request: Objeto HttpRequest con información de la petición
        cliente_pk: Clave primaria del cliente

    Returns:
        str: URL string de la vista de detalle apropiada

    Examples:
        >>> # Para usuario operador
        >>> url = get_cliente_detalle_url(request, 1)
        >>> print(url)  # '/usuarios/cliente/1/'
        
        >>> # Para administrador
        >>> url = get_cliente_detalle_url(request, 1)  
        >>> print(url)  # '/clientes/1/'
    """
    referer = request.META.get('HTTP_REFERER', '')
    if 'usuarios/cliente' in referer or not request.user.has_perm('clientes.gestion'):
        return f'/usuarios/cliente/{cliente_pk}/'
    else:
        return f'/clientes/{cliente_pk}/'

def procesar_medios_acreditacion_cliente(cliente, usuario):
    """
    Procesa y obtiene los medios de acreditación asociados a un cliente.

    Esta función auxiliar centraliza la lógica de obtención de medios de
    acreditación y determinación de permisos del usuario para presentar
    la información de manera consistente en las vistas.

    Args:
        cliente: Instancia del cliente cuyos medios se van a procesar
        usuario: Instancia del usuario que solicita la información

    Returns:
        dict: Diccionario con la siguiente estructura:
            - es_administrador (bool): Si el usuario tiene permisos administrativos
            - cuentas_bancarias (QuerySet): Cuentas bancarias del cliente
            - billeteras (QuerySet): Billeteras electrónicas del cliente

    Examples:
        >>> cliente = Cliente.objects.get(id=1)
        >>> usuario = request.user
        >>> datos = procesar_medios_acreditacion_cliente(cliente, usuario)
        >>> print(f"Es admin: {datos['es_administrador']}")
        >>> print(f"Cuentas: {datos['cuentas_bancarias'].count()}")
    """
    # Determinar si es administrador
    es_administrador = usuario.has_perm('clientes.gestion')
    
    # Obtener medios de acreditación
    cuentas_bancarias = cliente.cuentas_bancarias.all()
    billeteras = cliente.billeteras.all()
    
    return {
        'es_administrador': es_administrador,
        'cuentas_bancarias': cuentas_bancarias,
        'billeteras': billeteras,
    }

@login_required
@permission_required('clientes.gestion', raise_exception=True)
def cliente_crear(request):
    """
    Vista para crear un nuevo cliente.

    Permite a los usuarios con permisos administrativos crear nuevos clientes
    en el sistema mediante un formulario de Django. Maneja tanto la presentación
    del formulario (GET) como el procesamiento de los datos (POST).

    Args:
        request: Objeto HttpRequest con la información de la petición

    Returns:
        HttpResponse: Renderiza el formulario o redirecciona tras creación exitosa

    Decorators:
        - @login_required: Requiere usuario autenticado
        - @permission_required: Requiere permiso 'clientes.gestion'

    Template:
        clientes/cliente_form.html

    Context:
        - form: Instancia del formulario ClienteForm

    Examples:
        >>> # GET: Muestra el formulario vacío
        >>> # POST: Procesa datos y crea cliente si es válido
    """
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, 'Cliente creado exitosamente.')
            return redirect('clientes:cliente_detalle', pk=cliente.pk)
    else:
        form = ClienteForm()
    return render(request, 'clientes/cliente_form.html', {'form': form})

@login_required
@permission_required('clientes.gestion', raise_exception=True)
def cliente_lista(request):
    """
    Vista para listar todos los clientes con funciones de filtrado y búsqueda.

    Presenta una lista paginada de clientes con opciones de filtrado por segmento
    y búsqueda por nombre o documento. Incluye estadísticas por segmento para
    facilitar la navegación y gestión.

    Args:
        request: Objeto HttpRequest con la información de la petición

    Returns:
        HttpResponse: Página con la lista de clientes filtrada

    Decorators:
        - @login_required: Requiere usuario autenticado
        - @permission_required: Requiere permiso 'clientes.gestion'

    Template:
        clientes/cliente_lista.html

    Context:
        - clientes: QuerySet de clientes filtrados
        - hay_clientes: Boolean indicando si existen clientes
        - busqueda: Término de búsqueda aplicado
        - segmento_filtro: Segmento seleccionado para filtrar
        - stats_segmentos: Estadísticas de clientes por segmento

    Query Parameters:
        - segmento: Filtro por segmento (vip, corporativo, minorista)
        - busqueda: Término de búsqueda por nombre o documento
    """
    # Obtener todos los clientes para verificar si hay alguno
    todos_los_clientes = Cliente.objects.all()
    
    # Obtener clientes para mostrar (con filtros aplicados)
    clientes = todos_los_clientes
    
    # Manejar filtro por segmento
    segmento_filtro = request.GET.get('segmento', '').strip()
    if segmento_filtro and segmento_filtro in ['vip', 'corporativo', 'minorista']:
        clientes = clientes.filter(segmento=segmento_filtro)
    
    # Manejar búsqueda
    busqueda = request.GET.get('busqueda', '').strip()
    if busqueda:
        clientes = clientes.filter(
            Q(nombre__icontains=busqueda) |
            Q(numero_documento__icontains=busqueda)
        )
    
    # Ordenar por nombre
    clientes = clientes.order_by('nombre')
    
    # Estadísticas por segmento para mostrar en filtros
    stats_segmentos = {
        'vip': todos_los_clientes.filter(segmento='vip').count(),
        'corporativo': todos_los_clientes.filter(segmento='corporativo').count(),
        'minorista': todos_los_clientes.filter(segmento='minorista').count(),
    }
    
    context = {
        'clientes': clientes,
        'hay_clientes': todos_los_clientes.exists(),
        'busqueda': busqueda,
        'segmento_filtro': segmento_filtro,
        'stats_segmentos': stats_segmentos,
    }
    return render(request, 'clientes/cliente_lista.html', context)

@login_required
def cliente_detalle(request, pk):
    """
    Vista de detalle del cliente con acceso híbrido.

    Muestra la información detallada de un cliente específico, incluyendo
    datos personales, medios de acreditación y tarjetas de Stripe. Implementa
    un sistema de acceso híbrido donde tanto administradores como usuarios
    operadores asociados pueden ver los detalles.

    Args:
        request: Objeto HttpRequest con la información de la petición
        pk: Clave primaria del cliente a mostrar

    Returns:
        HttpResponse: Página de detalle del cliente o redirección si no tiene acceso

    Decorators:
        - @login_required: Requiere usuario autenticado

    Template:
        clientes/cliente_detalle.html

    Context:
        - cliente: Instancia del cliente
        - tarjetas_stripe: Lista de tarjetas de crédito del cliente
        - total_tarjetas: Número total de tarjetas
        - es_administrador: Si el usuario tiene permisos administrativos
        - cuentas_bancarias: Cuentas bancarias del cliente
        - billeteras: Billeteras electrónicas del cliente

    Access Control:
        - Administradores con permiso 'clientes.gestion': Acceso completo
        - Usuarios operadores asociados: Acceso limitado al cliente específico
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    
    tarjetas_stripe = cliente.obtener_tarjetas_stripe()
    # Verificar acceso híbrido (admin o usuario asociado)
    if not verificar_acceso_cliente(request.user, cliente):
        messages.error(request, 'No tienes permisos para ver este cliente.')
        return redirect('inicio')
    
    # Usar función auxiliar para procesar medios de acreditación
    medios_data = procesar_medios_acreditacion_cliente(cliente, request.user)
    
    context = {
        'cliente': cliente,
        'tarjetas_stripe': tarjetas_stripe,
        'total_tarjetas': len(tarjetas_stripe),
        **medios_data
    }
    return render(request, 'clientes/cliente_detalle.html', context)

@login_required
@permission_required('clientes.gestion', raise_exception=True)
def cliente_editar(request, pk):
    """
    Vista para editar un cliente existente.

    Permite a los usuarios con permisos administrativos modificar la información
    de un cliente existente mediante un formulario prellenado con los datos actuales.

    Args:
        request: Objeto HttpRequest con la información de la petición
        pk: Clave primaria del cliente a editar

    Returns:
        HttpResponse: Formulario de edición o redirección tras actualización exitosa

    Decorators:
        - @login_required: Requiere usuario autenticado
        - @permission_required: Requiere permiso 'clientes.gestion'

    Template:
        clientes/cliente_form.html

    Context:
        - form: Instancia del formulario ClienteForm con datos del cliente
        - cliente: Instancia del cliente siendo editado

    Examples:
        >>> # GET: Muestra formulario prellenado con datos actuales
        >>> # POST: Procesa cambios y actualiza si son válidos
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado exitosamente.')
            return redirect('clientes:cliente_detalle', pk=cliente.pk)
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'clientes/cliente_form.html', {'form': form, 'cliente': cliente})


@login_required
def agregar_tarjeta(request, pk):
    """
    Vista para agregar tarjeta de crédito a un cliente con acceso híbrido.

    Permite tanto a administradores como a usuarios operadores asociados
    agregar tarjetas de crédito a un cliente específico mediante integración
    con Stripe Elements.

    Args:
        request: Objeto HttpRequest con la información de la petición
        pk: Clave primaria del cliente al que agregar la tarjeta

    Returns:
        HttpResponse: Formulario de tarjeta o redirección tras procesamiento

    Decorators:
        - @login_required: Requiere usuario autenticado

    Template:
        clientes/cliente_agregar_cuenta.html

    Context:
        - form: Instancia del formulario AgregarTarjetaForm
        - cliente: Instancia del cliente
        - stripe_public_key: Clave pública de Stripe para el frontend

    Access Control:
        - Administradores con permiso 'clientes.gestion': Acceso completo
        - Usuarios operadores asociados al cliente: Acceso específico

    Note:
        Esta vista trabaja con Stripe Elements en el frontend para
        procesamiento seguro de datos de tarjetas de crédito.
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Verificar acceso híbrido (admin o usuario asociado)
    if not verificar_acceso_cliente(request.user, cliente):
        messages.error(request, 'No tienes permisos para gestionar las tarjetas de este cliente.')
        return redirect('inicio')
    
    if request.method == 'POST':
        form = AgregarTarjetaForm(request.POST, cliente=cliente)
        if form.is_valid():
            numero_cuenta = form.cleaned_data['numero_cuenta']
            
            # Buscar si existe una cuenta con EXACTAMENTE los mismos datos
            cuenta_existente = MedioPagoCliente.objects.filter(
                cliente=cliente,
                medio_pago__tipo='transferencia',
                numero_cuenta=numero_cuenta,
                nombre_titular_cuenta=form.cleaned_data['nombre_titular_cuenta'],
                banco=form.cleaned_data.get('banco', ''),
                tipo_cuenta=form.cleaned_data.get('tipo_cuenta', '')
            ).first()
            
            if cuenta_existente:
                # Si existe con exactamente los mismos datos pero está inactiva, reactivarla
                if not cuenta_existente.activo or cuenta_existente.is_deleted:
                    cuenta_existente.activo = True
                    cuenta_existente.is_deleted = False
                    cuenta_existente.save()
                    
                    messages.success(request, 'Cuenta bancaria agregada exitosamente.')
                else:
                    messages.warning(request, 'Esta cuenta bancaria ya está activa y asociada al cliente.')
            else:
                # Verificar si existe una cuenta con el mismo número pero datos diferentes
                cuenta_mismo_numero = MedioPagoCliente.objects.filter(
                    cliente=cliente,
                    medio_pago__tipo='transferencia',
                    numero_cuenta=numero_cuenta
                ).first()
                
                if cuenta_mismo_numero:
                    messages.error(request, 'Ya existe una cuenta con este número pero con datos diferentes. Si desea cambiar los datos, primero debe eliminar la cuenta anterior.')
                    return render(request, 'clientes/cliente_agregar_cuenta.html', {
                        'form': form,
                        'cliente': cliente,
                        'titulo': 'Agregar Cuenta Bancaria',
                        'cancelar_url': get_cliente_detalle_url(request, cliente.pk)
                    })
                
                # Obtener o crear el medio de pago tipo transferencia
                medio_pago_transferencia, created = MedioPago.objects.get_or_create(
                    tipo='transferencia',
                    defaults={'activo': True}
                )
                
                # Crear un nuevo registro en la tabla intermedia
                MedioPagoCliente.objects.create(
                    cliente=cliente,
                    medio_pago=medio_pago_transferencia,
                    numero_cuenta=numero_cuenta,
                    nombre_titular_cuenta=form.cleaned_data['nombre_titular_cuenta'],
                    banco=form.cleaned_data.get('banco', ''),
                    tipo_cuenta=form.cleaned_data.get('tipo_cuenta', ''),
                    activo=True,
                    is_deleted=False
                )
                
                messages.success(request, 'Cuenta bancaria agregada exitosamente.')
            
            return get_cliente_detalle_redirect(request, cliente.pk)
    else:
        form = AgregarTarjetaForm(cliente=cliente)
    
    context = {
        'form': form,
        'cliente': cliente,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'clientes/cliente_agregar_cuenta.html', context)

def cliente_agregar_cuenta_bancaria(request, pk):
    """
    Vista para agregar una cuenta bancaria al cliente con acceso híbrido.

    Permite tanto a administradores como a usuarios operadores asociados
    agregar cuentas bancarias como medio de acreditación para un cliente específico.

    Args:
        request: Objeto HttpRequest con la información de la petición
        pk: Clave primaria del cliente al que agregar la cuenta bancaria

    Returns:
        HttpResponse: Formulario de cuenta bancaria o redirección tras creación

    Decorators:
        Ninguno específico, pero utiliza verificación de acceso manual

    Template:
        clientes/agregar_cuenta_bancaria.html

    Context:
        - form: Instancia del formulario CuentaBancariaForm
        - cliente: Instancia del cliente
        - titulo: Título para mostrar en el template
        - cancelar_url: URL para el botón de cancelar

    Access Control:
        - Administradores con permiso 'clientes.gestion': Acceso completo
        - Usuarios operadores asociados al cliente: Acceso específico

    Validation:
        - Verifica duplicados de cuentas bancarias para evitar registros repetidos
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Verificar acceso híbrido (admin o usuario asociado)
    if not verificar_acceso_cliente(request.user, cliente):
        messages.error(request, 'No tienes permisos para gestionar este cliente.')
        return redirect('inicio')
    
    if request.method == 'POST':
        form = CuentaBancariaForm(request.POST)
        if form.is_valid():
            cuenta_bancaria = form.save(commit=False)
            cuenta_bancaria.cliente = cliente
            
            # Verificar si ya existe una cuenta con los mismos datos
            cuenta_existente = CuentaBancaria.objects.filter(
                cliente=cliente,
                banco=cuenta_bancaria.banco,
                numero_cuenta=cuenta_bancaria.numero_cuenta,
                nombre_titular=cuenta_bancaria.nombre_titular
            ).first()
            
            if cuenta_existente:
                messages.warning(request, 'Ya existe una cuenta bancaria con estos datos para este cliente.')
            else:
                cuenta_bancaria.save()
                messages.success(request, 'Cuenta bancaria agregada exitosamente.')
            
            return get_cliente_detalle_redirect(request, cliente.pk)
    else:
        form = CuentaBancariaForm()
    
    context = {
        'form': form,
        'cliente': cliente,
        'titulo': 'Agregar Cuenta Bancaria',
        'cancelar_url': get_cliente_detalle_url(request, cliente.pk)
    }
    return render(request, 'clientes/agregar_cuenta_bancaria.html', context)

@login_required
def eliminar_tarjeta(request, pk, payment_method_id):
    """Vista para eliminar tarjeta de crédito de un cliente - Acceso híbrido"""
    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect('inicio')
    
    medio_pago_cliente = get_object_or_404(MedioPagoCliente, id=medio_id, cliente=cliente)
    
    # Cambiar el estado
    medio_pago_cliente.activo = not medio_pago_cliente.activo
    medio_pago_cliente.save()
    
    estado = 'activado' if medio_pago_cliente.activo else 'desactivado'
    messages.success(request, f'Medio de pago {estado} exitosamente.')
    
    return redirect('clientes:cliente_detalle', pk=pk)


@login_required
def cliente_eliminar_medio_acreditacion(request, pk, tipo, medio_id):
    """Vista para eliminar un medio de acreditación (cuenta bancaria o billetera) - Acceso híbrido"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Verificar acceso híbrido (admin o usuario asociado)
    if not verificar_acceso_cliente(request.user, cliente):
        messages.error(request, 'No tienes permisos para gestionar este cliente.')
        return redirect('inicio')
    
    if request.method == 'POST':
        if tipo == 'cuenta':
            medio = get_object_or_404(CuentaBancaria, id=medio_id, cliente=cliente)
            descripcion = f'Cuenta {medio.banco} - {medio.numero_cuenta}'
        elif tipo == 'billetera':
            medio = get_object_or_404(Billetera, id=medio_id, cliente=cliente)
            descripcion = f'Billetera {medio.get_tipo_billetera_display()} - {medio.telefono}'
        else:
            messages.error(request, 'Tipo de medio de acreditación no válido.')
            return get_cliente_detalle_redirect(request, cliente.pk)
        
        medio.delete()
        messages.success(request, f'{descripcion} eliminado exitosamente.')
        
        return get_cliente_detalle_redirect(request, cliente.pk)
    
    # Solo aceptar POST
    messages.error(request, 'Acción no permitida.')
    return get_cliente_detalle_redirect(request, cliente.pk)

def cliente_agregar_billetera(request, pk):
    """Vista para agregar una billetera electrónica al cliente - Acceso híbrido"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Verificar acceso híbrido (admin o usuario asociado)
    if not verificar_acceso_cliente(request.user, cliente):
        messages.error(request, 'No tienes permisos para gestionar este cliente.')
        return redirect('inicio')
    
    if request.method == 'POST':
        form = BilleteraForm(request.POST)
        if form.is_valid():
            billetera = form.save(commit=False)
            billetera.cliente = cliente
            
            # Verificar si ya existe una billetera con los mismos datos
            billetera_existente = Billetera.objects.filter(
                cliente=cliente,
                tipo_billetera=billetera.tipo_billetera,
                telefono=billetera.telefono,
                nombre_titular=billetera.nombre_titular,
                nro_documento=billetera.nro_documento
            ).first()
            
            if billetera_existente:
                messages.warning(request, 'Ya existe una billetera con estos datos para este cliente.')
            else:
                billetera.save()
                messages.success(request, 'Billetera agregada exitosamente.')
            
            return get_cliente_detalle_redirect(request, cliente.pk)
    else:
        form = BilleteraForm()
    
    context = {
        'form': form,
        'cliente': cliente,
        'titulo': 'Agregar Billetera Electrónica',
        'cancelar_url': get_cliente_detalle_url(request, cliente.pk)
    }
    return render(request, 'clientes/agregar_billetera.html', context)

@login_required
@permission_required('transacciones.visualizacion', raise_exception=True)
def historial_transacciones(request, cliente_id):
    """
    Vista para el historial de transacciones de un cliente específico.
    
    Muestra un listado de transacciones con capacidades de filtrado
    específico para un cliente determinado, incluyendo filtros por
    usuario, tipo de operación y estado.
    
    Filtros disponibles:
        - Tipo de operación (compra/venta)
        - Estado de transacción (pendiente/completada/etc.)
        - Usuario específico que procesó la transacción
    
    Args:
        request (HttpRequest): Petición HTTP con parámetros de filtro
        cliente_id (int): ID específico del cliente
        
    Returns:
        HttpResponse: Listado de transacciones del cliente
        
    Template:
        clientes/cliente_historial_transacciones.html
        
    Context:
        - transacciones: QuerySet de transacciones filtradas del cliente
        - cliente: Instancia del cliente
        - tipo_operacion: Filtro de tipo aplicado
        - estado_filtro: Filtro de estado aplicado
        - usuario_filtro: Usuario específico si aplica
        - usuarios_cliente: Usuarios asociados al cliente
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        messages.error(request, "Cliente no encontrado")
        return redirect('clientes:cliente_lista')
    
    # Verificar acceso híbrido (admin o usuario asociado)
    if not verificar_acceso_cliente(request.user, cliente):
        messages.error(request, 'No tienes permisos para ver el historial de este cliente.')
        return redirect('inicio')
    
    transacciones_pasadas = Transaccion.objects.filter(cliente=cliente, estado='Pendiente')
    if transacciones_pasadas:
        for t in transacciones_pasadas:
            if t.fecha_hora < timezone.now() - timedelta(minutes=5):
                t.estado = 'Cancelada'
                t.razon = 'Expira el tiempo para confirmar la transacción'
                t.token = None
                t.save()
    
    # Obtener parámetros de filtrado
    tipo_operacion = request.GET.get('tipo_operacion', '')
    estado_filtro = request.GET.get('estado', '')
    usuario_filtro = request.GET.get('usuario', '')
    
    # Obtener todas las transacciones del cliente
    transacciones = Transaccion.objects.filter(cliente=cliente).order_by('-fecha_hora')
    
    # Obtener usuarios asociados al cliente
    usuarios_cliente = cliente.usuarios.all()
    
    # Aplicar filtros según parámetros recibidos
    if tipo_operacion:
        transacciones = transacciones.filter(tipo=tipo_operacion)
    
    if estado_filtro:
        transacciones = transacciones.filter(estado__iexact=estado_filtro)
    
    # Filtrar por usuario si se especifica
    if usuario_filtro:
        try:
            usuario_id = int(usuario_filtro)
            transacciones = transacciones.filter(usuario_id=usuario_id)
        except (ValueError, TypeError):
            pass
    
    context = {
        'transacciones': transacciones,
        'cliente': cliente,
        'tipo_operacion': tipo_operacion,
        'estado_filtro': estado_filtro,
        'usuario_filtro': usuario_filtro,
        'usuarios_cliente': usuarios_cliente
    }
    
    return render(request, 'clientes/cliente_historial_transacciones.html', context)

@login_required
def cliente_detalle_transaccion(request, cliente_id, transaccion_id):
    """
    Vista de detalle para una transacción específica desde el contexto de cliente.
    
    Muestra información completa y detallada de una transacción individual
    del cliente, incluyendo todos los datos relevantes como montos calculados,
    medios de pago/cobro, información del cliente y estado actual.
    
    Args:
        request (HttpRequest): Petición HTTP
        cliente_id (int): ID del cliente
        transaccion_id (int): ID de la transacción a mostrar
        
    Returns:
        HttpResponse: Página de detalle o redirección si no existe
        
    Template:
        clientes/cliente_detalle_transaccion.html
        
    Context:
        - transaccion: Instancia de la transacción
        - cliente: Instancia del cliente
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        messages.error(request, "Cliente no encontrado")
        return redirect('clientes:cliente_lista')
    
    # Verificar acceso híbrido (admin o usuario asociado)
    if not verificar_acceso_cliente(request.user, cliente):
        messages.error(request, 'No tienes permisos para ver las transacciones de este cliente.')
        return redirect('inicio')
    
    try:
        transaccion = Transaccion.objects.get(id=transaccion_id, cliente=cliente)
    except Transaccion.DoesNotExist:
        messages.error(request, 'La transacción solicitada no existe para este cliente.')
        return redirect('clientes:cliente_historial', cliente_id=cliente_id)

    if transaccion.fecha_hora < timezone.now() - timedelta(minutes=5):
        transaccion.estado = 'Cancelada'
        transaccion.razon = 'Expira el tiempo para confirmar la transacción'
        transaccion.token = None
        transaccion.save()
    
    context = {
        'transaccion': transaccion,
        'cliente': cliente,
    }
    
    return render(request, 'clientes/cliente_detalle_transaccion.html', context)