import pytest
from django.test import TestCase
from django.urls import reverse, resolve
from usuarios import views


class TestUsuarioUrls(TestCase):
    """Pruebas para las URLs de usuarios"""
    
    def test_login_url(self):
        """Test URL de login"""
        url = reverse('usuarios:login')
        self.assertEqual(url, '/usuarios/login/')
        self.assertEqual(resolve(url).func, views.login_usuario)
    
    def test_logout_url(self):
        """Test URL de logout"""
        url = reverse('usuarios:logout')
        self.assertEqual(url, '/usuarios/logout/')
        self.assertEqual(resolve(url).func, views.logout_usuario)
    
    def test_registro_url(self):
        """Test URL de registro"""
        url = reverse('usuarios:registro')
        self.assertEqual(url, '/usuarios/registro/')
        self.assertEqual(resolve(url).func, views.registro_usuario)
    
    def test_registro_exitoso_url(self):
        """Test URL de registro exitoso"""
        url = reverse('usuarios:registro_exitoso')
        self.assertEqual(url, '/usuarios/registro-exitoso/')
        self.assertEqual(resolve(url).func, views.registro_exitoso)
    
    def test_activar_cuenta_url(self):
        """Test URL de activación de cuenta"""
        url = reverse('usuarios:activar_cuenta', args=['uid123', 'token456'])
        self.assertEqual(url, '/usuarios/activar/uid123/token456/')
        self.assertEqual(resolve(url).func, views.activar_cuenta)
    
    def test_perfil_url(self):
        """Test URL de perfil"""
        url = reverse('usuarios:perfil')
        self.assertEqual(url, '/usuarios/perfil/')
        self.assertEqual(resolve(url).func, views.perfil)
    
    def test_recuperar_password_url(self):
        """Test URL de recuperar contraseña"""
        url = reverse('usuarios:recuperar_password')
        self.assertEqual(url, '/usuarios/recuperar-password/')
        self.assertEqual(resolve(url).func, views.recuperar_password)
    
    def test_reset_password_confirm_url(self):
        """Test URL de confirmación de reset de contraseña"""
        url = reverse('usuarios:reset_password_confirm', args=['uid123', 'token456'])
        self.assertEqual(url, '/usuarios/reset-password/uid123/token456/')
        self.assertEqual(resolve(url).func, views.reset_password_confirm)
    
    def test_administrar_usuarios_url(self):
        """Test URL de administrar usuarios"""
        url = reverse('usuarios:administrar_usuarios')
        self.assertEqual(url, '/usuarios/administrar/')
        self.assertEqual(resolve(url).func, views.administrar_usuarios)
    
    def test_bloquear_usuario_url(self):
        """Test URL de bloquear usuario"""
        url = reverse('usuarios:bloquear_usuario', args=[1])
        self.assertEqual(url, '/usuarios/usuario/1/bloquear/')
        self.assertEqual(resolve(url).func, views.bloquear_usuario)
    
    def test_eliminar_usuario_url(self):
        """Test URL de eliminar usuario"""
        url = reverse('usuarios:eliminar_usuario', args=[1])
        self.assertEqual(url, '/usuarios/usuario/1/eliminar/')
        self.assertEqual(resolve(url).func, views.eliminar_usuario)
    
    def test_app_name(self):
        """Test que el app_name está configurado correctamente"""
        # Verificar que las URLs usan el namespace correcto
        url = reverse('usuarios:login')
        self.assertTrue(url.startswith('/usuarios/'))
    
    def test_url_patterns_count(self):
        """Test que se han definido todas las URLs esperadas"""
        from usuarios.urls import urlpatterns
        self.assertEqual(len(urlpatterns), 11)  # Total de URLs definidas
