import pytest
from django.test import TestCase
from django.urls import reverse, resolve
from clientes import views


class TestClienteUrls(TestCase):
    """Pruebas para las URLs de clientes"""
    
    def test_cliente_crear_url(self):
        """Test URL para crear cliente"""
        url = reverse('clientes:cliente_crear')
        self.assertEqual(url, '/clientes/crear/')
        self.assertEqual(resolve(url).func, views.cliente_crear)
    
    def test_cliente_lista_url(self):
        """Test URL para lista de clientes"""
        url = reverse('clientes:cliente_lista')
        self.assertEqual(url, '/clientes/lista/')
        self.assertEqual(resolve(url).func, views.cliente_lista)
    
    def test_cliente_detalle_url(self):
        """Test URL para detalle de cliente"""
        url = reverse('clientes:cliente_detalle', args=[1])
        self.assertEqual(url, '/clientes/1/')
        self.assertEqual(resolve(url).func, views.cliente_detalle)
    
    def test_cliente_editar_url(self):
        """Test URL para editar cliente"""
        url = reverse('clientes:cliente_editar', args=[1])
        self.assertEqual(url, '/clientes/1/editar/')
        self.assertEqual(resolve(url).func, views.cliente_editar)
    
    def test_cliente_eliminar_url(self):
        """Test URL para eliminar cliente"""
        url = reverse('clientes:cliente_eliminar', args=[1])
        self.assertEqual(url, '/clientes/1/eliminar/')
        self.assertEqual(resolve(url).func, views.cliente_eliminar)
    
    def test_app_name(self):
        """Test que el app_name está configurado correctamente"""
        # Verificar que las URLs usan el namespace correcto
        url = reverse('clientes:cliente_lista')
        self.assertTrue(url.startswith('/clientes/'))
    
    def test_url_patterns_count(self):
        """Test que se han definido todas las URLs esperadas"""
        from clientes.urls import urlpatterns
        self.assertEqual(len(urlpatterns), 5)  # Crear, lista, detalle, editar, eliminar
