from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Permission
from .models import Roles
from .forms import RolForm
from django.urls import reverse
from functools import wraps

@login_required
@permission_required('roles.gestion', raise_exception=True)
def listar_roles(request):
    roles = Roles.objects.exclude(name='administrador')
    return render(request, 'roles/listar_roles.html', {'roles': roles})

@login_required
@permission_required('roles.gestion', raise_exception=True)
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
@permission_required('roles.gestion', raise_exception=True)
def editar_rol(request, pk):
    rol = get_object_or_404(Roles, pk=pk)
    
    # Solo administradores pueden editar el rol administrador
    if rol.name == 'administrador' and not request.user.es_administrador():
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
@permission_required('roles.gestion', raise_exception=True)
def detalle_rol(request, pk):
    rol = get_object_or_404(Roles, pk=pk)
    return render(request, 'roles/detalle_rol.html', {'rol': rol})
