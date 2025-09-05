from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.db.models import Q
from .models import MedioPago

@login_required
@permission_required('medios_pago.gestion', raise_exception=True)
def medio_pago_lista(request):
    """Vista para listar medios de pago con filtros de búsqueda"""
    # Obtener todos los medios de pago para verificar si hay alguno
    todos_los_medios = MedioPago.objects.all()
    
    # Obtener medios de pago para mostrar (con filtros aplicados)
    medios_pago = todos_los_medios
    

    # Ordenar por nombre
    medios_pago = medios_pago.order_by('tipo')
    
    context = {
        'medios_pago': medios_pago,
        'hay_medios': todos_los_medios.exists(),
    }
    return render(request, 'medios_pago/medio_pago_lista.html', context)



@login_required
@permission_required('medios_pago.gestion', raise_exception=True)
def medio_pago_detalle(request, pk):
    """Vista para mostrar detalles de un medio de pago"""
    medio_pago = get_object_or_404(MedioPago, pk=pk)
    return render(request, 'medios_pago/medio_pago_detalle.html', {
        'medio_pago': medio_pago
    })



@login_required
@permission_required('medios_pago.activacion', raise_exception=True)
def medio_pago_cambiar_estado(request, pk):
    """Vista para activar/desactivar un medio de pago"""
    if request.method != 'POST':
        raise Http404()
    
    medio_pago = get_object_or_404(MedioPago, pk=pk)
    
    # Cambiar el estado
    medio_pago.activo = not medio_pago.activo
    medio_pago.save()
    
    estado = 'activado' if medio_pago.activo else 'desactivado'
    messages.success(request, f'Medio de pago {estado} exitosamente.')
    
    return redirect('medios_pago:medio_pago_detalle', pk=medio_pago.pk)


@login_required
def obtener_campos_por_tipo(request):
    """Vista AJAX para obtener campos específicos según el tipo de medio de pago"""
    tipo = request.GET.get('tipo')
    
    campos_visibles = {
        'transferencia': ['moneda_transferencia'],
        'billetera_electronica': ['tipo_billetera', 'numero_billetera'],
        'tarjeta_credito': ['cuenta_destino', 'numero_cuenta'],
        'cheque': ['solo_compra_extranjera', 'moneda_cheque'],
        'efectivo': []
    }
    
    return JsonResponse({
        'campos': campos_visibles.get(tipo, [])
    })
