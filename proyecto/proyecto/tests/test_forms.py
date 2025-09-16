import pytest
from django.test import TestCase
from django.forms import ValidationError
from django.contrib.auth import get_user_model
from proyecto.forms import LoginForm

User = get_user_model()


@pytest.mark.django_db
class TestLoginForm:
    """Pruebas unitarias para el formulario LoginForm"""
    
    def test_login_exitoso_con_credenciales_correctas(self):
        """
        Prueba 1: Validar login exitoso con usuario y contraseña correctos
        """
        # Crear usuario de prueba
        user = User(
            username='testuser',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            bloqueado=False,
            is_active=True
        )
        user.set_password('testpassword')
        user.save()
        
        # Crear formulario con credenciales correctas
        form_data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        form = LoginForm(data=form_data)
        
        # Verificar que el formulario es válido
        assert form.is_valid(), f"Formulario debería ser válido, errores: {form.errors}"
        
        # Verificar que el usuario autenticado es el correcto
        user_authenticated = form.get_user()
        assert user_authenticated == user
        assert user_authenticated.username == 'testuser'

    def test_login_rechaza_usuario_bloqueado(self):
        """
        Prueba 2: Rechazar login si el usuario está bloqueado (campo bloqueado=True)
        """
        # Crear usuario bloqueado
        user = User(
            username='blockeduser',
            first_name='Blocked',
            last_name='User',
            email='blocked@example.com',
            tipo_cedula='CI',
            cedula_identidad='87654321',
            bloqueado=True,  # Usuario bloqueado
            is_active=True
        )
        user.set_password('testpassword')
        user.save()
        
        # Intentar login con usuario bloqueado
        form_data = {
            'username': 'blockeduser',
            'password': 'testpassword'
        }
        form = LoginForm(data=form_data)
        
        # Verificar que el formulario no es válido
        assert not form.is_valid()
        
        # Verificar que hay errores no relacionados con campos específicos
        assert form.non_field_errors()

    def test_mensaje_error_personalizado_usuario_bloqueado(self):
        """
        Prueba 3: Mostrar mensaje de error personalizado si el usuario está bloqueado
        """
        # Crear usuario bloqueado
        user = User(
            username='blockeduser2',
            first_name='Blocked',
            last_name='User2',
            email='blocked2@example.com',
            tipo_cedula='CI',
            cedula_identidad='11223344',
            bloqueado=True,
            is_active=True
        )
        user.set_password('testpassword')
        user.save()
        
        # Intentar login
        form_data = {
            'username': 'blockeduser2',
            'password': 'testpassword'
        }
        form = LoginForm(data=form_data)
        
        # Verificar que el formulario no es válido
        assert not form.is_valid()
        
        # Verificar mensaje de error específico para usuario bloqueado
        error_message = "Esta cuenta está bloqueada. Por favor contacta con el administrador."
        assert error_message in str(form.non_field_errors())

    def test_mensaje_error_personalizado_credenciales_incorrectas(self):
        """
        Prueba 4: Mostrar mensaje de error personalizado si usuario/contraseña no coinciden
        """
        # Crear usuario válido
        user = User(
            username='validuser',
            first_name='Valid',
            last_name='User',
            email='valid@example.com',
            tipo_cedula='CI',
            cedula_identidad='55667788',
            bloqueado=False,
            is_active=True
        )
        user.set_password('correctpassword')
        user.save()
        
        # Intentar login con contraseña incorrecta
        form_data = {
            'username': 'validuser',
            'password': 'wrongpassword'
        }
        form = LoginForm(data=form_data)
        
        # Verificar que el formulario no es válido
        assert not form.is_valid()
        
        # Verificar mensaje de error personalizado para credenciales incorrectas
        error_message = "El nombre de usuario y contraseña no coinciden. Inténtelo de nuevo."
        assert error_message in str(form.non_field_errors())