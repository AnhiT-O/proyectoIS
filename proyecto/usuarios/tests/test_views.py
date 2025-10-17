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
            telefono='099123456',
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
            telefono='099123456',
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
            telefono='099123456',
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
            numero_documento='22222222',
            is_active=True
        )
        self.normal_user.set_password('password')
        self.normal_user.save()
    

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
            numero_documento='22222222',
            is_active=True
        )
        self.normal_user.set_password('password')
        self.normal_user.save()
    