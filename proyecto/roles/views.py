from functools import wraps
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from .models import Roles
from .forms import RolForm
from django.core.exceptions import PermissionDenied

def permiso_administrador(view_func):
    """
    Decorador que verifica si el usuario tiene al menos uno de los permisos necesarios
    para administrar monedas: creación, edición o activación.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        if request.user.es_admin:
            return view_func(request, *args, **kwargs)

        # Si no tiene ningún permiso, denegar acceso
        raise PermissionDenied()

    return _wrapped_view

@login_required
@permiso_administrador
def listar_roles(request):
    """
    Muestra una lista de todos los roles disponibles para asignar, excepto 'Administrador'.

    Args:
        request: Objeto solicitante.
    """

    roles = Roles.objects.exclude(name='Administrador')
    contexto = {'roles': roles}
    return render(request, 'roles/listar_roles.html', contexto)

@login_required
@permiso_administrador
def crear_rol(request):
    """
    Gestiona el formulario para crear un nuevo rol.

    -   Si el método es GET, muestra el formulario para completarlo.
    -   Si el método es POST, valida el formulario y crea el nuevo rol.

    Args:
        request: Objeto solicitante.

    Raises:
        Exception: Si ocurre un error al guardar el rol.
    """

    if request.method == 'POST':
        form = RolForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Rol creado exitosamente.')
            except Exception as e:
                messages.error(request, f'Error al crear rol: {e}')
            return redirect('roles:listar_roles')
    else:
        form = RolForm()

    contexto = {
        'form': form
    }
    return render(request, 'roles/rol_form.html', contexto)

@login_required
@permiso_administrador
def editar_rol(request, pk):
    """
    Gestiona el formulario para editar un rol existente.

    -   Si el método es GET, muestra el formulario con los datos actuales del rol.
    -   Si el método es POST, valida el formulario y actualiza el rol.

    Args:
        request: Objeto solicitante.
        pk: Clave primaria del rol a editar.

    Raises:
        Roles.DoesNotExist: Si el rol no existe.
        Exception: Si ocurre un error al guardar el rol.
    """

    try:
        rol = Roles.objects.get(pk=pk)
    except Roles.DoesNotExist:
        messages.error(request, 'Rol no encontrado.')
        return redirect('roles:listar_roles')
        
    if request.method == 'POST':
        form = RolForm(request.POST, instance=rol)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Rol editado exitosamente.')
            except Exception as e:
                messages.error(request, f'Error al editar rol: {e}')
            return redirect('roles:listar_roles')
    else:
        form = RolForm(instance=rol)

    contexto = {
        'form': form,
        'rol': rol
    }
    return render(request, 'roles/rol_form.html', contexto)

@login_required
@permiso_administrador
def detalle_rol(request, pk):
    """
    Muestra los detalles de un rol específico (nombre, descripción y permisos).

    Args:
        request: Objeto solicitante.
        pk: Clave primaria del rol a mostrar.
    
    Raises:
        Roles.DoesNotExist: Si el rol no existe.
    """
    try:
        rol = Roles.objects.get(pk=pk)
    except Roles.DoesNotExist:
        messages.error(request, 'Rol no encontrado.')
        return redirect('roles:listar_roles')
    
    contexto = {'rol': rol}
    return render(request, 'roles/detalle_rol.html', contexto)
