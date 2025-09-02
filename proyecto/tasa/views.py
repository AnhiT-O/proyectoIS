from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
from .models import TasaCambio
from .forms import TasaCambioForm

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

@login_required
def lista_tasas(request):
    if not any(group.name in ['administrador', 'analista cambiario'] for group in request.user.groups.all()):
        raise PermissionDenied
    
    if request.method == 'POST' and request.user.has_perm('tasa.activar_tasa'):
        if 'cambiar_estado' in request.POST:
            tasa_id = request.POST.get('tasa_id')
            tasa = get_object_or_404(TasaCambio, id=tasa_id)
            tasa.activa = not tasa.activa
            tasa.ultimo_editor = request.user
            tasa.save()
            estado = "activada" if tasa.activa else "desactivada"
            messages.success(request, f'La tasa de cambio para {tasa.moneda.nombre} ha sido {estado} exitosamente.')
            return redirect('tasa:lista_tasas')
    
    # Lógica de búsqueda
    query = request.GET.get('q')
    
    # Si es analista cambiario, solo mostrar tasas activas
    if request.user.groups.filter(name='analista cambiario').exists():
        tasas = TasaCambio.objects.select_related('moneda', 'ultimo_editor').filter(activa=True)
    else:
        # Para administradores, mostrar todas las tasas
        tasas = TasaCambio.objects.select_related('moneda', 'ultimo_editor').all()
    if query:
        tasas = TasaCambio.objects.select_related('moneda', 'ultimo_editor').filter(
            moneda__nombre__icontains=query
        )
    return render(request, 'tasa/lista_tasas.html', {'tasas': tasas})

@permission_required('tasa.crear_tasa')
def crear_tasa(request):
    if request.method == 'POST':
        form = TasaCambioForm(request.POST)
        if form.is_valid():
            tasa = form.save(commit=False)
            tasa.ultimo_editor = request.user
            tasa.save()
            messages.success(request, 'Tasa de cambio creada exitosamente.')
            return redirect('tasa:lista_tasas')
    else:
        form = TasaCambioForm()
    
    return render(request, 'tasa/form_tasa.html', {'form': form})

@permission_required('tasa.editar_tasa')
def editar_tasa(request, tasa_id):
    tasa = get_object_or_404(TasaCambio, id=tasa_id)
    
    # Verificar si el usuario es analista cambiario y la tasa está inactiva
    if request.user.groups.filter(name='analista cambiario').exists() and not tasa.activa:
        messages.error(request, 'No tienes permiso para editar tasas inactivas.')
        return redirect('tasa:lista_tasas')
    
    if request.method == 'POST':
        form = TasaCambioForm(request.POST, instance=tasa)
        if form.is_valid():
            if form.has_changed():
                tasa = form.save(commit=False)
                tasa.ultimo_editor = request.user
                tasa.save()
                messages.success(request, 'Tasa de cambio actualizada exitosamente.')
            else:
                messages.info(request, 'No se detectaron cambios en la tasa de cambio.')
            return redirect('tasa:lista_tasas')
    else:
        form = TasaCambioForm(instance=tasa)
    
    return render(request, 'tasa/form_tasa.html', {'form': form, 'tasa': tasa})

@permission_required('tasa.activar_tasa')
def activar_tasa(request, tasa_id):
    if request.method == 'POST':
        tasa = get_object_or_404(TasaCambio, id=tasa_id)
        tasa.activa = not tasa.activa
        tasa.ultimo_editor = request.user
        tasa.save()
        estado = "activada" if tasa.activa else "desactivada"
        messages.success(request, f'Tasa de cambio {estado} exitosamente.')
    return redirect('tasa:lista_tasas')
