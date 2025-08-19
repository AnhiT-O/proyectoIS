import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core import mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from unittest.mock import patch, MagicMock
from usuarios.models import Usuario
from usuarios.forms import RegistroUsuarioForm

@pytest.mark.django_db
class TestRegistroUsuarioView:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.client = Client()
        self.url = reverse('usuarios:registro')
        self.valid_data = {
            'username': 'juan_perez',
            'cedula_identidad': '12345678',
            'tipo_cedula': 'CI',
            'email': 'test@example.com',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'password1': 'contraseña123!',
            'password2': 'contraseña123!'
        }

    def test_registro_usuario_get_muestra_formulario(self):
        """Prueba que GET muestre el formulario de registro"""
        response = self.client.get(self.url)
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert isinstance(response.context['form'], RegistroUsuarioForm)

    @patch('usuarios.views.enviar_email_confirmacion')
    def test_registro_usuario_post_exitoso(self, mock_enviar_email):
        """Prueba registro exitoso de nuevo usuario"""
        response = self.client.post(self.url, self.valid_data)
        
        # Verificar redirección
        assert response.status_code == 302
        assert response.url == reverse('usuarios:registro_exitoso')
        
        # Verificar que se creó el usuario
        user = Usuario.objects.get(email=self.valid_data['email'])
        assert user.cedula_identidad == self.valid_data['cedula_identidad']
        assert not user.is_active  # Usuario inactivo hasta confirmación
        
        # Verificar que se envió email de confirmación
        mock_enviar_email.assert_called_once()

    @patch('usuarios.views.enviar_email_confirmacion')
    def test_registro_usuario_existente_inactivo_reenvia_email(self, mock_enviar_email):
        """Prueba que se reenvíe email a usuario existente inactivo"""
        # Crear usuario inactivo existente
        existing_user = Usuario.objects.create_user(
            username='existing_user',
            cedula_identidad=self.valid_data['cedula_identidad'],
            tipo_cedula=self.valid_data['tipo_cedula'],
            email=self.valid_data['email'],
            first_name='Juan',
            last_name='Pérez',
            password='password123',
            is_active=False
        )
        
        response = self.client.post(self.url, self.valid_data)
        
        # Verificar redirección
        assert response.status_code == 302
        assert response.url == reverse('usuarios:registro_exitoso')
        
        # Verificar que se reenvió email al usuario existente
        mock_enviar_email.assert_called_once_with(response.wsgi_request, existing_user)
        
        # Verificar mensaje informativo
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert 'Ya tienes una cuenta pendiente' in str(messages[0])

    def test_registro_usuario_formulario_invalido(self):
        """Prueba manejo de formulario inválido"""
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'email_invalido'
        
        response = self.client.post(self.url, invalid_data)
        
        # Verificar que no redirige
        assert response.status_code == 200
        
        # Verificar que se muestra el formulario con errores
        assert 'form' in response.context
        assert response.context['form'].errors
        
        # Verificar que no se creó usuario
        assert not Usuario.objects.filter(email=invalid_data['email']).exists()

@pytest.mark.django_db
class TestEnviarEmailConfirmacion:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.client = Client()
        self.user = Usuario.objects.create_user(
            username='testuser1',
            cedula_identidad='12345678',
            tipo_cedula='CI',
            email='test@example.com',
            first_name='Juan',
            last_name='Pérez',
            password='password123',
            is_active=False
        )

    @patch('usuarios.views.EmailMultiAlternatives')
    def test_enviar_email_confirmacion_exitoso(self, mock_email_class):
        """Prueba que se envíe email de confirmación correctamente"""
        from usuarios.views import enviar_email_confirmacion
        
        # Crear un mock del objeto EmailMultiAlternatives
        mock_email_instance = MagicMock()
        mock_email_class.return_value = mock_email_instance
        
        request = MagicMock()
        request.build_absolute_uri.return_value = 'http://example.com/activate/123/token'
        
        enviar_email_confirmacion(request, self.user)
        
        # Verificar que se creó el objeto EmailMultiAlternatives
        mock_email_class.assert_called_once()
        args, kwargs = mock_email_class.call_args
        
        # Verificar argumentos del email
        assert kwargs['subject'] == 'Confirma tu cuenta'
        assert self.user.email in kwargs['to']
        
        # Verificar que se adjuntó la versión HTML
        mock_email_instance.attach_alternative.assert_called_once()
        
        # Verificar que se envió el email
        mock_email_instance.send.assert_called_once()

@pytest.mark.django_db
class TestActivarCuentaView:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.client = Client()
        self.user = Usuario.objects.create_user(
            username='testuser2',
            cedula_identidad='12345678',
            tipo_cedula='CI',
            email='test@example.com',
            first_name='Juan',
            last_name='Pérez',
            password='password123',
            is_active=False
        )
        self.token = default_token_generator.make_token(self.user)
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))

    def test_activar_cuenta_exitoso(self):
        """Prueba activación exitosa de cuenta"""
        url = reverse('usuarios:activar_cuenta', kwargs={
            'uidb64': self.uid,
            'token': self.token
        })
        
        response = self.client.get(url)
        
        # Verificar redirección al perfil
        assert response.status_code == 302
        assert response.url == reverse('usuarios:perfil')
        
        # Verificar que el usuario se activó
        self.user.refresh_from_db()
        assert self.user.is_active
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert '¡Cuenta activada exitosamente!' in str(messages[0])

    def test_activar_cuenta_token_invalido(self):
        """Prueba activación con token inválido"""
        url = reverse('usuarios:activar_cuenta', kwargs={
            'uidb64': self.uid,
            'token': 'token_invalido'
        })
        
        response = self.client.get(url)
        
        # Verificar redirección al registro
        assert response.status_code == 302
        assert response.url == reverse('usuarios:registro')
        
        # Verificar que el usuario NO se activó
        self.user.refresh_from_db()
        assert not self.user.is_active
        
        # Verificar mensaje de error
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert 'inválido o ha expirado' in str(messages[0])

    def test_activar_cuenta_uid_invalido(self):
        """Prueba activación con UID inválido"""
        url = reverse('usuarios:activar_cuenta', kwargs={
            'uidb64': 'uid_invalido',
            'token': self.token
        })
        
        response = self.client.get(url)
        
        # Verificar redirección al registro
        assert response.status_code == 302
        assert response.url == reverse('usuarios:registro')
        
        # Verificar mensaje de error
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert 'inválido o ha expirado' in str(messages[0])

    def test_activar_cuenta_usuario_inexistente(self):
        """Prueba activación con usuario inexistente"""
        fake_uid = urlsafe_base64_encode(force_bytes(99999))
        url = reverse('usuarios:activar_cuenta', kwargs={
            'uidb64': fake_uid,
            'token': self.token
        })
        
        response = self.client.get(url)
        
        # Verificar redirección al registro
        assert response.status_code == 302
        assert response.url == reverse('usuarios:registro')
        
        # Verificar mensaje de error
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert 'inválido o ha expirado' in str(messages[0])

@pytest.mark.django_db
class TestRegistroExitosoView:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.client = Client()
        self.url = reverse('usuarios:registro_exitoso')

    def test_registro_exitoso_muestra_template_correcto(self):
        """Prueba que la vista muestre el template correcto"""
        response = self.client.get(self.url)
        
        assert response.status_code == 200
        assert 'usuarios/registro_exitoso.html' in [t.name for t in response.templates]

@pytest.mark.django_db
class TestPerfilView:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.client = Client()
        self.url = reverse('usuarios:perfil')

    def test_perfil_muestra_template_correcto(self):
        """Prueba que la vista muestre el template correcto"""
        response = self.client.get(self.url)
        
        assert response.status_code == 200
        assert 'usuarios/perfil.html' in [t.name for t in response.templates]

@pytest.mark.django_db
class TestIntegracionCompleta:
    """Pruebas de integración del flujo completo de registro y activación"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.client = Client()
        self.valid_data = {
            'username': 'juan_perez',
            'cedula_identidad': '12345678',
            'tipo_cedula': 'CI',
            'email': 'test@example.com',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'password1': 'contraseña123!',
            'password2': 'contraseña123!'
        }

    @patch('usuarios.views.EmailMultiAlternatives')
    def test_flujo_completo_registro_y_activacion(self, mock_email_class):
        """Prueba el flujo completo desde registro hasta activación"""
        # Crear un mock del objeto EmailMultiAlternatives
        mock_email_instance = MagicMock()
        mock_email_class.return_value = mock_email_instance
        
        # Paso 1: Registro
        registro_url = reverse('usuarios:registro')
        response = self.client.post(registro_url, self.valid_data)
        
        assert response.status_code == 302
        
        # Verificar que se creó el usuario inactivo
        user = Usuario.objects.get(email=self.valid_data['email'])
        assert not user.is_active
        
        # Paso 2: Simular activación
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        activacion_url = reverse('usuarios:activar_cuenta', kwargs={
            'uidb64': uid,
            'token': token
        })
        
        response = self.client.get(activacion_url)
        
        # Verificar activación exitosa
        assert response.status_code == 302
        assert response.url == reverse('usuarios:perfil')
        
        # Verificar que el usuario está activo y logueado
        user.refresh_from_db()
        assert user.is_active
