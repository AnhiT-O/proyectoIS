from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from functools import wraps
from .forms import RegistroUsuarioForm, RecuperarPasswordForm, EstablecerPasswordForm, AsignarRolForm, AsignarClienteForm
from .models import Usuario
from clientes.models import Cliente, UsuarioCliente
from roles.models import Roles
from django.db.models import Q

def tiene_algun_permiso(view_func):
    """
    Decorador que verifica si el usuario tiene al menos uno de los permisos necesarios
    para administrar usuarios: bloqueo, asignación de roles o asignación de clientes.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        # Permisos requeridos para administrar usuarios
        permisos_requeridos = [
            'usuarios.bloqueo',                 # Permiso para bloquear usuarios
            'usuarios.asignacion_roles',        # Permiso para asignar roles
            'usuarios.asignacion_clientes'      # Permiso para asignar clientes
        ]
        
        # Verificar si el usuario tiene al menos uno de los permisos
        for permiso in permisos_requeridos:
            if request.user.has_perm(permiso):
                return view_func(request, *args, **kwargs)
        
        # Si no tiene ningún permiso, denegar acceso
        raise PermissionDenied()
    
    return _wrapped_view

def registro_usuario(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Enviar email de confirmación
            enviar_email_confirmacion(request, user)
            messages.success(request, '¡Registro exitoso! Por favor, verifica tu correo para activar tu cuenta.')
            return redirect('login')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'usuarios/registro.html', {'form': form})

def enviar_email_confirmacion(request, user):
    # token de activación
    token = default_token_generator.make_token(user)
    # identificador del usuario a activar
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    # generación de enlace de activación
    activacion_url = request.build_absolute_uri(
        reverse('usuarios:activar_cuenta', kwargs={'uidb64': uid, 'token': token})
    )
    
    # transforma el HTML en formato de correo
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

    from_email = getattr(settings, 'EMAIL_HOST_USER', 'noreply@localhost')
    
    msg = EmailMultiAlternatives(
        subject='Confirma tu cuenta',
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
        operador_role = Group.objects.get(name='Operador')
        user.groups.add(operador_role)
        user.save()
        login(request, user)
        messages.success(request, '¡Cuenta activada exitosamente! Bienvenido.')
        return redirect('inicio')
    else:
        # Si el usuario existe pero el token es inválido o expiró
        if user is not None:
            # Verificar si el usuario no está activo (nunca activó su cuenta)
            if not user.is_active:
                # Eliminar el usuario de la base de datos
                user.delete()
                messages.error(request, 
                    'El enlace de activación ha expirado y tu cuenta ha sido eliminada.'
                    'Por favor, regístrate nuevamente.')
            else:
                # Si el usuario ya está activo, solo mostrar error de enlace inválido
                messages.error(request, 'El enlace de activación ya se usó.')
        else:
            messages.error(request, 'Hubo un error inesperado. Contacta a soporte.')

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
            user = Usuario.objects.get(email=email)
            
            # Enviar email de recuperación
            enviar_email_recuperacion(request, user)
            
            messages.success(request, 
                'Se ha enviado un enlace de recuperación a tu correo electrónico. '
                'Revisa tu bandeja de entrada y sigue las instrucciones.')
            return redirect('login')
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
    
    # Crear contenido HTML
    html_content = render_to_string('usuarios/email_recuperacion.html', {
        'user': user,
        'reset_url': reset_url,
    })
    
    # Crear versión de texto plano (fallback)
    text_content = f"""
¡Hola {user.first_name}!

Has solicitado recuperar tu contraseña en Global Exchange.

Para crear una nueva contraseña, por favor visita el siguiente enlace:
{reset_url}

Este enlace expirará en una hora por seguridad.

Si no solicitaste este cambio, puedes ignorar este correo y tu contraseña permanecerá sin cambios.

Saludos,
El equipo de Global Exchange
    """.strip()
    
    # Crear email con HTML y texto plano
    from_email = getattr(settings, 'EMAIL_HOST_USER', 'noreply@localhost')
    
    msg = EmailMultiAlternatives(
        subject='Recuperación de contraseña - Global Exchange',
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
                return redirect('login')
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
@tiene_algun_permiso
def usuario_detalle(request, pk):
    """Vista para mostrar detalles de un usuario"""
    try:
        usuario = Usuario.objects.get(pk=pk)
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('usuarios:administrar_usuarios')
    
    # Obtener información adicional del usuario
    roles = usuario.groups.all()
    clientes_asignados = usuario.clientes_operados.all()
    
    context = {
        'usuario': usuario,
        'roles': roles,
        'clientes_asignados': clientes_asignados,
        'total_clientes': clientes_asignados.count(),
        'es_operador': any(rol.name == 'Operador' for rol in roles)
    }
    
    return render(request, 'usuarios/usuario_detalle.html', context)


@login_required
@tiene_algun_permiso
def administrar_usuarios(request):
    """Vista para administrar usuarios (para usuarios con permisos de bloqueo)"""
    # Obtener el término de búsqueda
    busqueda = request.GET.get('busqueda', '').strip()
    
    # Iniciar el queryset base excluyendo al usuario actual
    usuarios = Usuario.objects.exclude(pk=request.user.pk)
    
    # Aplicar filtro de búsqueda si existe
    if busqueda:
        usuarios = usuarios.filter(
            Q(first_name__icontains=busqueda) |
            Q(last_name__icontains=busqueda) |
            Q(username__icontains=busqueda)
        )
    
    # Ordenar resultados
    usuarios = usuarios.order_by('first_name', 'last_name')
    
    # Calcular estadísticas
    total_usuarios = usuarios.count()
    usuarios_activos = usuarios.filter(bloqueado=False).count()
    usuarios_bloqueados = usuarios.filter(bloqueado=True).count()
    
    return render(request, 'usuarios/administrar_usuarios.html', {
        'usuarios': usuarios,
        'busqueda': busqueda,
        'total_usuarios': total_usuarios,
        'usuarios_activos': usuarios_activos,
        'usuarios_bloqueados': usuarios_bloqueados
    })

@login_required
@permission_required('usuarios.bloqueo', raise_exception=True)
def bloquear_usuario(request, pk):
    """Vista para bloquear/desbloquear usuarios"""
    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect('usuarios:administrar_usuarios')
    
    try:
        usuario = Usuario.objects.get(pk=pk)
        
        # No permitir bloquear otros administradores (solo si es administrador)
        if usuario.groups.filter(name='Administrador').exists() and not request.user.groups.filter(name='Administrador').exists():
            messages.error(request, 'No puedes bloquear a otros administradores.')
            return redirect('usuarios:administrar_usuarios')
        
        # Cambiar estado de bloqueo del usuario
        usuario.bloqueado = not usuario.bloqueado
        usuario.save()
        
        estado = 'desbloqueado' if not usuario.bloqueado else 'bloqueado'
        messages.success(request, f'El usuario {usuario.get_full_name()} ha sido {estado}.')
        
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
    
    return redirect('usuarios:administrar_usuarios')


@login_required
@permission_required('usuarios.asignacion_roles', raise_exception=True)
def asignar_rol(request, pk):
    """Vista para asignar roles a usuarios"""
    try:
        usuario = Usuario.objects.get(pk=pk)
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('usuarios:administrar_usuarios')

    # No permitir asignar roles a otros administradores (solo si es administrador)
    if usuario.groups.filter(name='Administrador').exists() and not request.user.groups.filter(name='Administrador').exists():
        messages.error(request, 'No puedes modificar los roles de otros administradores.')
        return redirect('usuarios:administrar_usuarios')

    if request.method == 'POST':
        form = AsignarRolForm(request.POST, usuario=usuario)
        if form.is_valid():
            roles = form.cleaned_data['rol']
            for rol in roles:
                usuario.groups.add(rol)
            if len(roles) == 1:
                messages.success(request, f'Rol "{list(roles)[0]}" asignado exitosamente a {usuario.get_full_name()}.')
            else:
                messages.success(request, f'{len(roles)} roles asignados exitosamente a {usuario.get_full_name()}.')
            return redirect('usuarios:administrar_usuarios')
    else:
        form = AsignarRolForm(usuario=usuario)
        # Verificar si hay roles disponibles para asignar
        if not form.fields['rol'].queryset.exists():
            messages.info(request, f'{usuario.get_full_name()} ya tiene todos los roles disponibles asignados.')
            return redirect('usuarios:administrar_usuarios')

    return render(request, 'usuarios/asignar_rol.html', {
        'form': form,
        'usuario': usuario,
        'roles_disponibles': Roles.objects.exclude(name='Administrador').exclude(
            id__in=usuario.groups.all().values_list('id', flat=True)
        ).order_by('name')
    })


@login_required
@permission_required('usuarios.asignacion_roles', raise_exception=True)
def remover_rol(request, pk, rol_id):
    """Vista para remover roles de usuarios"""
    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect('usuarios:administrar_usuarios')
    
    try:
        usuario = Usuario.objects.get(pk=pk)
        rol = Group.objects.get(pk=rol_id)
    except:
        messages.error(request, 'Usuario o rol no encontrado.')
        return redirect('usuarios:administrar_usuarios')
    # No permitir modificar roles de administradores (solo si es administrador)
    if usuario.groups.filter(name='Administrador').exists() and not request.user.groups.filter(name='Administrador').exists():
        messages.error(request, 'No puedes modificar los roles de otros administradores.')
        return redirect('usuarios:administrar_usuarios')
    
    # Si el rol a remover es 'Operador', desasociar todos los clientes del usuario
    if rol.name == 'Operador':
        clientes_asociados = usuario.clientes_operados.all()
        for cliente in clientes_asociados:
            try:
                relacion = UsuarioCliente.objects.get(usuario=usuario, cliente=cliente)
                relacion.delete()
            except UsuarioCliente.DoesNotExist:
                pass
    usuario.groups.remove(rol)
    messages.success(request, f'Rol "{rol.name}" removido exitosamente de {usuario.get_full_name()}.')
    return redirect('usuarios:administrar_usuarios')


@login_required
@permission_required('usuarios.asignacion_clientes', raise_exception=True)
def asignar_clientes(request, pk):
    """Vista para asignar clientes a usuarios"""
    try:
        usuario = Usuario.objects.get(pk=pk)
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('usuarios:administrar_usuarios')
    
    # Solo permitir asignar clientes a usuarios con rol 'Operador'
    if not usuario.groups.filter(name='Operador').exists():
        messages.error(request, 'Solo puedes asignar clientes a usuarios con rol Operador.')
        return redirect('usuarios:administrar_usuarios')
    
    # Verificar si existen clientes creados en el sistema
    if not Cliente.objects.exists():
        messages.info(request, 'No hay clientes creados en el sistema. Primero se deben crear clientes antes de poder asignarlos.')
        return redirect('usuarios:administrar_usuarios')
    
    if request.method == 'POST':
        form = AsignarClienteForm(request.POST, usuario=usuario)
        if form.is_valid():
            clientes = form.cleaned_data['clientes']
            # Crear las relaciones usuario-cliente
            for cliente in clientes:
                UsuarioCliente.objects.get_or_create(
                    usuario=usuario,
                    cliente=cliente
                )
            
            if len(clientes) == 1:
                messages.success(request, f'Cliente "{clientes.first()}" asignado exitosamente a {usuario.get_full_name()}.')
            else:
                messages.success(request, f'{len(clientes)} clientes asignados exitosamente a {usuario.get_full_name()}.')
            return redirect('usuarios:usuario_detalle', pk=usuario.pk)
    else:
        form = AsignarClienteForm(usuario=usuario)
    
    # Verificar si hay clientes disponibles para asignar
    if not form.fields['clientes'].queryset.exists():
        messages.info(request, f'{usuario.get_full_name()} ya tiene todos los clientes disponibles asignados.')
        return redirect('usuarios:usuario_detalle', pk=usuario.pk)

    return render(request, 'usuarios/asignar_clientes.html', {
        'form': form,
        'usuario': usuario
    })

@login_required
@permission_required('usuarios.asignacion_clientes', raise_exception=True)
def remover_cliente(request, pk, cliente_id):
    """Vista para remover la asignación de un cliente a un usuario"""
    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect('usuarios:administrar_usuarios')
    
    try:
        usuario = Usuario.objects.get(pk=pk)
        cliente = Cliente.objects.get(pk=cliente_id)
    except:
        messages.error(request, 'Usuario o cliente no encontrado.')
        return redirect('usuarios:administrar_usuarios')
    
    # Verificar que la relación existe
    try:
        relacion = UsuarioCliente.objects.get(usuario=usuario, cliente=cliente)
        relacion.delete()
        messages.success(request, f'Cliente "{cliente}" desasignado exitosamente de {usuario.get_full_name()}.')
    except UsuarioCliente.DoesNotExist:
        messages.error(request, 'La asignación no existe.')

    return redirect('usuarios:usuario_detalle', pk=usuario.pk)


@login_required
@permission_required('usuarios.asignacion_clientes', raise_exception=True)
def ver_clientes_usuario(request, pk):
    """Vista para ver todos los clientes asignados a un usuario"""
    try:
        usuario = Usuario.objects.get(pk=pk)
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('usuarios:administrar_usuarios')
    clientes_asignados = usuario.clientes_operados.all().order_by('nombre', 'apellido')
    
    return render(request, 'usuarios/ver_clientes_usuario.html', {
        'usuario': usuario,
        'clientes_asignados': clientes_asignados
    })

