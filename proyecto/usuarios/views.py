from django.shortcuts import get_object_or_404, render, redirect
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
from django.utils import timezone
from functools import wraps
from .forms import RegistroUsuarioForm, RecuperarPasswordForm, EstablecerPasswordForm, AsignarRolForm, AsignarClienteForm, EditarPerfilForm
from .models import Usuario
from clientes.models import Cliente
from clientes.views import procesar_medios_acreditacion_cliente
from clientes.exceptions import TarjetaNoPermitida, MarcaNoPermitida
from roles.models import Roles
from django.db.models import Q
from django.contrib.sessions.models import Session

def tiene_algun_permiso(view_func):
    """
    Decorador que verifica si el usuario tiene al menos uno de los permisos necesarios
    para administrar usuarios: bloqueo, asignación de roles o asignación de clientes.

    Args:
        view_func (callable): La vista a envolver.

    Raises:
        PermissionDenied: Si el usuario no tiene ninguno de los permisos requeridos.
    
    Returns:
        callable: La vista envuelta que verifica los permisos.
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
    """
    Vista para registrar un nuevo usuario.

    -   Si el método es POST, procesa el formulario de registro y envía un email de confirmación de registro.
    
    -   Si el método es GET, muestra el formulario de registro para completarse.

    Raises:
        Exception: Si ocurre un error al guardar el usuario o enviar el email.
    """
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                enviar_email_confirmacion(request, user)
                messages.success(request, '¡Registro exitoso! Por favor, verifica tu correo para activar tu cuenta.')
                return redirect('inicio')
            except Exception as e:
                messages.error(request, f'Error al registrar usuario: {e}')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'usuarios/registro.html', {'form': form})

def enviar_email_confirmacion(request, user):
    """
    Envía email de confirmación de registro con enlace de activación. Genera un token seguro
    y un identificador único para el usuario, y construye un enlace de activación que
    se incluye en el email.

    Raises:
        Exception: Si ocurre un error al enviar el email.
    """
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
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
        body=text_content,  
        from_email=from_email,
        to=[user.email]
    )
    

    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send()
    except Exception as e:
        print(f'Error al enviar email de confirmación: {e}')

def activar_cuenta(request, uidb64, token):
    """
    Vista para activar la cuenta de un usuario a través del enlace enviado por email. Verifica
    el token y activa la cuenta si es válido. Si el token ha expirado y el usuario no ha activado su cuenta,
    elimina el usuario de la base de datos.

    Args:
        uidb64 (str): Identificador único del usuario codificado en base64.
        token (str): Token de activación.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Usuario.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.groups.add(Group.objects.get(name='Operador'))
        user.save()
        login(request, user)
        messages.success(request, 'Cuenta activada exitosamente. ¡Bienvenido!')
        return redirect('inicio')
    else:
        # Si el usuario existe pero el token es inválido o expiró
        if user is not None:
            # Verificar si el usuario no está activo (nunca activó su cuenta)
            if not user.is_active:
                # Eliminar el usuario de la base de datos
                user.delete()
                messages.warning(request, 
                    'El enlace de activación ha expirado y la cuenta ha sido eliminada.'
                    'Por favor, regístrate nuevamente.')
            else:
                # Si el usuario ya está activo, solo mostrar error de enlace inválido
                messages.error(request, 'El enlace de activación ya se usó.')
        else:
            messages.error(request, 'Hubo un error inesperado. Contacta a soporte.')

        return redirect('inicio')

@login_required
def perfil(request):
    """
    Vista para mostrar el perfil del usuario.
    """
    return render(request, 'usuarios/perfil.html')


def recuperar_password(request):
    """
    Vista para solicitar recuperación de contraseña. 
    
    -   Si el método es POST, procesa el formulario de recuperación y envía un email con enlace para restablecer la contraseña.
    -   Si el método es GET, muestra el formulario para ingresar el email asociado a la cuenta.
    """
    if request.method == 'POST':
        form = RecuperarPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            # Obtener el usuario
            user = Usuario.objects.get(email=email)
            
            # Enviar email de recuperación
            enviar_email_recuperacion(request, user)

            messages.success(request, 'Se ha enviado un enlace de recuperación a tu correo electrónico. Revisa tu bandeja de entrada y sigue las instrucciones.')
            return redirect('inicio')
    else:
        form = RecuperarPasswordForm()
    
    return render(request, 'usuarios/recuperar_password.html', {'form': form})


def enviar_email_recuperacion(request, user):
    """
    Envía email con enlace para recuperar contraseña. Genera un token seguro
    y un identificador único para el usuario, y construye un enlace de restablecimiento
    que se incluye en el email.

    Raises:
        Exception: Si ocurre un error al enviar el email.
    """
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
    
    try:
        msg.send()
    except Exception as e:
        print(f'Error al enviar email de recuperación: {e}')


def reset_password_confirm(request, uidb64, token):
    """
    Vista para confirmar y establecer nueva contraseña. Verifica el token y permite al usuario
    establecer una nueva contraseña si el token es válido.

    -   Si el método es POST, procesa el formulario para establecer la nueva contraseña.
    -   Si el método es GET, muestra el formulario para ingresar la nueva contraseña.
    """
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
    """
    Vista para mostrar detalles de un usuario. Solo accesible para usuarios con permisos necesarios.

    Args:
        pk (int): ID del usuario a mostrar.
    
    Raises:
        PermissionDenied: Si el usuario no tiene permisos para ver detalles de usuarios.
        Usuario.DoesNotExist: Si el usuario con el ID proporcionado no existe.
    """
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
    """
    Vista para gestionar usuarios. Solo accesible para usuarios con permisos necesarios.
    Posee filtros de búsqueda por nombre, apellido, nombre de usuario y por roles.
    """
    # Iniciar el queryset base excluyendo al usuario actual
    usuarios = Usuario.objects.exclude(pk=request.user.pk)
    
    # Aplicar filtro de búsqueda si existe
    busqueda = request.GET.get('busqueda', '').strip()
    if busqueda:
        usuarios = usuarios.filter(
            Q(first_name__icontains=busqueda) |
            Q(last_name__icontains=busqueda) |
            Q(username__icontains=busqueda)
        )
    
    # Manejar filtro por roles
    roles_filtro = request.GET.get('roles', '').strip()
    if roles_filtro:
        usuarios = usuarios.filter(groups__name=roles_filtro)
    
    # Ordenar resultados
    usuarios = usuarios.order_by('first_name', 'last_name')
    
    # Obtener todos los roles disponibles para el filtro
    roles_disponibles = Group.objects.all().order_by('name')
    
    # Crear lista de roles con sus estadísticas para el template
    roles_con_stats = []
    for rol in roles_disponibles:
        count = Usuario.objects.exclude(pk=request.user.pk).filter(groups=rol).count()
        roles_con_stats.append({
            'name': rol.name,
            'count': count
        })
    
    # Calcular estadísticas generales
    total_usuarios = usuarios.count()
    usuarios_activos = usuarios.filter(bloqueado=False).count()
    usuarios_bloqueados = usuarios.filter(bloqueado=True).count()
    
    return render(request, 'usuarios/administrar_usuarios.html', {
        'usuarios': usuarios,
        'roles_filtro': roles_filtro,
        'busqueda': busqueda,
        'total_usuarios': total_usuarios,
        'usuarios_activos': usuarios_activos,
        'usuarios_bloqueados': usuarios_bloqueados,
        'roles_con_stats': roles_con_stats
    })

@login_required
@permission_required('usuarios.bloqueo', raise_exception=True)
def bloquear_usuario(request, pk):
    """
    Vista para bloquear/desbloquear usuarios. Solo accesible para usuarios con permiso de bloqueo.

    Args:
        pk (int): ID del usuario a bloquear/desbloquear.

    Raises:
        PermissionDenied: Si el usuario no tiene permiso para bloquear usuarios.
        Usuario.DoesNotExist: Si el usuario con el ID proporcionado no existe.

    Note:
        -   No se permite bloquear otros administradores.
        -   Si un usuario es bloqueado mientras está autenticado, se cierran todas sus sesiones activas.
    """
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
        if usuario.is_authenticated and usuario.bloqueado:
            for session in Session.objects.all():
                data = session.get_decoded()
                if data.get('_auth_user_id') == str(usuario.pk):
                    session.delete()
        estado = 'desbloqueado' if not usuario.bloqueado else 'bloqueado'
        messages.success(request, f'El usuario {usuario.nombre_completo()} ha sido {estado}.')
        
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
    
    return redirect('usuarios:administrar_usuarios')


@login_required
@permission_required('usuarios.asignacion_roles', raise_exception=True)
def asignar_rol(request, pk):
    """
    Vista para asignar roles a usuarios. Solo accesible para usuarios con permiso de asignación de roles.

    Args:
        pk (int): ID del usuario al que se le asignarán roles.
    
    Raises:
        PermissionDenied: Si el usuario no tiene permiso para asignar roles.
        Usuario.DoesNotExist: Si el usuario con el ID proporcionado no existe.

    Note:
        -   No se permite asignar roles a otros administradores.
        -   No se permite asignar el rol de 'Administrador' a través de esta vista.
    """
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
                messages.success(request, f'Rol "{list(roles)[0]}" asignado exitosamente a {usuario.nombre_completo()}.')
            else:
                messages.success(request, f'{len(roles)} roles asignados exitosamente a {usuario.nombre_completo()}.')
            return redirect('usuarios:administrar_usuarios')
    else:
        form = AsignarRolForm(usuario=usuario)
        # Verificar si hay roles disponibles para asignar
        if not form.fields['rol'].queryset.exists():
            messages.info(request, f'{usuario.nombre_completo()} ya tiene todos los roles disponibles asignados.')
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
    """
    Vista para remover roles de usuarios. Solo accesible para usuarios con permiso de asignación de roles.

    Args:
        pk (int): ID del usuario al que se le removerá el rol.
        rol_id (int): ID del rol a remover.
    
    Raises:
        PermissionDenied: Si el usuario no tiene permiso para asignar roles.
        Usuario.DoesNotExist: Si el usuario con el ID proporcionado no existe.
        Group.DoesNotExist: Si el rol con el ID proporcionado no existe.
    
    Note:
        -   No se permite modificar roles de otros administradores.
        -   Si el rol a remover es 'Operador', se desasocian todos los clientes del usuario, si hubiere.
    """
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

    if usuario.groups.count() == 1:
        messages.warning(request, 'El usuario no puede quedarse sin roles.')
        return redirect('usuarios:administrar_usuarios')

    # Si el rol a remover es 'Operador', desasociar todos los clientes del usuario
    if rol.name == 'Operador':
        clientes_asociados = usuario.clientes_operados.all()
        if usuario.cliente_activo:
            usuario.cliente_activo = None
            usuario.save()
        for cliente in clientes_asociados:
            try:
                cliente.usuarios.remove(usuario)
            except cliente.usuarios.DoesNotExist:
                pass
    usuario.groups.remove(rol)
    messages.success(request, f'Rol "{rol.name}" removido exitosamente de {usuario.nombre_completo()}.')
    return redirect('usuarios:administrar_usuarios')


@login_required
@permission_required('usuarios.asignacion_clientes', raise_exception=True)
def asignar_clientes(request, pk):
    """
    Vista para asignar clientes a usuarios.

    Args:
        pk (int): ID del usuario al que se le asignarán clientes.

    Raises:
        PermissionDenied: Si el usuario no tiene permiso para asignar clientes.
        Usuario.DoesNotExist: Si el usuario con el ID proporcionado no existe.
        Cliente.DoesNotExist: Si no existen clientes creados en el sistema.

    Note:
        -   Solo se permite asignar clientes a usuarios con rol 'Operador'.
    """
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
                cliente.usuarios.add(usuario)
            if len(clientes) == 1:
                messages.success(request, f'Cliente "{clientes.first()}" asignado exitosamente a {usuario.nombre_completo()}.')
            else:
                messages.success(request, f'{len(clientes)} clientes asignados exitosamente a {usuario.nombre_completo()}.')
            return redirect('usuarios:usuario_detalle', pk=usuario.pk)
    else:
        form = AsignarClienteForm(usuario=usuario)
    
    # Verificar si hay clientes disponibles para asignar
    if not form.fields['clientes'].queryset.exists():
        messages.info(request, f'{usuario.nombre_completo()} ya tiene todos los clientes disponibles asignados.')
        return redirect('usuarios:usuario_detalle', pk=usuario.pk)

    return render(request, 'usuarios/asignar_clientes.html', {
        'form': form,
        'usuario': usuario
    })

@login_required
@permission_required('usuarios.asignacion_clientes', raise_exception=True)
def remover_cliente(request, pk, cliente_id):
    """
    Vista para remover la asignación de un cliente a un usuario.

    Args:
        pk (int): ID del usuario al que se le removerá el cliente.
        cliente_id (int): ID del cliente a remover.
    
    Raises:
        PermissionDenied: Si el usuario no tiene permiso para asignar clientes.
        Usuario.DoesNotExist: Si el usuario con el ID proporcionado no existe.
        Cliente.DoesNotExist: Si el cliente con el ID proporcionado no existe.
    """
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
        cliente.usuarios.remove(usuario)
        if usuario.cliente_activo == cliente:
            usuario.cliente_activo = None
            usuario.save()
        messages.success(request, f'Cliente "{cliente}" desasignado exitosamente de {usuario.nombre_completo()}.')
    except cliente.usuarios.DoesNotExist:
        messages.error(request, 'La asignación no se hizo correctamente.')

    return redirect('usuarios:usuario_detalle', pk=usuario.pk)

@login_required
def ver_clientes_asociados(request):
    """
    Vista para que un usuario vea los clientes con los que está asociado.
    """
    # Obtener los clientes asociados al usuario actual
    clientes = request.user.clientes_operados.all()
    
    context = {
        'clientes': clientes,
        'total_clientes': clientes.count(),
        'cliente_activo': request.user.cliente_activo,
    }

    return render(request, 'usuarios/ver_clientes_asociados.html', context)

@login_required
def seleccionar_cliente_activo(request, cliente_id):
    """
    Vista para seleccionar un cliente como activo. El cliente activo se usa para operaciones
    que el usuario realiza en el sistema.

    Args:
        cliente_id (int): ID del cliente a seleccionar como activo.
    
    Raises:
        Cliente.DoesNotExist: Si el cliente con el ID proporcionado no existe o no está asociado al usuario.
    """
    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect('usuarios:mis_clientes')
    
    try:
        # Verificar que el cliente existe y está asociado al usuario
        cliente = request.user.clientes_operados.get(pk=cliente_id)
        
        # Asignar el cliente como activo
        request.user.cliente_activo = cliente
        request.user.save()
        
        messages.success(request, f'Cliente "{cliente.nombre}" seleccionado como cliente activo.')
        
    except Cliente.DoesNotExist:
        messages.error(request, 'Cliente no encontrado o no autorizado.')
    
    return redirect('inicio')

@login_required
def detalle_cliente(request, cliente_id):
    """
    Vista para que el usuario vea los detalles de un cliente específico asociado.

    Args:
        cliente_id (int): ID del cliente a ver.
    """
    try:
        # Verificar que el cliente existe y está asociado al usuario
        cliente = request.user.clientes_operados.get(pk=cliente_id)
        
        # Obtener las tarjetas de Stripe del cliente
        tarjetas_stripe = cliente.obtener_tarjetas_stripe()

        # Usar función auxiliar para procesar medios de acreditación
        medios_data = procesar_medios_acreditacion_cliente(cliente, request.user)
        
        context = {
            'cliente': cliente,
            'tarjetas_stripe': tarjetas_stripe,
            'total_tarjetas': len(tarjetas_stripe),
            **medios_data
        }
        
        return render(request, 'usuarios/detalle_cliente.html', context)
        
    except Cliente.DoesNotExist:
        messages.error(request, 'Cliente no encontrado o no autorizado.')
        return redirect('usuarios:mis_clientes')


@login_required
def agregar_tarjeta_cliente(request, pk):
    """
    Vista para que un operador agregue tarjeta de crédito a su cliente asignado.

    Args:
        pk (int): ID del cliente al que se le agregará la tarjeta.

    Raises:
        Cliente.DoesNotExist: Si el cliente con el ID proporcionado no existe o no está asociado al usuario.
        Exception: Si ocurre un error al agregar la tarjeta.

    Note:
        -   Se utiliza el formulario AgregarTarjetaForm del módulo clientes.forms.
    """
    try:
        # Verificar que el cliente existe y está asociado al usuario
        cliente = request.user.clientes_operados.get(pk=pk)
    except Cliente.DoesNotExist:
        messages.error(request, 'Cliente no encontrado o no autorizado.')
        return redirect('usuarios:mis_clientes')
    
    # Importar el formulario aquí para evitar dependencia circular
    from clientes.forms import AgregarTarjetaForm
    
    if request.method == 'POST':
        form = AgregarTarjetaForm(request.POST, cliente=cliente)
        if form.is_valid():
            try:
                payment_method = form.save()
                messages.success(request, 'Tarjeta agregada exitosamente.')
                return redirect('usuarios:detalle_cliente', cliente_id=pk)
                
            except TarjetaNoPermitida:
                messages.error(request, 'Solo se permiten tarjetas de crédito.')
            except MarcaNoPermitida:
                messages.error(request, 'La marca de la tarjeta no está permitida.')
            except Exception as e:
                messages.error(request, f'Error al agregar la tarjeta: {str(e)}')
    else:
        form = AgregarTarjetaForm(cliente=cliente)
    
    context = {
        'form': form,
        'cliente': cliente,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'clientes/agregar_tarjeta.html', context)


@login_required
def eliminar_tarjeta_cliente(request, pk, payment_method_id):
    """
    Vista para que un operador elimine tarjeta de crédito de su cliente asignado. Utiliza la API de Stripe
    para desadjuntar el método de pago del cliente.

    Args:
        pk (int): ID del cliente al que se le eliminará la tarjeta.
        payment_method_id (str): ID del método de pago (tarjeta) a eliminar.

    Raises:
        Cliente.DoesNotExist: Si el cliente con el ID proporcionado no existe o no está asociado al usuario.
        Exception: Si ocurre un error al eliminar la tarjeta.
    """
    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect('usuarios:mis_clientes')
    
    try:
        # Verificar que el cliente existe y está asociado al usuario
        cliente = request.user.clientes_operados.get(pk=pk)
    except Cliente.DoesNotExist:
        messages.error(request, 'Cliente no encontrado o no autorizado.')
        return redirect('usuarios:mis_clientes')
    
    import stripe
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Desadjuntar el método de pago del cliente
        stripe.PaymentMethod.detach(payment_method_id)
        messages.success(request, 'Tarjeta eliminada exitosamente.')
        
    except stripe.error.InvalidRequestError:
        messages.error(request, 'La tarjeta no existe o ya fue eliminada.')
    except stripe.error.StripeError as e:
        messages.error(request, f'Error al eliminar la tarjeta: {str(e)}')
    except Exception as e:
        logger.error(f"Error inesperado al eliminar tarjeta: {str(e)}")
        messages.error(request, 'Error inesperado al eliminar la tarjeta.')
    
    return redirect('usuarios:detalle_cliente', cliente_id=pk)




@login_required
def editar_perfil(request):
    """
    Vista para editar el perfil del usuario. Todos los campos se actualizan inmediatamente.
    """
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, instance=request.user, user=request.user)
        if form.is_valid():
            user = form.save()
            
            # Forzar recarga del usuario en la sesión si cambió contraseña
            if form.has_password_changed():
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
            
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('usuarios:perfil')
    else:
        form = EditarPerfilForm(instance=request.user, user=request.user)
    
    context = {
        'form': form,
        'usuario': request.user,
    }
    return render(request, 'usuarios/editar_perfil.html', context)


