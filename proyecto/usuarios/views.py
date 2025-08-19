from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse
from .forms import RegistroUsuarioForm
from .models import Usuario

def registro_usuario(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            # Verificar si existe un usuario inactivo con los mismos datos
            cedula = form.cleaned_data['cedula_identidad']
            email = form.cleaned_data['email']
            
            existing_user = Usuario.objects.filter(
                cedula_identidad=cedula, 
                email=email, 
                is_active=False
            ).first()
            
            if existing_user:
                # Reenviar email de confirmación al usuario existente
                enviar_email_confirmacion(request, existing_user)
                messages.info(request, 'Ya tienes una cuenta pendiente de activación. Te hemos reenviado el correo de confirmación.')
                return redirect('usuarios:registro_exitoso')
            
            user = form.save()
            
            # Enviar email de confirmación
            enviar_email_confirmacion(request, user)
            
            messages.success(request, 'Registro exitoso. Revisa tu correo electrónico para activar tu cuenta.')
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
    message = render_to_string('usuarios/email_confirmacion.html', {
        'user': user,
        'activacion_url': activacion_url,
    })
    
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

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

def perfil(request):
    return render(request, 'usuarios/perfil.html')

