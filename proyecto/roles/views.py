from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from .models import Roles
from .forms import RolForm

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
            form.save()
            messages.success(request, 'Rol creado exitosamente.')
            return redirect('roles:listar_roles')
    else:
        form = RolForm()
    return render(request, 'roles/rol_form.html', {
        'form': form,
        'titulo': 'Nuevo Rol'
    })

@login_required
@permission_required('roles.gestion', raise_exception=True)
def editar_rol(request, pk):
    try:
        rol = Roles.objects.get(pk=pk)
    except Roles.DoesNotExist:
        messages.error(request, 'Rol no encontrado.')
        return redirect('roles:listar_roles')
        
    if request.method == 'POST':
        form = RolForm(request.POST, instance=rol)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rol actualizado exitosamente.')
            return redirect('roles:listar_roles')
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
    try:
        rol = Roles.objects.get(pk=pk)
    except Roles.DoesNotExist:
        messages.error(request, 'Rol no encontrado.')
        return redirect('roles:listar_roles')
    return render(request, 'roles/detalle_rol.html', {'rol': rol})
