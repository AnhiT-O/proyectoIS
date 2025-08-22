import pytest
from django.test import TestCase
from django.urls import reverse, resolve
from roles import views


class TestRolesUrls(TestCase):
    """Pruebas para las URLs de roles"""
    
    def test_listar_roles_url(self):
        """Test URL para listar roles"""
        url = reverse('listar_roles')
        self.assertEqual(url, '/roles/')
        self.assertEqual(resolve(url).func, views.listar_roles)
    
    def test_crear_rol_url(self):
        """Test URL para crear rol"""
        url = reverse('crear_rol')
        self.assertEqual(url, '/roles/crear/')
        self.assertEqual(resolve(url).func, views.crear_rol)
    
    def test_editar_rol_url(self):
        """Test URL para editar rol"""
        url = reverse('editar_rol', args=[1])
        self.assertEqual(url, '/roles/editar/1/')
        self.assertEqual(resolve(url).func, views.editar_rol)
    
    def test_eliminar_rol_url(self):
        """Test URL para eliminar rol"""
        url = reverse('eliminar_rol', args=[1])
        self.assertEqual(url, '/roles/eliminar/1/')
        self.assertEqual(resolve(url).func, views.eliminar_rol)
    
    def test_detalle_rol_url(self):
        """Test URL para detalle de rol"""
        url = reverse('detalle_rol', args=[1])
        self.assertEqual(url, '/roles/detalle/1/')
        self.assertEqual(resolve(url).func, views.detalle_rol)
    
    def test_url_patterns_count(self):
        """Test que se han definido todas las URLs esperadas"""
        from roles.urls import urlpatterns
        self.assertEqual(len(urlpatterns), 5)  # Listar, crear, editar, eliminar, detalle
    
    def test_urls_con_diferentes_ids(self):
        """Test URLs con diferentes IDs"""
        # Test con diferentes IDs para verificar el patrón
        test_ids = [1, 10, 999]
        
        for test_id in test_ids:
            # Editar
            url = reverse('editar_rol', args=[test_id])
            self.assertEqual(url, f'/roles/editar/{test_id}/')
            
            # Eliminar
            url = reverse('eliminar_rol', args=[test_id])
            self.assertEqual(url, f'/roles/eliminar/{test_id}/')
            
            # Detalle
            url = reverse('detalle_rol', args=[test_id])
            self.assertEqual(url, f'/roles/detalle/{test_id}/')
    
    def test_url_sin_app_name(self):
        """Test que las URLs no usan app_name (según el archivo urls.py)"""
        # Verificar que las URLs están accesibles directamente sin namespace
        url = reverse('listar_roles')
        self.assertTrue(url.startswith('/roles/'))
        
        # Si hubiera app_name, necesitaríamos usar reverse('roles:listar_roles')
        # Como no lo hay, las URLs son directas
