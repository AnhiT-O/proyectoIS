from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Permission
from .models import Roles
from .forms import RolForm
from django.urls import reverse
from functools import wraps

def admin_required(view_func):
    """Decorator para asegurar que solo los administradores puedan acceder"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.es_administrador():
            raise PermissionDenied("No tienes permisos para acceder a esta página.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
@admin_required
def listar_roles(request):
    # Obtener todos los roles, excluyendo el rol administrador si es necesario
    roles = Roles.objects.exclude(name='administrador')
    return render(request, 'roles/listar_roles.html', {'roles': roles})

@login_required
@admin_required
def crear_rol(request):
    if request.method == 'POST':
        form = RolForm(request.POST)
        if form.is_valid():
            rol = form.save()
            messages.success(request, 'Rol creado exitosamente.')
            return redirect('listar_roles')
    else:
        form = RolForm()
    return render(request, 'roles/rol_form.html', {
        'form': form,
        'titulo': 'Crear Nuevo Rol'
    })

@login_required
@admin_required
def editar_rol(request, pk):
    rol = get_object_or_404(Roles, pk=pk)
    if rol.name == 'administrador':  # Si es el rol admin
        messages.error(request, 'No se puede editar el rol de administrador.')
        return redirect('listar_roles')
        
    if request.method == 'POST':
        form = RolForm(request.POST, instance=rol)
        if form.is_valid():
            rol = form.save()
            messages.success(request, 'Rol actualizado exitosamente.')
            return redirect('listar_roles')
    else:
        form = RolForm(instance=rol)
    return render(request, 'roles/rol_form.html', {
        'form': form,
        'titulo': 'Editar Rol',
        'rol': rol
    })

@login_required
@admin_required
def detalle_rol(request, pk):
    rol = get_object_or_404(Roles, pk=pk)
    return render(request, 'roles/detalle_rol.html', {'rol': rol})
