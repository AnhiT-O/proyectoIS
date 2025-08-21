from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse
from .forms import RegistroUsuarioForm, LoginForm, RecuperarPasswordForm, EstablecerPasswordForm
from .models import Usuario

def login_usuario(request):
    if request.user.is_authenticated:
        return redirect('usuarios:perfil')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'¡Bienvenido de nuevo, {user.first_name}!')
                    # Redirigir a la página que el usuario intentaba acceder o al perfil
                    next_page = request.GET.get('next', 'usuarios:perfil')
                    return redirect(next_page)
                else:
                    messages.error(request, 'Tu cuenta no está activada. Revisa tu correo electrónico.')
            else:
                messages.error(request, 'Nombre de usuario o contraseña incorrectos.')
    else:
        form = LoginForm()
    
    return render(request, 'usuarios/login.html', {'form': form})

def logout_usuario(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('usuarios:login')

def registro_usuario(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Enviar email de confirmación
            enviar_email_confirmacion(request, user)
            
            return redirect('usuarios:registro_exitoso')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'usuarios/registro.html', {'form': form})

def enviar_email_confirmacion(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    activacion_url = request.build_absolute_uri(
        reverse('usuarios:activar_cuenta', kwargs={'uidb64': uid, 'token': token})
    )
    
    subject = 'Confirma tu cuenta'
    
    # Crear contenido HTML
    html_content = render_to_string('usuarios/email_confirmacion.html', {
        'user': user,
        'activacion_url': activacion_url,
    })
    
    # Crear versión de texto plano (fallback)
    text_content = f"""
¡Hola {user.first_name}!

Gracias por registrarte en nuestro sistema.

Para activar tu cuenta, por favor visita el siguiente enlace:
{activacion_url}

Si no solicitaste esta cuenta, puedes ignorar este correo.

Saludos,
El equipo de desarrollo
    """.strip()
    
    # Crear email con HTML y texto plano
    from_email = getattr(settings, 'EMAIL_HOST_USER', 'noreply@localhost')
    
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,  # Contenido de texto plano
        from_email=from_email,
        to=[user.email]
    )
    
    # Adjuntar la versión HTML
    msg.attach_alternative(html_content, "text/html")
    
    # Enviar el email
    msg.send()

def activar_cuenta(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Usuario.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, '¡Cuenta activada exitosamente! Bienvenido.')
        return redirect('usuarios:perfil')
    else:
        messages.error(request, 'El enlace de activación es inválido o ha expirado.')
        return redirect('usuarios:registro')

def registro_exitoso(request):
    return render(request, 'usuarios/registro_exitoso.html')

@login_required
def perfil(request):
    return render(request, 'usuarios/perfil.html')


def recuperar_password(request):
    """Vista para solicitar recuperación de contraseña"""
    if request.method == 'POST':
        form = RecuperarPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            # Obtener el usuario
            user = Usuario.objects.get(email=email, is_active=True)
            
            # Enviar email de recuperación
            enviar_email_recuperacion(request, user)
            
            messages.success(request, 
                'Se ha enviado un enlace de recuperación a tu correo electrónico. '
                'Revisa tu bandeja de entrada y sigue las instrucciones.')
            return redirect('usuarios:login')
    else:
        form = RecuperarPasswordForm()
    
    return render(request, 'usuarios/recuperar_password.html', {'form': form})


def enviar_email_recuperacion(request, user):
    """Envía email con enlace para recuperar contraseña"""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    reset_url = request.build_absolute_uri(
        reverse('usuarios:reset_password_confirm', kwargs={'uidb64': uid, 'token': token})
    )
    
    subject = 'Recuperación de contraseña - Casa de Cambios'
    
    # Crear contenido HTML
    html_content = render_to_string('usuarios/email_recuperacion.html', {
        'user': user,
        'reset_url': reset_url,
    })
    
    # Crear versión de texto plano (fallback)
    text_content = f"""
¡Hola {user.first_name}!

Has solicitado recuperar tu contraseña en Casa de Cambios.

Para crear una nueva contraseña, por favor visita el siguiente enlace:
{reset_url}

Este enlace expirará en 24 horas por seguridad.

Si no solicitaste este cambio, puedes ignorar este correo y tu contraseña permanecerá sin cambios.

Saludos,
El equipo de Casa de Cambios
    """.strip()
    
    # Crear email con HTML y texto plano
    from_email = getattr(settings, 'EMAIL_HOST_USER', 'noreply@localhost')
    
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,  # Contenido de texto plano
        from_email=from_email,
        to=[user.email]
    )
    
    # Adjuntar la versión HTML
    msg.attach_alternative(html_content, "text/html")
    
    # Enviar el email
    msg.send()


def reset_password_confirm(request, uidb64, token):
    """Vista para confirmar y establecer nueva contraseña"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Usuario.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = EstablecerPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 
                    '¡Tu contraseña ha sido cambiada exitosamente! '
                    'Ya puedes iniciar sesión con tu nueva contraseña.')
                return redirect('usuarios:login')
        else:
            form = EstablecerPasswordForm(user)
        
        return render(request, 'usuarios/reset_password_confirm.html', {
            'form': form,
            'validlink': True
        })
    else:
        messages.error(request, 
            'El enlace de recuperación es inválido o ha expirado. '
            'Por favor, solicita un nuevo enlace de recuperación.')
        return redirect('usuarios:recuperar_password')

@login_required
def administrar_usuarios(request):
    """Vista para administrar usuarios (solo para administradores)"""
    # Verificar si el usuario es administrador
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('usuarios:perfil')
    
    # Obtener todos los usuarios excepto el actual
    usuarios = Usuario.objects.exclude(pk=request.user.pk).order_by('first_name', 'last_name')
    
    return render(request, 'usuarios/administrar_usuarios.html', {
        'usuarios': usuarios
    })

@login_required
def bloquear_usuario(request, pk):
    """Vista para bloquear/desbloquear usuarios"""
    # Verificar si el usuario es administrador
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('usuarios:perfil')
    
    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect('usuarios:administrar_usuarios')
    
    try:
        usuario = Usuario.objects.get(pk=pk)
        
        # No permitir bloquear otros administradores
        if usuario.is_staff:
            messages.error(request, 'No puedes bloquear a otros administradores.')
            return redirect('usuarios:administrar_usuarios')
        
        # Cambiar estado del usuario
        usuario.is_active = not usuario.is_active
        usuario.save()
        
        estado = 'desbloqueado' if usuario.is_active else 'bloqueado'
        messages.success(request, f'El usuario {usuario.get_full_name()} ha sido {estado}.')
        
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
    
    return redirect('usuarios:administrar_usuarios')

@login_required
def eliminar_usuario(request, pk):
    """Vista para eliminar usuarios"""
    # Verificar si el usuario es administrador
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('usuarios:perfil')
    
    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect('usuarios:administrar_usuarios')
    
    try:
        usuario = Usuario.objects.get(pk=pk)
        
        # No permitir eliminar administradores
        if usuario.is_staff:
            messages.error(request, 'No puedes eliminar a otros administradores.')
            return redirect('usuarios:administrar_usuarios')
        
        nombre_completo = usuario.get_full_name()
        usuario.delete()
        messages.success(request, f'El usuario {nombre_completo} ha sido eliminado permanentemente.')
        
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
    
    return redirect('usuarios:administrar_usuarios')

