from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q
from .models import Cliente
from .forms import ClienteForm
from medios_acreditacion.models import CuentaBancaria, Billetera
from medios_acreditacion.forms import CuentaBancariaForm, BilleteraForm

def verificar_acceso_cliente(user, cliente):
    """
    Verifica si el usuario tiene acceso al cliente mediante:
    1. Permisos de administración (clientes.gestion)
    2. Asociación directa como usuario operador
    """
    return (user.has_perm('clientes.gestion') or 
            cliente in user.clientes_operados.all())

def get_cliente_detalle_redirect(request, cliente_pk):
    """
    Determina la URL correcta para redirigir según el tipo de usuario
    """
    referer = request.META.get('HTTP_REFERER', '')
    if 'usuarios/cliente' in referer or not request.user.has_perm('clientes.gestion'):
        return redirect('usuarios:detalle_cliente', cliente_id=cliente_pk)
    else:
        return redirect('clientes:cliente_detalle', pk=cliente_pk)

def get_cliente_detalle_url(request, cliente_pk):
    """
    Determina la URL correcta de detalle del cliente según el tipo de usuario (para templates)
    """
    referer = request.META.get('HTTP_REFERER', '')
    if 'usuarios/cliente' in referer or not request.user.has_perm('clientes.gestion'):
        return f'/usuarios/cliente/{cliente_pk}/'
    else:
        return f'/clientes/{cliente_pk}/'

def procesar_medios_acreditacion_cliente(cliente, usuario):
    """
    Función auxiliar para procesar los medios de acreditación de un cliente
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
            Q(docCliente__icontains=busqueda)
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
    """Vista de detalle del cliente - Acceso híbrido"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Verificar acceso híbrido (admin o usuario asociado)
    if not verificar_acceso_cliente(request.user, cliente):
        messages.error(request, 'No tienes permisos para ver este cliente.')
        return redirect('inicio')
    
    # Usar función auxiliar para procesar medios de acreditación
    medios_data = procesar_medios_acreditacion_cliente(cliente, request.user)
    
    context = {
        'cliente': cliente,
        **medios_data
    }
    return render(request, 'clientes/cliente_detalle.html', context)

@login_required
@permission_required('clientes.gestion', raise_exception=True)
def cliente_editar(request, pk):
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
def cliente_agregar_cuenta_bancaria(request, pk):
    """Vista para agregar una cuenta bancaria al cliente - Acceso híbrido"""
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
                numero_billetera=billetera.numero_billetera,
                nombre_titular=billetera.nombre_titular,
                ci=billetera.ci
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
            descripcion = f'Billetera {medio.get_tipo_billetera_display()} - {medio.numero_billetera}'
        else:
            messages.error(request, 'Tipo de medio de acreditación no válido.')
            return get_cliente_detalle_redirect(request, cliente.pk)
        
        medio.delete()
        messages.success(request, f'{descripcion} eliminado exitosamente.')
        
        return get_cliente_detalle_redirect(request, cliente.pk)
    
    # Solo aceptar POST
    messages.error(request, 'Acción no permitida.')
    return get_cliente_detalle_redirect(request, cliente.pk)


