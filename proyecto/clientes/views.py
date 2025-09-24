from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.conf import settings
from .models import Cliente
from .forms import ClienteForm, AgregarTarjetaForm
import stripe
import logging

# Configurar Stripe y logging
stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

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
    
    tarjetas_stripe = cliente.obtener_tarjetas_stripe()
    # Verificar acceso híbrido (admin o usuario asociado)
    if not verificar_acceso_cliente(request.user, cliente):
        messages.error(request, 'No tienes permisos para ver este cliente.')
        return redirect('inicio')
    
    context = {
        'cliente': cliente,
        'tarjetas_stripe': tarjetas_stripe,
        'total_tarjetas': len(tarjetas_stripe)
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
def agregar_tarjeta(request, pk):
    """Vista para agregar tarjeta de crédito a un cliente - Acceso híbrido"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Verificar acceso híbrido (admin o usuario asociado)
    if not verificar_acceso_cliente(request.user, cliente):
        messages.error(request, 'No tienes permisos para gestionar las tarjetas de este cliente.')
        return redirect('inicio')
    
    if request.method == 'POST':
        form = AgregarTarjetaForm(request.POST, cliente=cliente)
        if form.is_valid():
            try:
                payment_method = form.save()
                messages.success(request, 'Tarjeta agregada exitosamente.')
                
                # Determinar la URL de redirección según el tipo de usuario
                return get_cliente_detalle_redirect(request, pk)
                
            except Exception as e:
                messages.error(request, f'Error al agregar la tarjeta: {str(e)}')
    else:
        form = AgregarTarjetaForm(cliente=cliente)
    
    context = {
        'form': form,
        'cliente': cliente,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'clientes/agregar_tarjeta.html', context)


@login_required
def eliminar_tarjeta(request, pk, payment_method_id):
    """Vista para eliminar tarjeta de crédito de un cliente - Acceso híbrido"""
    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect('inicio')
    
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Verificar acceso híbrido (admin o usuario asociado)
    if not verificar_acceso_cliente(request.user, cliente):
        messages.error(request, 'No tienes permisos para gestionar las tarjetas de este cliente.')
        return redirect('inicio')
    
    try:
        # Desadjuntar el método de pago del cliente
        stripe.PaymentMethod.detach(payment_method_id)
        messages.success(request, 'Tarjeta eliminada exitosamente.')
        
    except stripe.error.InvalidRequestError:
        messages.error(request, 'La tarjeta no existe o ya fue eliminada.')
    except stripe.error.StripeError as e:
        messages.error(request, f'Error al eliminar la tarjeta: {str(e)}')
    except Exception as e:
        logger.error(f"Error inesperado al eliminar tarjeta: {str(e)}")
        messages.error(request, 'Error inesperado al eliminar la tarjeta.')
    
    # Determinar la URL de redirección según el tipo de usuario
    return get_cliente_detalle_redirect(request, pk)