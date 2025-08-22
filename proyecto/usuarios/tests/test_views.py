import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Group
from django.contrib import messages
from django.core import mail
from unittest.mock import patch
from usuarios.models import Usuario
from usuarios.views import login_usuario


class TestUsuarioViews(TestCase):
    """Pruebas para las vistas de usuarios"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.client = Client()
        
        # Crear grupos
        self.admin_group, _ = Group.objects.get_or_create(name='administrador')
        self.operador_group, _ = Group.objects.get_or_create(name='operador')
        
        # Crear usuarios de prueba
        self.admin_user = Usuario.objects.create_user(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='11111111',
            password='testpass123!'
        )
        self.admin_user.groups.add(self.admin_group)
        
        self.regular_user = Usuario.objects.create_user(
            username='regular',
            email='regular@example.com',
            first_name='Regular',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='22222222',
            password='testpass123!'
        )
        
        self.blocked_user = Usuario.objects.create_user(
            username='blocked',
            email='blocked@example.com',
            first_name='Blocked',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='33333333',
            password='testpass123!',
            bloqueado=True
        )
    
    def test_login_get(self):
        """Test GET a la página de login"""
        url = reverse('usuarios:login')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nombre de usuario')
        self.assertContains(response, 'Contraseña')
    
    def test_login_usuario_autenticado_redirige(self):
        """Test que usuario autenticado es redirigido"""
        self.client.login(username='regular', password='testpass123!')
        url = reverse('usuarios:login')
        response = self.client.get(url)
        
        self.assertRedirects(response, reverse('usuarios:perfil'))
    
    def test_login_credenciales_validas(self):
        """Test login con credenciales válidas"""
        url = reverse('usuarios:login')
        data = {
            'username': 'regular',
            'password': 'testpass123!'
        }
        response = self.client.post(url, data)
        
        self.assertRedirects(response, reverse('usuarios:perfil'))
        # Verificar que el usuario está autenticado
        self.assertTrue('_auth_user_id' in self.client.session)
    
    def test_login_credenciales_invalidas(self):
        """Test login con credenciales inválidas"""
        url = reverse('usuarios:login')
        data = {
            'username': 'regular',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 200)
        # El mensaje de error proviene del formulario Django estándar
        self.assertContains(response, 'Por favor, introduce un nombre de usuario y contraseña correctos')
    
    def test_login_usuario_inexistente(self):
        """Test login con usuario inexistente"""
        url = reverse('usuarios:login')
        data = {
            'username': 'noexiste',
            'password': 'testpass123!'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 200)
        # El mensaje de error proviene del formulario Django estándar
        self.assertContains(response, 'Por favor, introduce un nombre de usuario y contraseña correctos')
    
    def test_login_usuario_bloqueado(self):
        """Test login con usuario bloqueado"""
        url = reverse('usuarios:login')
        data = {
            'username': 'blocked',
            'password': 'testpass123!'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tu cuenta está bloqueada')
        self.assertIn('usuario_bloqueado', response.context)
        self.assertTrue(response.context['usuario_bloqueado'])
    
    def test_logout_usuario(self):
        """Test logout de usuario"""
        self.client.login(username='regular', password='testpass123!')
        url = reverse('usuarios:logout')
        response = self.client.get(url)
        
        self.assertRedirects(response, reverse('usuarios:login'))
        # Verificar que el usuario ya no está autenticado
        self.assertFalse('_auth_user_id' in self.client.session)
    
    def test_registro_get(self):
        """Test GET a la página de registro"""
        url = reverse('usuarios:registro')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
    
    def test_registro_post_valido(self):
        """Test POST registro con datos válidos"""
        url = reverse('usuarios:registro')
        data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '44444444',
            'password1': 'newpass123!',
            'password2': 'newpass123!'
        }
        
        with patch('usuarios.views.enviar_email_confirmacion') as mock_email:
            response = self.client.post(url, data)
            
            # Verificar que se creó el usuario
            self.assertTrue(Usuario.objects.filter(username='newuser').exists())
            
            # Verificar que se llamó la función de envío de email
            mock_email.assert_called_once()
            
            # Verificar redirección
            self.assertRedirects(response, reverse('usuarios:registro_exitoso'))
    
    def test_perfil_sin_autenticar(self):
        """Test acceso a perfil sin autenticar"""
        url = reverse('usuarios:perfil')
        response = self.client.get(url)
        
        self.assertRedirects(response, f'/usuarios/login/?next={url}')
    
    def test_perfil_autenticado(self):
        """Test acceso a perfil autenticado"""
        self.client.login(username='regular', password='testpass123!')
        url = reverse('usuarios:perfil')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
    
    def test_administrar_usuarios_sin_permisos(self):
        """Test acceso a administrar usuarios sin permisos"""
        self.client.login(username='regular', password='testpass123!')
        url = reverse('usuarios:administrar_usuarios')
        response = self.client.get(url)
        
        self.assertRedirects(response, reverse('usuarios:perfil'))
    
    def test_administrar_usuarios_con_permisos(self):
        """Test acceso a administrar usuarios con permisos de admin"""
        self.client.login(username='admin', password='testpass123!')
        url = reverse('usuarios:administrar_usuarios')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('usuarios', response.context)
        # Verificar que no incluye al usuario actual
        self.assertNotIn(self.admin_user, response.context['usuarios'])
    
    def test_administrar_usuarios_con_busqueda(self):
        """Test buscar usuarios en página de administración"""
        self.client.login(username='admin', password='testpass123!')
        url = reverse('usuarios:administrar_usuarios') + '?busqueda=regular'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'regular')
    
    def test_bloquear_usuario_admin(self):
        """Test bloquear usuario como administrador"""
        self.client.login(username='admin', password='testpass123!')
        url = reverse('usuarios:bloquear_usuario', args=[self.regular_user.pk])
        response = self.client.post(url)
        
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.bloqueado)
        self.assertRedirects(response, reverse('usuarios:administrar_usuarios'))
    
    def test_bloquear_usuario_sin_permisos(self):
        """Test bloquear usuario sin permisos"""
        self.client.login(username='regular', password='testpass123!')
        url = reverse('usuarios:bloquear_usuario', args=[self.blocked_user.pk])
        response = self.client.post(url)
        
        self.assertRedirects(response, reverse('usuarios:perfil'))
    
    def test_no_bloquear_administrador(self):
        """Test que no se puede bloquear a otro administrador"""
        admin2 = Usuario.objects.create_user(
            username='admin2',
            email='admin2@example.com',
            first_name='Admin2',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='55555555',
            password='testpass123!'
        )
        admin2.groups.add(self.admin_group)
        
        self.client.login(username='admin', password='testpass123!')
        url = reverse('usuarios:bloquear_usuario', args=[admin2.pk])
        response = self.client.post(url)
        
        admin2.refresh_from_db()
        self.assertFalse(admin2.bloqueado)
        self.assertRedirects(response, reverse('usuarios:administrar_usuarios'))
    
    def test_eliminar_usuario_admin(self):
        """Test eliminar usuario como administrador"""
        self.client.login(username='admin', password='testpass123!')
        url = reverse('usuarios:eliminar_usuario', args=[self.regular_user.pk])
        response = self.client.post(url)
        
        self.assertFalse(Usuario.objects.filter(pk=self.regular_user.pk).exists())
        self.assertRedirects(response, reverse('usuarios:administrar_usuarios'))
    
    def test_no_eliminar_administrador(self):
        """Test que no se puede eliminar a otro administrador"""
        admin2 = Usuario.objects.create_user(
            username='admin2',
            email='admin2@example.com',
            first_name='Admin2',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='55555555',
            password='testpass123!'
        )
        admin2.groups.add(self.admin_group)
        
        self.client.login(username='admin', password='testpass123!')
        url = reverse('usuarios:eliminar_usuario', args=[admin2.pk])
        response = self.client.post(url)
        
        self.assertTrue(Usuario.objects.filter(pk=admin2.pk).exists())
        self.assertRedirects(response, reverse('usuarios:administrar_usuarios'))
    
    def test_recuperar_password_get(self):
        """Test GET página recuperar contraseña"""
        url = reverse('usuarios:recuperar_password')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
    
    def test_recuperar_password_post_valido(self):
        """Test POST recuperar contraseña con email válido"""
        url = reverse('usuarios:recuperar_password')
        data = {'email': 'regular@example.com'}
        
        with patch('usuarios.views.enviar_email_recuperacion') as mock_email:
            response = self.client.post(url, data)
            
            mock_email.assert_called_once()
            self.assertRedirects(response, reverse('usuarios:login'))
    
    def test_registro_exitoso_view(self):
        """Test vista de registro exitoso"""
        url = reverse('usuarios:registro_exitoso')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
