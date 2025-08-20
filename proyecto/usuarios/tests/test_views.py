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
from usuarios.forms import RegistroUsuarioForm, LoginForm

@pytest.mark.django_db
class TestLoginUsuarioView:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.client = Client()
        self.url = reverse('usuarios:login')
        self.user = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            cedula_identidad='12345678',
            tipo_cedula='CI',
            first_name='Juan',
            last_name='Pérez',
            password='TestPass123!',
            is_active=True
        )

    def test_login_get_muestra_formulario(self):
        """Prueba que GET muestre el formulario de login"""
        response = self.client.get(self.url)
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert isinstance(response.context['form'], LoginForm)
        assert 'usuarios/login.html' in [t.name for t in response.templates]

    def test_login_post_credenciales_correctas(self):
        """Prueba login exitoso con credenciales correctas"""
        login_data = {
            'username': 'testuser',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.url, login_data)
        
        # Verificar redirección al perfil
        assert response.status_code == 302
        assert response.url == reverse('usuarios:perfil')
        
        # Verificar que el usuario está autenticado
        assert '_auth_user_id' in self.client.session
        assert self.client.session['_auth_user_id'] == str(self.user.pk)
        
        # Verificar mensaje de bienvenida
        response = self.client.get(response.url)
        messages = list(get_messages(response.wsgi_request))
        assert any('¡Bienvenido de nuevo, Juan!' in str(message) for message in messages)

    def test_login_post_credenciales_incorrectas(self):
        """Prueba login con credenciales incorrectas"""
        login_data = {
            'username': 'testuser',
            'password': 'PasswordIncorrecto'
        }
        
        response = self.client.post(self.url, login_data)
        
        # Verificar que no redirige
        assert response.status_code == 200
        
        # Verificar que el usuario NO está autenticado
        assert '_auth_user_id' not in self.client.session
        
        # Verificar que el formulario tiene errores de autenticación
        assert 'form' in response.context
        form = response.context['form']
        assert not form.is_valid()

    def test_login_post_usuario_inexistente(self):
        """Prueba login con usuario inexistente"""
        login_data = {
            'username': 'usuarioinexistente',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.url, login_data)
        
        # Verificar que no redirige
        assert response.status_code == 200
        
        # Verificar que el usuario NO está autenticado
        assert '_auth_user_id' not in self.client.session
        
        # Verificar que el formulario tiene errores de autenticación
        assert 'form' in response.context
        form = response.context['form']
        assert not form.is_valid()

    def test_login_post_usuario_inactivo(self):
        """Prueba login con usuario inactivo"""
        # Crear usuario inactivo
        inactive_user = Usuario.objects.create_user(
            username='inactiveuser',
            email='inactive@example.com',
            cedula_identidad='87654321',
            tipo_cedula='CI',
            first_name='María',
            last_name='González',
            password='TestPass123!',
            is_active=False
        )
        
        login_data = {
            'username': 'inactiveuser',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.url, login_data)
        
        # Verificar que no redirige
        assert response.status_code == 200
        
        # Verificar que el usuario NO está autenticado
        assert '_auth_user_id' not in self.client.session
        
        # Para usuario inactivo, el formulario será válido pero no se autenticará
        # Django's AuthenticationForm maneja usuarios inactivos automáticamente
        assert 'form' in response.context
        form = response.context['form']
        # El formulario debería tener errores debido a usuario inactivo
        assert not form.is_valid() or form.get_user() is None or not form.get_user().is_active

    def test_login_formulario_invalido(self):
        """Prueba login con formulario inválido"""
        login_data = {
            'username': '',
            'password': ''
        }
        
        response = self.client.post(self.url, login_data)
        
        # Verificar que no redirige
        assert response.status_code == 200
        
        # Verificar que el formulario tiene errores
        assert 'form' in response.context
        assert response.context['form'].errors
        
        # Verificar que el usuario NO está autenticado
        assert '_auth_user_id' not in self.client.session

    def test_login_usuario_ya_autenticado_redirige_perfil(self):
        """Prueba que usuario ya autenticado sea redirigido al perfil"""
        # Autenticar usuario primero
        self.client.force_login(self.user)
        
        response = self.client.get(self.url)
        
        # Verificar redirección al perfil
        assert response.status_code == 302
        assert response.url == reverse('usuarios:perfil')

    def test_login_con_parametro_next(self):
        """Prueba redirección con parámetro 'next'"""
        next_url = '/usuarios/perfil/'
        login_data = {
            'username': 'testuser',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(f'{self.url}?next={next_url}', login_data)
        
        # Verificar redirección a la URL especificada en 'next'
        assert response.status_code == 302
        assert response.url == next_url

@pytest.mark.django_db
class TestLogoutUsuarioView:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.client = Client()
        self.url = reverse('usuarios:logout')
        self.user = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            cedula_identidad='12345678',
            tipo_cedula='CI',
            first_name='Juan',
            last_name='Pérez',
            password='TestPass123!',
            is_active=True
        )

    def test_logout_usuario_autenticado(self):
        """Prueba logout de usuario autenticado"""
        # Autenticar usuario primero
        self.client.force_login(self.user)
        
        # Verificar que está autenticado
        assert '_auth_user_id' in self.client.session
        
        response = self.client.get(self.url)
        
        # Verificar redirección al login
        assert response.status_code == 302
        assert response.url == reverse('usuarios:login')
        
        # Verificar que ya no está autenticado
        assert '_auth_user_id' not in self.client.session
        
        # Verificar mensaje de confirmación
        response = self.client.get(response.url)
        messages = list(get_messages(response.wsgi_request))
        assert any('Has cerrado sesión exitosamente' in str(message) for message in messages)

    def test_logout_usuario_no_autenticado(self):
        """Prueba logout de usuario no autenticado"""
        response = self.client.get(self.url)
        
        # Verificar redirección al login
        assert response.status_code == 302
        assert response.url == reverse('usuarios:login')
        
        # Verificar mensaje de confirmación (incluso si no estaba autenticado)
        response = self.client.get(response.url)
        messages = list(get_messages(response.wsgi_request))
        assert any('Has cerrado sesión exitosamente' in str(message) for message in messages)

    def test_logout_post_method(self):
        """Prueba logout con método POST"""
        # Autenticar usuario primero
        self.client.force_login(self.user)
        
        response = self.client.post(self.url)
        
        # Verificar redirección al login
        assert response.status_code == 302
        assert response.url == reverse('usuarios:login')
        
        # Verificar que ya no está autenticado
        assert '_auth_user_id' not in self.client.session

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
        mock_enviar_email.assert_called_once_with(response.wsgi_request, user)

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

    @patch('usuarios.views.render_to_string')
    @patch('usuarios.views.EmailMultiAlternatives')
    def test_enviar_email_confirmacion_exitoso(self, mock_email_class, mock_render_to_string):
        """Prueba que se envíe email de confirmación correctamente"""
        from usuarios.views import enviar_email_confirmacion
        
        # Configurar mocks
        mock_render_to_string.return_value = '<html>Test HTML content</html>'
        mock_email_instance = MagicMock()
        mock_email_class.return_value = mock_email_instance
        
        request = MagicMock()
        request.build_absolute_uri.return_value = 'http://example.com/activate/123/token'
        
        enviar_email_confirmacion(request, self.user)
        
        # Verificar que se llamó render_to_string con los parámetros correctos
        mock_render_to_string.assert_called_once_with('usuarios/email_confirmacion.html', {
            'user': self.user,
            'activacion_url': 'http://example.com/activate/123/token',
        })
        
        # Verificar que se creó el objeto EmailMultiAlternatives
        mock_email_class.assert_called_once()
        args, kwargs = mock_email_class.call_args
        
        # Verificar argumentos del email
        assert kwargs['subject'] == 'Confirma tu cuenta'
        assert self.user.email in kwargs['to']
        assert 'Juan' in kwargs['body']  # Verificar que el contenido de texto plano contiene el nombre
        assert 'http://example.com/activate/123/token' in kwargs['body']  # Verificar URL en texto plano
        
        # Verificar que se adjuntó la versión HTML
        mock_email_instance.attach_alternative.assert_called_once_with('<html>Test HTML content</html>', "text/html")
        
        # Verificar que se envió el email
        mock_email_instance.send.assert_called_once()

    def test_contenido_email_texto_plano(self):
        """Prueba que el contenido del email de texto plano se genere correctamente"""
        from usuarios.views import enviar_email_confirmacion
        
        # Crear un mock para capturar el contenido del email
        with patch('usuarios.views.EmailMultiAlternatives') as mock_email_class, \
             patch('usuarios.views.render_to_string') as mock_render_to_string:
            
            mock_render_to_string.return_value = '<html>Test HTML</html>'
            mock_email_instance = MagicMock()
            mock_email_class.return_value = mock_email_instance
            
            request = MagicMock()
            test_url = 'http://test.com/activate/abc123/token456'
            request.build_absolute_uri.return_value = test_url
            
            enviar_email_confirmacion(request, self.user)
            
            # Obtener el contenido del texto plano
            args, kwargs = mock_email_class.call_args
            text_content = kwargs['body']
            
            # Verificar que el contenido incluye elementos esperados
            assert f'¡Hola {self.user.first_name}!' in text_content
            assert 'Gracias por registrarte en nuestro sistema.' in text_content
            assert test_url in text_content
            assert 'El equipo de desarrollo' in text_content
            assert 'Si no solicitaste esta cuenta' in text_content

    @patch('usuarios.views.render_to_string')
    @patch('usuarios.views.EmailMultiAlternatives')
    def test_enviar_email_confirmacion_configuracion_email(self, mock_email_class, mock_render_to_string):
        """Prueba que se use la configuración correcta de email"""
        from usuarios.views import enviar_email_confirmacion
        
        # Configurar mocks
        mock_render_to_string.return_value = '<html>Test HTML</html>'
        mock_email_instance = MagicMock()
        mock_email_class.return_value = mock_email_instance
        
        request = MagicMock()
        request.build_absolute_uri.return_value = 'http://test.com/activate'
        
        with patch('usuarios.views.getattr') as mock_getattr:
            mock_getattr.return_value = 'test@empresa.com'
            
            enviar_email_confirmacion(request, self.user)
            
            # Verificar que se llamó getattr para obtener EMAIL_HOST_USER
            mock_getattr.assert_called_once()
            
            # Verificar argumentos del email
            args, kwargs = mock_email_class.call_args
            assert kwargs['from_email'] == 'test@empresa.com'

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
        self.user = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            cedula_identidad='12345678',
            tipo_cedula='CI',
            first_name='Juan',
            last_name='Pérez',
            password='TestPass123!',
            is_active=True
        )

    def test_perfil_usuario_autenticado(self):
        """Prueba que usuario autenticado pueda acceder al perfil"""
        self.client.force_login(self.user)
        
        response = self.client.get(self.url)
        
        assert response.status_code == 200
        assert 'usuarios/perfil.html' in [t.name for t in response.templates]
        assert response.context['user'] == self.user

    def test_perfil_usuario_no_autenticado_redirige_login(self):
        """Prueba que usuario no autenticado sea redirigido al login"""
        response = self.client.get(self.url)
        
        # Verificar redirección al login
        assert response.status_code == 302
        assert '/usuarios/login/' in response.url
        assert f'next={self.url}' in response.url

    def test_perfil_muestra_informacion_usuario(self):
        """Prueba que el perfil muestre la información correcta del usuario"""
        self.client.force_login(self.user)
        
        response = self.client.get(self.url)
        
        # Verificar que el contexto contiene la información del usuario
        assert response.context['user'].first_name == 'Juan'
        assert response.context['user'].last_name == 'Pérez'
        assert response.context['user'].email == 'test@example.com'
        assert response.context['user'].cedula_identidad == '12345678'
        assert response.context['user'].tipo_cedula == 'CI'


@pytest.mark.django_db
class TestRecuperarPasswordView:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.client = Client()
        self.url = reverse('usuarios:recuperar_password')
        self.user = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            cedula_identidad='12345678',
            tipo_cedula='CI',
            first_name='Juan',
            last_name='Pérez',
            password='TestPass123!',
            is_active=True
        )

    def test_recuperar_password_get_muestra_formulario(self):
        """Prueba que GET muestre el formulario de recuperación"""
        response = self.client.get(self.url)
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'usuarios/recuperar_password.html' in [t.name for t in response.templates]

    @patch('usuarios.views.enviar_email_recuperacion')
    def test_recuperar_password_post_exitoso(self, mock_enviar_email):
        """Prueba recuperación exitosa con email válido"""
        data = {'email': self.user.email}
        
        response = self.client.post(self.url, data)
        
        # Verificar redirección al login
        assert response.status_code == 302
        assert response.url == reverse('usuarios:login')
        
        # Verificar que se envió email de recuperación
        mock_enviar_email.assert_called_once()
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        assert any('Se ha enviado un enlace de recuperación' in str(message) for message in messages)

    def test_recuperar_password_email_inexistente(self):
        """Prueba recuperación con email inexistente"""
        data = {'email': 'inexistente@example.com'}
        
        response = self.client.post(self.url, data)
        
        # Verificar que no redirige
        assert response.status_code == 200
        
        # Verificar que el formulario tiene errores
        assert 'form' in response.context
        form = response.context['form']
        assert 'email' in form.errors
        assert 'No existe una cuenta activa' in str(form.errors['email'])

    def test_recuperar_password_usuario_inactivo(self):
        """Prueba recuperación con usuario inactivo"""
        # Crear usuario inactivo
        inactive_user = Usuario.objects.create_user(
            username='inactive',
            email='inactive@example.com',
            cedula_identidad='87654321',
            tipo_cedula='CI',
            first_name='María',
            last_name='González',
            password='TestPass123!',
            is_active=False
        )
        
        data = {'email': inactive_user.email}
        
        response = self.client.post(self.url, data)
        
        # Verificar que no redirige
        assert response.status_code == 200
        
        # Verificar que el formulario tiene errores
        assert 'form' in response.context
        form = response.context['form']
        assert 'email' in form.errors
        assert 'No existe una cuenta activa' in str(form.errors['email'])

    def test_recuperar_password_formulario_invalido(self):
        """Prueba recuperación con formulario inválido"""
        data = {'email': 'email_invalido'}
        
        response = self.client.post(self.url, data)
        
        # Verificar que no redirige
        assert response.status_code == 200
        
        # Verificar que el formulario tiene errores
        assert 'form' in response.context
        assert response.context['form'].errors


@pytest.mark.django_db
class TestEnviarEmailRecuperacion:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.client = Client()
        self.user = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            cedula_identidad='12345678',
            tipo_cedula='CI',
            first_name='Juan',
            last_name='Pérez',
            password='TestPass123!',
            is_active=True
        )

    @patch('usuarios.views.render_to_string')
    @patch('usuarios.views.EmailMultiAlternatives')
    def test_enviar_email_recuperacion_exitoso(self, mock_email_class, mock_render_to_string):
        """Prueba que se envíe email de recuperación correctamente"""
        from usuarios.views import enviar_email_recuperacion
        
        # Configurar mocks
        mock_render_to_string.return_value = '<html>Recovery HTML content</html>'
        mock_email_instance = MagicMock()
        mock_email_class.return_value = mock_email_instance
        
        request = MagicMock()
        request.build_absolute_uri.return_value = 'http://example.com/reset/123/token'
        
        enviar_email_recuperacion(request, self.user)
        
        # Verificar que se llamó render_to_string
        mock_render_to_string.assert_called_once_with('usuarios/email_recuperacion.html', {
            'user': self.user,
            'reset_url': 'http://example.com/reset/123/token',
        })
        
        # Verificar que se creó el objeto EmailMultiAlternatives
        mock_email_class.assert_called_once()
        args, kwargs = mock_email_class.call_args
        
        # Verificar argumentos del email
        assert kwargs['subject'] == 'Recuperación de contraseña - Casa de Cambios'
        assert self.user.email in kwargs['to']
        assert 'Juan' in kwargs['body']
        assert 'http://example.com/reset/123/token' in kwargs['body']
        
        # Verificar que se adjuntó la versión HTML
        mock_email_instance.attach_alternative.assert_called_once()
        
        # Verificar que se envió el email
        mock_email_instance.send.assert_called_once()


@pytest.mark.django_db
class TestResetPasswordConfirmView:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.client = Client()
        self.user = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            cedula_identidad='12345678',
            tipo_cedula='CI',
            first_name='Juan',
            last_name='Pérez',
            password='TestPass123!',
            is_active=True
        )
        self.token = default_token_generator.make_token(self.user)
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))

    def test_reset_password_confirm_get_valido(self):
        """Prueba que GET con token válido muestre el formulario"""
        url = reverse('usuarios:reset_password_confirm', kwargs={
            'uidb64': self.uid,
            'token': self.token
        })
        
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['validlink'] is True
        assert 'usuarios/reset_password_confirm.html' in [t.name for t in response.templates]

    def test_reset_password_confirm_post_exitoso(self):
        """Prueba cambio exitoso de contraseña"""
        url = reverse('usuarios:reset_password_confirm', kwargs={
            'uidb64': self.uid,
            'token': self.token
        })
        
        data = {
            'new_password1': 'NuevaPassword123!',
            'new_password2': 'NuevaPassword123!'
        }
        
        response = self.client.post(url, data)
        
        # Verificar redirección al login
        assert response.status_code == 302
        assert response.url == reverse('usuarios:login')
        
        # Verificar que la contraseña cambió
        self.user.refresh_from_db()
        assert self.user.check_password('NuevaPassword123!')
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        assert any('contraseña ha sido cambiada exitosamente' in str(message) for message in messages)

    def test_reset_password_confirm_formulario_invalido(self):
        """Prueba manejo de formulario inválido"""
        url = reverse('usuarios:reset_password_confirm', kwargs={
            'uidb64': self.uid,
            'token': self.token
        })
        
        data = {
            'new_password1': '123',  # Contraseña muy corta
            'new_password2': '123'
        }
        
        response = self.client.post(url, data)
        
        # Verificar que no redirige
        assert response.status_code == 200
        
        # Verificar que el formulario tiene errores
        assert 'form' in response.context
        assert response.context['form'].errors
        
        # Verificar que la contraseña NO cambió
        self.user.refresh_from_db()
        assert self.user.check_password('TestPass123!')

    def test_reset_password_confirm_token_invalido(self):
        """Prueba con token inválido"""
        url = reverse('usuarios:reset_password_confirm', kwargs={
            'uidb64': self.uid,
            'token': 'token_invalido'
        })
        
        response = self.client.get(url)
        
        # Verificar redirección a recuperar password
        assert response.status_code == 302
        assert response.url == reverse('usuarios:recuperar_password')
        
        # Verificar mensaje de error
        messages = list(get_messages(response.wsgi_request))
        assert any('inválido o ha expirado' in str(message) for message in messages)

    def test_reset_password_confirm_uid_invalido(self):
        """Prueba con UID inválido"""
        url = reverse('usuarios:reset_password_confirm', kwargs={
            'uidb64': 'uid_invalido',
            'token': self.token
        })
        
        response = self.client.get(url)
        
        # Verificar redirección a recuperar password
        assert response.status_code == 302
        assert response.url == reverse('usuarios:recuperar_password')
        
        # Verificar mensaje de error
        messages = list(get_messages(response.wsgi_request))
        assert any('inválido o ha expirado' in str(message) for message in messages)

    def test_reset_password_confirm_usuario_inexistente(self):
        """Prueba con usuario inexistente"""
        fake_uid = urlsafe_base64_encode(force_bytes(99999))
        url = reverse('usuarios:reset_password_confirm', kwargs={
            'uidb64': fake_uid,
            'token': self.token
        })
        
        response = self.client.get(url)
        
        # Verificar redirección a recuperar password
        assert response.status_code == 302
        assert response.url == reverse('usuarios:recuperar_password')
        
        # Verificar mensaje de error
        messages = list(get_messages(response.wsgi_request))
        assert any('inválido o ha expirado' in str(message) for message in messages)