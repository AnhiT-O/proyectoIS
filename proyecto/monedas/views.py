from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.db.models import Q
from .models import Moneda
from .forms import MonedaForm

@login_required
@permission_required('monedas.crear', raise_exception=True)
def moneda_crear(request):
    if request.method == 'POST':
        form = MonedaForm(request.POST)
        if form.is_valid():
            moneda = form.save()
            messages.success(request, f'Moneda "{moneda.nombre}" creada exitosamente.')
            return redirect('monedas:lista_monedas')
    else:
        form = MonedaForm()
    return render(request, 'monedas/moneda_form.html', {'form': form, 'accion': 'Crear'})

@login_required
@permission_required('monedas.editar', raise_exception=True)
def moneda_lista(request):
    # Manejar cambio de estado si se envía POST
    if request.method == 'POST' and 'cambiar_estado' in request.POST:
        # Verificar permisos de activación
        if not request.user.has_perm('monedas.activacion'):
            messages.error(request, 'No tienes permisos para activar/desactivar monedas.')
            return redirect('monedas:lista_monedas')
        
        try:
            moneda_id = request.POST.get('moneda_id')
            moneda = get_object_or_404(Moneda, pk=moneda_id)
            
            # Cambiar el estado de la moneda
            moneda.activa = not moneda.activa
            moneda.save()
            
            estado_texto = "activada" if moneda.activa else "desactivada"
            messages.success(request, f'Moneda "{moneda.nombre}" {estado_texto} exitosamente.')
        except Exception as e:
            messages.error(request, 'Error al cambiar el estado de la moneda.')
    
    # Obtener todas las monedas
    monedas = Moneda.objects.all()
    
    # Manejar búsqueda
    busqueda = request.GET.get('busqueda', '').strip()
    if busqueda:
        monedas = monedas.filter(
            Q(nombre__icontains=busqueda) | 
            Q(simbolo__icontains=busqueda)
        )
    
    # Ordenar por nombre
    monedas = monedas.order_by('nombre')
    
    # Calcular estadísticas
    monedas_activas = monedas.filter(activa=True).count()
    monedas_inactivas = monedas.filter(activa=False).count()
    
    context = {
        'monedas': monedas,
        'monedas_activas': monedas_activas,
        'monedas_inactivas': monedas_inactivas,
        'busqueda': busqueda,
    }
    return render(request, 'monedas/moneda_lista.html', context)

@login_required
@permission_required('monedas.editar', raise_exception=True)
def moneda_editar(request, pk):
    moneda = get_object_or_404(Moneda, pk=pk)
    if request.method == 'POST':
        form = MonedaForm(request.POST, instance=moneda)
        if form.is_valid():
            form.save()
            messages.success(request, f'Moneda "{moneda.nombre}" actualizada exitosamente.')
            return redirect('monedas:lista_monedas')
    else:
        form = MonedaForm(instance=moneda)
    return render(request, 'monedas/moneda_form.html', {'form': form, 'moneda': moneda, 'accion': 'Editar'})