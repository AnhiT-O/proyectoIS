import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Group, Permission
from django.contrib.messages import get_messages
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core import mail
from unittest.mock import patch, MagicMock

from usuarios.models import Usuario
from usuarios.views import (
    registro_usuario, 
    activar_cuenta, 
    recuperar_password,
    reset_password_confirm,
    bloquear_usuario,
    asignar_rol,
    asignar_clientes
)
from clientes.models import Cliente


@pytest.mark.django_db
class TestRegistroUsuarioView:
    """Pruebas para la vista de registro de usuario."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        self.client = Client()
        self.url = reverse('usuarios:registro')
    
    def test_crea_usuario_envia_email_y_redirige(self):
        """Prueba 9: Vista registro_usuario: crea usuario, envía email y redirige correctamente."""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'tipo_documento': 'CI',
            'numero_documento': '12345678',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        
        # Verificar que no hay usuarios inicialmente
        assert Usuario.objects.count() == 0
        
        # Enviar formulario
        response = self.client.post(self.url, data=form_data)
        
        # Verificar que se creó el usuario
        assert Usuario.objects.count() == 1
        user = Usuario.objects.first()
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert not user.is_active  # Usuario inactivo hasta confirmar email
        
        # Verificar que se envió email
        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert email.to == ['test@example.com']
        assert 'Confirma tu cuenta' in email.subject
        
        # Verificar redirección
        assert response.status_code == 302
        assert response.url == reverse('login')
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        assert any('¡Registro exitoso! Por favor, verifica tu correo para activar tu cuenta.' in str(m) for m in messages)


@pytest.mark.django_db
class TestActivarCuentaView:
    """Pruebas para la vista de activación de cuenta."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        self.client = Client()
        
        # Crear rol Operador (usar get_or_create para evitar duplicados)
        self.operador_role, created = Group.objects.get_or_create(name='Operador')
        
        # Crear usuario inactivo
        self.user = Usuario.objects.create(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            tipo_documento='CI',
            numero_documento='12345678',
            is_active=False
        )
        self.user.set_password('password')
        self.user.save()
    
    def test_activa_usuario_con_token_valido_asigna_rol_y_redirige(self):
        """Prueba 10: Vista activar_cuenta: activa usuario solo con token válido, asigna rol "Operador" y redirige."""
        # Generar token válido
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        url = reverse('usuarios:activar_cuenta', kwargs={'uidb64': uid, 'token': token})
        response = self.client.get(url)
        
        # Recargar usuario desde la base de datos
        self.user.refresh_from_db()
        
        # Verificar que el usuario se activó
        assert self.user.is_active
        
        # Verificar que se asignó el rol Operador
        assert self.user.groups.filter(name='Operador').exists()
        
        # Verificar redirección a inicio
        assert response.status_code == 302
        assert response.url == reverse('inicio')
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        assert any('Cuenta activada exitosamente' in str(m) for m in messages)
    
    def test_token_invalido_redirige_a_registro(self):
        """Prueba 10: Vista activar_cuenta: con token inválido redirige a registro."""
        # Token inválido
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        invalid_token = 'invalid-token'
        
        url = reverse('usuarios:activar_cuenta', kwargs={'uidb64': uid, 'token': invalid_token})
        response = self.client.get(url)
        
        # Verificar que el usuario fue eliminado (lógica de la vista)
        assert not Usuario.objects.filter(pk=self.user.pk).exists()
        
        # Verificar redirección a registro
        assert response.status_code == 302
        assert response.url == reverse('usuarios:registro')


@pytest.mark.django_db
class TestRecuperarPasswordView:
    """Pruebas para la vista de recuperación de contraseña."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        self.client = Client()
        self.url = reverse('usuarios:recuperar_password')
        
        # Crear usuario activo
        self.user = Usuario.objects.create(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            tipo_documento='CI',
            numero_documento='12345678',
            is_active=True
        )
        self.user.set_password('password')
        self.user.save()
    
    def test_envia_email_solo_si_usuario_existe_y_esta_activo(self):
        """Prueba 11: Vista recuperar_password: envía email solo si el usuario existe y está activo."""
        form_data = {
            'email': 'test@example.com'
        }
        
        response = self.client.post(self.url, data=form_data)
        
        # Verificar que se envió email
        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert email.to == ['test@example.com']
        assert 'Recuperación de contraseña' in email.subject
        
        # Verificar redirección
        assert response.status_code == 302


@pytest.mark.django_db
class TestResetPasswordConfirmView:
    """Pruebas para la vista de confirmación de restablecimiento de contraseña."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        self.client = Client()
        
        # Crear usuario activo
        self.user = Usuario.objects.create(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            tipo_documento='CI',
            numero_documento='12345678',
            is_active=True
        )
        self.user.set_password('oldpassword')
        self.user.save()
    
    def test_permite_cambiar_password_con_token_valido(self):
        """Prueba 12: Vista reset_password_confirm: permite cambiar contraseña solo con token válido."""
        # Generar token válido
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        url = reverse('usuarios:reset_password_confirm', kwargs={'uidb64': uid, 'token': token})
        
        # Primero GET para mostrar el formulario
        response = self.client.get(url)
        assert response.status_code == 200
        assert 'validlink' in response.context
        assert response.context['validlink'] == True
        
        # Luego POST para cambiar la contraseña
        form_data = {
            'new_password1': 'NewPassword123!',
            'new_password2': 'NewPassword123!'
        }
        
        response = self.client.post(url, data=form_data)
        
        # Recargar usuario desde la base de datos
        self.user.refresh_from_db()
        
        # Verificar que la contraseña cambió
        assert self.user.check_password('NewPassword123!')
        
        # Verificar redirección
        assert response.status_code == 302
    
    def test_token_invalido_redirige_a_recuperar_password(self):
        """Prueba 12: Vista reset_password_confirm: con token inválido redirige a recuperar password."""
        # Token inválido
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        invalid_token = 'invalid-token'
        
        url = reverse('usuarios:reset_password_confirm', kwargs={'uidb64': uid, 'token': invalid_token})
        response = self.client.get(url)
        
        # Verificar redirección
        assert response.status_code == 302
        assert response.url == reverse('usuarios:recuperar_password')


@pytest.mark.django_db
class TestBloquearUsuarioView:
    """Pruebas para la vista de bloqueo de usuario."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        self.client = Client()
        
        # Crear usuario administrador con permisos
        self.admin_user = Usuario.objects.create(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            tipo_documento='CI',
            numero_documento='11111111',
            is_active=True
        )
        self.admin_user.set_password('password')
        self.admin_user.save()
        
        # Asignar permiso de bloqueo
        permission = Permission.objects.get(codename='bloqueo')
        self.admin_user.user_permissions.add(permission)
        
        # Crear usuario normal
        self.normal_user = Usuario.objects.create(
            username='normal',
            email='normal@example.com',
            first_name='Normal',
            last_name='User',
            tipo_documento='CI',
            numero_documento='22222222',
            is_active=True
        )
        self.normal_user.set_password('password')
        self.normal_user.save()
    
    def test_bloquea_usuario_con_permiso_y_metodo_post(self):
        """Prueba 13: Vista bloquear_usuario: bloquea/desbloquea usuario solo con permiso y método POST."""
        # Iniciar sesión como administrador
        self.client.force_login(self.admin_user)
        
        url = reverse('usuarios:bloquear_usuario', kwargs={'pk': self.normal_user.pk})
        
        # Verificar que inicialmente no está bloqueado
        assert not self.normal_user.bloqueado
        
        # Bloquear usuario
        response = self.client.post(url)
        
        # Recargar usuario desde la base de datos
        self.normal_user.refresh_from_db()
        
        # Verificar que se bloqueó
        assert self.normal_user.bloqueado
        
        # Verificar redirección
        assert response.status_code == 302
        assert response.url == reverse('usuarios:administrar_usuarios')
        
        # Desbloquear usuario
        response = self.client.post(url)
        
        # Recargar usuario desde la base de datos
        self.normal_user.refresh_from_db()
        
        # Verificar que se desbloqueó
        assert not self.normal_user.bloqueado
    
    def test_metodo_get_no_permitido(self):
        """Prueba 13: Vista bloquear_usuario: método GET no permitido."""
        # Iniciar sesión como administrador
        self.client.force_login(self.admin_user)
        
        url = reverse('usuarios:bloquear_usuario', kwargs={'pk': self.normal_user.pk})
        
        # Intentar con GET
        response = self.client.get(url)
        
        # Verificar redirección
        assert response.status_code == 302
        assert response.url == reverse('usuarios:administrar_usuarios')


@pytest.mark.django_db
class TestAsignarRolView:
    """Pruebas para la vista de asignación de roles."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        self.client = Client()
        
        # Crear roles (usar get_or_create para evitar duplicados)
        self.operador_role, created = Group.objects.get_or_create(name='Operador')
        self.supervisor_role, created = Group.objects.get_or_create(name='Supervisor')
        self.admin_role, created = Group.objects.get_or_create(name='Administrador')
        
        # Crear usuario administrador con permisos
        self.admin_user = Usuario.objects.create(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            tipo_documento='CI',
            numero_documento='11111111',
            is_active=True
        )
        self.admin_user.set_password('password')
        self.admin_user.save()
        
        # Asignar permiso de asignación de roles
        permission = Permission.objects.get(codename='asignacion_roles')
        self.admin_user.user_permissions.add(permission)
        
        # Crear usuario normal
        self.normal_user = Usuario.objects.create(
            username='normal',
            email='normal@example.com',
            first_name='Normal',
            last_name='User',
            tipo_documento='CI',
            numero_documento='22222222',
            is_active=True
        )
        self.normal_user.set_password('password')
        self.normal_user.save()
    
    def test_asigna_roles_con_permiso_usuario_no_administrador(self):
        """Prueba 14: Vista asignar_rol: asigna roles solo si el usuario tiene permiso y no es administrador."""
        # Iniciar sesión como administrador
        self.client.force_login(self.admin_user)
        
        url = reverse('usuarios:asignar_rol', kwargs={'pk': self.normal_user.pk})
        
        # Asignar rol Supervisor
        form_data = {
            'rol': [self.supervisor_role.pk]
        }
        
        response = self.client.post(url, data=form_data)
        
        # Verificar que se asignó el rol
        assert self.normal_user.groups.filter(name='Supervisor').exists()
        
        # Verificar redirección
        assert response.status_code == 302
        assert response.url == reverse('usuarios:administrar_usuarios')
    
    def test_no_permite_asignar_rol_a_administrador(self):
        """Prueba 14: Vista asignar_rol: no permite asignar roles a administradores."""
        # Hacer al usuario normal un administrador
        self.normal_user.groups.add(self.admin_role)
        
        # Crear otro usuario con permiso pero no administrador
        user_with_permission = Usuario.objects.create(
            username='supervisor',
            email='supervisor@example.com',
            first_name='Supervisor',
            last_name='User',
            tipo_documento='CI',
            numero_documento='33333333',
            is_active=True
        )
        user_with_permission.set_password('password')
        user_with_permission.save()
        permission = Permission.objects.get(codename='asignacion_roles')
        user_with_permission.user_permissions.add(permission)
        
        # Iniciar sesión con usuario con permiso (no administrador)
        self.client.force_login(user_with_permission)
        
        url = reverse('usuarios:asignar_rol', kwargs={'pk': self.normal_user.pk})
        
        response = self.client.get(url)
        
        # Verificar que se deniega el acceso
        assert response.status_code == 302


@pytest.mark.django_db
class TestAsignarClientesView:
    """Pruebas para la vista de asignación de clientes."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        self.client = Client()
        
        # Crear roles (usar get_or_create para evitar duplicados)
        self.operador_role, created = Group.objects.get_or_create(name='Operador')
        
        # Crear usuario administrador con permisos
        self.admin_user = Usuario.objects.create(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            tipo_documento='CI',
            numero_documento='11111111',
            is_active=True
        )
        self.admin_user.set_password('password')
        self.admin_user.save()
        
        # Asignar permiso de asignación de clientes
        permission = Permission.objects.get(codename='asignacion_clientes')
        self.admin_user.user_permissions.add(permission)
        
        # Crear usuario operador
        self.operador_user = Usuario.objects.create(
            username='operador',
            email='operador@example.com',
            first_name='Operador',
            last_name='User',
            tipo_documento='CI',
            numero_documento='22222222',
            is_active=True
        )
        self.operador_user.set_password('password')
        self.operador_user.save()
        self.operador_user.groups.add(self.operador_role)
        
        # Crear usuario sin rol operador
        self.normal_user = Usuario.objects.create(
            username='normal',
            email='normal@example.com',
            first_name='Normal',
            last_name='User',
            tipo_documento='CI',
            numero_documento='33333333',
            is_active=True
        )
        self.normal_user.set_password('password')
        self.normal_user.save()
        
        # Crear cliente
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test',
            tipo_documento='CI',
            numero_documento='12345678',
            correo_electronico='cliente@example.com',
            telefono='123456789',
            tipo='F',
            direccion='Dirección test',
            ocupacion='Ocupación test'
        )
    
    def test_asigna_clientes_solo_a_operadores_con_clientes_disponibles(self):
        """Prueba 15: Vista asignar_clientes: asigna clientes solo a operadores y si hay clientes disponibles."""
        # Iniciar sesión como administrador
        self.client.force_login(self.admin_user)
        
        url = reverse('usuarios:asignar_clientes', kwargs={'pk': self.operador_user.pk})
        
        # Asignar cliente
        form_data = {
            'clientes': [self.cliente.pk]
        }
        
        response = self.client.post(url, data=form_data)
        
        # Verificar que se asignó el cliente
        assert self.operador_user.clientes_operados.filter(pk=self.cliente.pk).exists()
        
        # Verificar redirección
        assert response.status_code == 302
        assert response.url == reverse('usuarios:usuario_detalle', kwargs={'pk': self.operador_user.pk})
    
    def test_no_permite_asignar_clientes_a_no_operadores(self):
        """Prueba 15: Vista asignar_clientes: no permite asignar clientes a usuarios sin rol Operador."""
        # Iniciar sesión como administrador
        self.client.force_login(self.admin_user)
        
        url = reverse('usuarios:asignar_clientes', kwargs={'pk': self.normal_user.pk})
        
        response = self.client.get(url)
        
        # Verificar redirección (usuario no es operador)
        assert response.status_code == 302
        assert response.url == reverse('usuarios:administrar_usuarios')
    
    def test_redirige_si_no_hay_clientes_disponibles(self):
        """Prueba 15: Vista asignar_clientes: redirige si no hay clientes creados."""
        # Eliminar el cliente
        self.cliente.delete()
        
        # Iniciar sesión como administrador
        self.client.force_login(self.admin_user)
        
        url = reverse('usuarios:asignar_clientes', kwargs={'pk': self.operador_user.pk})
        
        response = self.client.get(url)
        
        # Verificar redirección (no hay clientes)
        assert response.status_code == 302
        assert response.url == reverse('usuarios:administrar_usuarios')