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
from .forms import RegistroUsuarioForm, LoginForm
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

