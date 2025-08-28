from django.shortcuts import redirect, render
from django.http import HttpResponseForbidden
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages

from .forms import LoginForm
from usuarios.models import Usuario

def inicio(request):
    """Vista para la página de inicio"""
    return render(request, 'inicio.html')

def custom_permission_denied_view(request, exception):
    """
    Vista personalizada para manejar errores 403 (Permission Denied)
    Se renderiza cuando un usuario autenticado no tiene permisos para acceder a una vista
    """
    return HttpResponseForbidden(render(request, '403.html').content)

def login_usuario(request):
    if request.user.is_authenticated:
        return redirect('usuarios:perfil')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            try:
                # Primero verificamos si el usuario existe
                user = Usuario.objects.get(username=username)
                
                # Si el usuario está bloqueado, mostramos mensaje específico
                if user.bloqueado:
                    return render(request, 'usuarios/login.html', {
                        'form': form,
                        'usuario_bloqueado': True,
                        'nombre_usuario': user.get_full_name()
                    })
                if not user.is_active:
                    return render(request, 'usuarios/login.html', {
                        'form': form,
                        'usuario_inactivo': True,
                        'nombre_usuario': user.get_full_name()
                    })

                # Si no está bloqueado, intentamos autenticar
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, f'¡Bienvenido de nuevo, {user.first_name}!')
                    next_page = request.GET.get('next', 'usuarios:perfil')
                    return redirect(next_page)
                else:
                    messages.error(request, 'La contraseña ingresada es incorrecta.')
            except Usuario.DoesNotExist:
                messages.error(request, 'No existe un usuario con ese nombre de usuario.')
    else:
        form = LoginForm()
    
    return render(request, 'usuarios/login.html', {'form': form})

def logout_usuario(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('inicio')