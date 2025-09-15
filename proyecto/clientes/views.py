from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from .models import Cliente
from .forms import ClienteForm
from medios_pago.models import MedioPago
from medios_pago.forms import TarjetaCreditoForm, CuentaBancariaForm

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

def procesar_medios_pago_cliente(cliente, usuario):
    """
    Función auxiliar para procesar los medios de pago de un cliente
    con la lógica de ocultación de datos sensibles según el tipo de usuario
    """
    # Determinar si es administrador
    es_administrador = usuario.has_perm('clientes.gestion')
    
    # Obtener medios de pago según el rol del usuario
    if es_administrador:
        # Administradores ven todos los medios (activos e inactivos)
        medios_pago = cliente.medios_pago.all().order_by('tipo')
    else:
        # Operadores solo ven medios activos
        medios_pago = cliente.medios_pago.filter(activo=True).order_by('tipo')
    
    # Aplicar ocultación de datos sensibles para operadores
    if not es_administrador:
        for medio in medios_pago:
            if medio.tipo == 'tarjeta_credito':
                # Ocultar datos sensibles de tarjeta
                if medio.numero_tarjeta:
                    medio.numero_tarjeta_oculto = '**** **** **** ' + medio.numero_tarjeta[-4:]
                else:
                    medio.numero_tarjeta_oculto = '****'
                medio.cvv_tarjeta_oculto = '***'
            elif medio.tipo == 'transferencia':
                # Ocultar datos sensibles de cuenta bancaria
                if medio.numero_cuenta:
                    medio.numero_cuenta_oculto = '****' + medio.numero_cuenta[-4:] if len(medio.numero_cuenta) > 4 else '****'
                else:
                    medio.numero_cuenta_oculto = '****'
    else:
        # Administradores ven datos completos
        for medio in medios_pago:
            if medio.tipo == 'tarjeta_credito':
                medio.numero_tarjeta_oculto = medio.numero_tarjeta
                medio.cvv_tarjeta_oculto = medio.cvv_tarjeta
            elif medio.tipo == 'transferencia':
                medio.numero_cuenta_oculto = medio.numero_cuenta
    
    # Separar por tipo para mostrar en la interfaz
    medios_por_tipo = {}
    for medio in medios_pago:
        if medio.tipo not in medios_por_tipo:
            medios_por_tipo[medio.tipo] = []
        medios_por_tipo[medio.tipo].append(medio)
    
    # Verificar si hay medios configurados por tipo
    tiene_tarjetas_configuradas = any(
        medio.tarjeta_credito_completa 
        for medio in medios_por_tipo.get('tarjeta_credito', [])
    )
    
    tiene_cuentas_configuradas = any(
        medio.cuenta_bancaria_completa 
        for medio in medios_por_tipo.get('transferencia', [])
    )
    
    # Verificar si se pueden agregar más tarjetas (máximo 3)
    tarjetas_configuradas = sum(
        1 for medio in medios_por_tipo.get('tarjeta_credito', [])
        if medio.tarjeta_credito_completa
    )
    puede_agregar_tarjeta = tarjetas_configuradas < 3
    
    return {
        'medios_pago': medios_pago,
        'medios_por_tipo': medios_por_tipo,
        'tiene_tarjetas_configuradas': tiene_tarjetas_configuradas,
        'tiene_cuentas_configuradas': tiene_cuentas_configuradas,
        'puede_agregar_tarjeta': puede_agregar_tarjeta,
        'es_administrador': es_administrador,
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
    
    # Usar función auxiliar para procesar medios de pago
    medios_data = procesar_medios_pago_cliente(cliente, request.user)
    
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
def cliente_agregar_tarjeta(request, pk):
    """Vista para agregar una tarjeta de crédito al cliente - Acceso híbrido"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Verificar acceso híbrido (admin o usuario asociado)
    if not verificar_acceso_cliente(request.user, cliente):
        messages.error(request, 'No tienes permisos para gestionar este cliente.')
        return redirect('inicio')
    
    # Verificar límite de tarjetas configuradas activas (máximo 3)
    tarjetas_configuradas = MedioPago.objects.filter(
        tipo='tarjeta_credito',
        clientes=cliente,
        numero_tarjeta__isnull=False,
        activo=True
    ).count()
    
    if tarjetas_configuradas >= 3:
        messages.error(request, f'El cliente {cliente.nombre} ya tiene el máximo de 3 tarjetas de crédito configuradas.')
        return get_cliente_detalle_redirect(request, cliente.pk)
    
    if request.method == 'POST':
        form = TarjetaCreditoForm(request.POST)
        if form.is_valid():
            numero_tarjeta = form.cleaned_data['numero_tarjeta']
            
            # Buscar si existe una tarjeta con EXACTAMENTE los mismos datos
            tarjeta_existente = MedioPago.objects.filter(
                tipo='tarjeta_credito',
                numero_tarjeta=numero_tarjeta,
                cvv_tarjeta=form.cleaned_data['cvv'],
                nombre_titular_tarjeta=form.cleaned_data['nombre_titular_tarjeta'],
                fecha_vencimiento_tc=form.cleaned_data['fecha_vencimiento_tc'],
                descripcion_tarjeta=form.cleaned_data['descripcion_tarjeta'],
                moneda_tc=form.cleaned_data['moneda_tc'],
                clientes=cliente
            ).first()
            
            if tarjeta_existente:
                # Si existe con exactamente los mismos datos pero está inactiva, reactivarla
                if not tarjeta_existente.activo:
                    tarjeta_existente.activo = True
                    tarjeta_existente.is_deleted = False  # Restaurar si estaba eliminada
                    tarjeta_existente.save()
                    
                    messages.success(request, f'Tarjeta de crédito "{tarjeta_existente.descripcion_tarjeta}" agregada exitosamente.')
                else:
                    messages.warning(request, 'Esta tarjeta ya está activa y asociada al cliente.')
            else:
                # Verificar si existe una tarjeta con el mismo número pero datos diferentes
                tarjeta_mismo_numero = MedioPago.objects.filter(
                    tipo='tarjeta_credito',
                    numero_tarjeta=numero_tarjeta,
                    clientes=cliente
                ).first()
                
                if tarjeta_mismo_numero:
                    messages.error(request, 'Ya existe una tarjeta con este número pero con datos diferentes. Si desea cambiar los datos, primero debe eliminar la tarjeta anterior.')
                    return render(request, 'clientes/cliente_agregar_tarjeta.html', {
                        'form': form,
                        'cliente': cliente,
                        'titulo': 'Agregar Tarjeta de Crédito',
                        'cancelar_url': get_cliente_detalle_url(request, cliente.pk)
                    })
                
                # Crear un nuevo medio de pago tipo tarjeta de crédito
                tarjeta = MedioPago.objects.create(
                    tipo='tarjeta_credito',
                    numero_tarjeta=numero_tarjeta,
                    cvv_tarjeta=form.cleaned_data['cvv'],
                    nombre_titular_tarjeta=form.cleaned_data['nombre_titular_tarjeta'],
                    fecha_vencimiento_tc=form.cleaned_data['fecha_vencimiento_tc'],
                    descripcion_tarjeta=form.cleaned_data['descripcion_tarjeta'],
                    moneda_tc=form.cleaned_data['moneda_tc']
                )
                
                # Asociar la tarjeta al cliente
                cliente.medios_pago.add(tarjeta)
                
                messages.success(request, f'Tarjeta de crédito "{tarjeta.descripcion_tarjeta}" agregada exitosamente.')
            
            return get_cliente_detalle_redirect(request, cliente.pk)
    else:
        form = TarjetaCreditoForm()
    
    context = {
        'form': form,
        'cliente': cliente,
        'titulo': 'Agregar Tarjeta de Crédito',
        'cancelar_url': get_cliente_detalle_url(request, cliente.pk)
    }
    return render(request, 'clientes/cliente_agregar_tarjeta.html', context)


@login_required
def cliente_agregar_cuenta(request, pk):
    """Vista para agregar una cuenta bancaria al cliente - Acceso híbrido"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Verificar acceso híbrido (admin o usuario asociado)
    if not verificar_acceso_cliente(request.user, cliente):
        messages.error(request, 'No tienes permisos para gestionar este cliente.')
        return redirect('inicio')
    
    if request.method == 'POST':
        form = CuentaBancariaForm(request.POST)
        if form.is_valid():
            numero_cuenta = form.cleaned_data['numero_cuenta']
            
            # Buscar si existe una cuenta con EXACTAMENTE los mismos datos
            cuenta_existente = MedioPago.objects.filter(
                tipo='transferencia',
                numero_cuenta=numero_cuenta,
                nombre_titular_cuenta=form.cleaned_data['nombre_titular_cuenta'],
                banco=form.cleaned_data.get('banco', ''),
                tipo_cuenta=form.cleaned_data.get('tipo_cuenta', ''),
                cedula_ruc_cuenta=form.cleaned_data.get('cedula_ruc_cuenta', ''),
                clientes=cliente
            ).first()
            
            if cuenta_existente:
                # Si existe con exactamente los mismos datos pero está inactiva, reactivarla
                if not cuenta_existente.activo:
                    cuenta_existente.activo = True
                    cuenta_existente.is_deleted = False  # Restaurar si estaba eliminada
                    cuenta_existente.save()
                    
                    messages.success(request, 'Cuenta bancaria agregada exitosamente.')
                else:
                    messages.warning(request, 'Esta cuenta bancaria ya está activa y asociada al cliente.')
            else:
                # Verificar si existe una cuenta con el mismo número pero datos diferentes
                cuenta_mismo_numero = MedioPago.objects.filter(
                    tipo='transferencia',
                    numero_cuenta=numero_cuenta,
                    clientes=cliente
                ).first()
                
                if cuenta_mismo_numero:
                    messages.error(request, 'Ya existe una cuenta con este número pero con datos diferentes. Si desea cambiar los datos, primero debe eliminar la cuenta anterior.')
                    return render(request, 'clientes/cliente_agregar_cuenta.html', {
                        'form': form,
                        'cliente': cliente,
                        'titulo': 'Agregar Cuenta Bancaria',
                        'cancelar_url': get_cliente_detalle_url(request, cliente.pk)
                    })
                
                # Buscar el medio de pago transferencia básico del cliente
                transferencia_basica = cliente.medios_pago.filter(
                    tipo='transferencia',
                    numero_cuenta__isnull=True
                ).first()
                
                if transferencia_basica:
                    # Crear una nueva transferencia con datos específicos
                    transferencia = MedioPago.objects.create(
                        tipo='transferencia',
                        numero_cuenta=numero_cuenta,
                        nombre_titular_cuenta=form.cleaned_data['nombre_titular_cuenta'],
                        banco=form.cleaned_data.get('banco', ''),
                        tipo_cuenta=form.cleaned_data.get('tipo_cuenta', ''),
                        cedula_ruc_cuenta=form.cleaned_data.get('cedula_ruc_cuenta', '')
                    )
                    
                    # Asociar la cuenta al cliente
                    cliente.medios_pago.add(transferencia)
                
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
    return render(request, 'clientes/cliente_agregar_cuenta.html', context)


@login_required
def cliente_cambiar_estado_medio_pago(request, pk, medio_id):
    """Vista para activar/desactivar un medio de pago específico del cliente - Acceso híbrido"""
    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect('clientes:cliente_detalle', pk=pk)
    
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Verificar acceso híbrido (admin o usuario asociado)
    if not verificar_acceso_cliente(request.user, cliente):
        messages.error(request, 'No tienes permisos para gestionar este cliente.')
        return redirect('inicio')
    
    medio_pago = get_object_or_404(MedioPago, id=medio_id)
    
    # Verificar que el medio de pago pertenece al cliente
    if not cliente.medios_pago.filter(id=medio_id).exists():
        messages.error(request, 'El medio de pago no está asociado a este cliente.')
        return redirect('clientes:cliente_detalle', pk=pk)
    
    # Cambiar el estado
    medio_pago.activo = not medio_pago.activo
    medio_pago.save()
    
    estado = 'activado' if medio_pago.activo else 'desactivado'
    messages.success(request, f'Medio de pago {estado} exitosamente.')
    
    return redirect('clientes:cliente_detalle', pk=pk)


@login_required
def cliente_eliminar_medio_pago(request, pk, medio_id):
    """Vista para desactivar un medio de pago del cliente - Solo POST con modal"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Verificar acceso híbrido (admin o usuario asociado)
    if not verificar_acceso_cliente(request.user, cliente):
        messages.error(request, 'No tienes permisos para gestionar este cliente.')
        return redirect('inicio')
    
    medio_pago = get_object_or_404(MedioPago, id=medio_id)
    
    # Verificar que el medio de pago pertenece al cliente
    if not cliente.medios_pago.filter(id=medio_id).exists():
        messages.error(request, 'No tienes permisos para eliminar este medio de pago.')
        return redirect('clientes:cliente_detalle', pk=pk)
    
    # No permitir eliminar medios de pago básicos (efectivo, cheque sin configurar)
    medios_basicos = ['efectivo', 'cheque']
    if medio_pago.tipo in medios_basicos and not any([
        medio_pago.numero_tarjeta, medio_pago.numero_cuenta, medio_pago.numero_billetera
    ]):
        messages.error(request, f'No se puede eliminar el medio de pago {medio_pago.get_tipo_display()} básico.')
        return redirect('clientes:cliente_detalle', pk=pk)
    
    # Permitir eliminar transferencias solo si están configuradas
    if medio_pago.tipo == 'transferencia' and not medio_pago.numero_cuenta:
        messages.error(request, f'No se puede eliminar la transferencia básica sin configurar.')
        return redirect('clientes:cliente_detalle', pk=pk)
    
    if request.method == 'POST':
        descripcion_completa = medio_pago.get_descripcion_completa()
        
        # Solo desactivar el medio de pago, no marcarlo como eliminado
        # Esto permite que aparezca en el panel de administración como inactivo
        medio_pago.activo = False
        medio_pago.save()
        
        # Si es una petición AJAX, devolver JSON para mostrar modal de éxito
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Determinar la URL de redirección basada en el referer
            referer = request.META.get('HTTP_REFERER', '')
            if 'usuarios/cliente' in referer:
                redirect_url = reverse('usuarios:detalle_cliente', kwargs={'cliente_id': pk})
            else:
                redirect_url = reverse('clientes:cliente_detalle', kwargs={'pk': pk})
                
            return JsonResponse({
                'success': True,
                'message': f'{descripcion_completa} eliminado exitosamente.',
                'descripcion': descripcion_completa,
                'redirect_url': redirect_url
            })
        
        messages.success(request, f'{descripcion_completa} eliminado exitosamente.')
        return redirect('clientes:cliente_detalle', pk=pk)
    
    # Solo aceptar POST - ya no necesitamos página de confirmación con modal
    messages.error(request, 'Acción no permitida.')
    return redirect('clientes:cliente_detalle', pk=pk)