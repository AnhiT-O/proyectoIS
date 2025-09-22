from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.conf import settings
from .models import Cliente
from .forms import ClienteForm
from medios_pago.models import MedioPago, MedioPagoCliente
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
    
    # Obtener medios de pago según el rol del usuario (usando el modelo intermedio)
    if es_administrador:
        # Administradores ven todos los medios (activos e inactivos)
        medios_pago_cliente = MedioPagoCliente.objects.filter(
            cliente=cliente
        ).select_related('medio_pago').order_by('medio_pago__tipo')
    else:
        # Operadores solo ven medios activos
        medios_pago_cliente = MedioPagoCliente.objects.filter(
            cliente=cliente, 
            activo=True, 
            is_deleted=False
        ).select_related('medio_pago').order_by('medio_pago__tipo')
    
    # Aplicar ocultación de datos sensibles para operadores
    if not es_administrador:
        for medio_cliente in medios_pago_cliente:
            if medio_cliente.medio_pago.tipo == 'tarjeta_credito':
                # Ocultar datos sensibles de tarjeta
                if medio_cliente.stripe_payment_method_id:
                    # Para tarjetas de Stripe, obtener info desde Stripe
                    try:
                        import stripe
                        stripe.api_key = settings.STRIPE_SECRET_KEY
                        payment_method = stripe.PaymentMethod.retrieve(medio_cliente.stripe_payment_method_id)
                        card = payment_method.card
                        medio_cliente.numero_tarjeta_oculto = f'**** **** **** {card.last4}'
                        medio_cliente.marca_tarjeta = card.brand.upper()
                    except:
                        medio_cliente.numero_tarjeta_oculto = '****'
                        medio_cliente.marca_tarjeta = 'STRIPE'
                else:
                    medio_cliente.numero_tarjeta_oculto = '****'
                medio_cliente.cvv_tarjeta_oculto = '***'
            elif medio_cliente.medio_pago.tipo == 'transferencia':
                # Ocultar datos sensibles de cuenta bancaria
                if medio_cliente.numero_cuenta:
                    medio_cliente.numero_cuenta_oculto = '****' + medio_cliente.numero_cuenta[-4:] if len(medio_cliente.numero_cuenta) > 4 else '****'
                else:
                    medio_cliente.numero_cuenta_oculto = '****'
    else:
        # Administradores ven datos completos (pero no datos sensibles de Stripe)
        for medio_cliente in medios_pago_cliente:
            if medio_cliente.medio_pago.tipo == 'tarjeta_credito':
                if medio_cliente.stripe_payment_method_id:
                    # Para tarjetas de Stripe, mostrar info disponible
                    try:
                        import stripe
                        stripe.api_key = settings.STRIPE_SECRET_KEY
                        payment_method = stripe.PaymentMethod.retrieve(medio_cliente.stripe_payment_method_id)
                        card = payment_method.card
                        medio_cliente.numero_tarjeta_oculto = f'**** **** **** {card.last4}'
                        medio_cliente.marca_tarjeta = card.brand.upper()
                    except:
                        medio_cliente.numero_tarjeta_oculto = '****'
                        medio_cliente.marca_tarjeta = 'STRIPE'
                else:
                    medio_cliente.numero_tarjeta_oculto = '****'
                medio_cliente.cvv_tarjeta_oculto = '***'  # Nunca mostrar CVV
            elif medio_cliente.medio_pago.tipo == 'transferencia':
                medio_cliente.numero_cuenta_oculto = medio_cliente.numero_cuenta
    
    # Separar por tipo para mostrar en la interfaz
    medios_por_tipo = {}
    for medio_cliente in medios_pago_cliente:
        tipo = medio_cliente.medio_pago.tipo
        if tipo not in medios_por_tipo:
            medios_por_tipo[tipo] = []
        medios_por_tipo[tipo].append(medio_cliente)
    
    # Verificar si hay medios configurados por tipo
    tiene_tarjetas_configuradas = any(
        medio_cliente.tarjeta_credito_completa 
        for medio_cliente in medios_por_tipo.get('tarjeta_credito', [])
    )
    
    tiene_cuentas_configuradas = any(
        medio_cliente.cuenta_bancaria_completa 
        for medio_cliente in medios_por_tipo.get('transferencia', [])
    )
    
    # Verificar si se pueden agregar más tarjetas (máximo 3)
    tarjetas_configuradas = sum(
        1 for medio_cliente in medios_por_tipo.get('tarjeta_credito', [])
        if medio_cliente.tarjeta_credito_completa
    )
    puede_agregar_tarjeta = tarjetas_configuradas < 3
    
    return {
        'medios_pago': medios_pago_cliente,  # Ahora son objetos MedioPagoCliente
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
    """Vista para agregar una tarjeta de crédito usando Stripe - Acceso híbrido"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Verificar acceso híbrido (admin o usuario asociado)
    if not verificar_acceso_cliente(request.user, cliente):
        messages.error(request, 'No tienes permisos para gestionar este cliente.')
        return redirect('inicio')
    
    # Verificar límite de tarjetas configuradas activas (máximo 3)
    tarjetas_configuradas = MedioPagoCliente.objects.filter(
        cliente=cliente,
        medio_pago__tipo='tarjeta_credito',
        stripe_payment_method_id__isnull=False,  # Solo contar las de Stripe
        activo=True,
        is_deleted=False
    ).count()
    
    if tarjetas_configuradas >= 3:
        messages.error(request, f'El cliente {cliente.nombre} ya tiene el máximo de 3 tarjetas de crédito configuradas.')
        return get_cliente_detalle_redirect(request, cliente.pk)
    
    # Esta vista solo renderiza el template con Stripe Elements
    # El procesamiento se hace via AJAX con las vistas de medios_pago
    context = {
        'cliente': cliente,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
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
    
    medio_pago_cliente = get_object_or_404(MedioPagoCliente, id=medio_id, cliente=cliente)
    
    # Cambiar el estado
    medio_pago_cliente.activo = not medio_pago_cliente.activo
    medio_pago_cliente.save()
    
    estado = 'activado' if medio_pago_cliente.activo else 'desactivado'
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
    
    medio_pago_cliente = get_object_or_404(MedioPagoCliente, id=medio_id, cliente=cliente)
    
    # No permitir eliminar medios de pago básicos sin configuración específica
    if medio_pago_cliente.medio_pago.tipo == 'efectivo':
        # Efectivo es básico, no se puede eliminar
        messages.error(request, f'No se puede eliminar el medio de pago Efectivo básico.')
        return redirect('clientes:cliente_detalle', pk=pk)
    elif medio_pago_cliente.medio_pago.tipo == 'cheque':
        # Cheque básico sin configuración específica no se puede eliminar
        messages.error(request, f'No se puede eliminar el medio de pago Cheque básico.')
        return redirect('clientes:cliente_detalle', pk=pk)
    elif medio_pago_cliente.medio_pago.tipo == 'billetera_electronica':
        # Billetera electrónica básica no se puede eliminar
        messages.error(request, f'No se puede eliminar el medio de pago Billetera Electrónica básico.')
        return redirect('clientes:cliente_detalle', pk=pk)
    
    # Permitir eliminar transferencias solo si están configuradas
    if medio_pago_cliente.medio_pago.tipo == 'transferencia' and not medio_pago_cliente.numero_cuenta:
        messages.error(request, f'No se puede eliminar la transferencia básica sin configurar.')
        return redirect('clientes:cliente_detalle', pk=pk)
    
    if request.method == 'POST':
        descripcion_completa = medio_pago_cliente.get_descripcion_completa()
        
        # Solo desactivar el medio de pago, no marcarlo como eliminado
        # Esto permite que aparezca en el panel de administración como inactivo
        medio_pago_cliente.activo = False
        medio_pago_cliente.save()
        
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