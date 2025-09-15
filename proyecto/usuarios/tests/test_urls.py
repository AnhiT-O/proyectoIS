import pytest
from django.urls import reverse, resolve
from django.test import RequestFactory
from usuarios import views


class TestUsuariosUrls:
    """Pruebas unitarias para las URLs de la aplicación usuarios"""

    def test_registro_url_resolve(self):
        """Test que verifica que la URL de registro se resuelve correctamente"""
        url = reverse('usuarios:registro')
        resolver = resolve(url)
        
        assert resolver.func == views.registro_usuario, "La URL de registro no se resuelve a la vista correcta"
        assert resolver.view_name == 'usuarios:registro', "El nombre de la vista no es correcto"

    def test_activar_cuenta_url_resolve(self):
        """Test que verifica que la URL de activar cuenta se resuelve correctamente"""
        url = reverse('usuarios:activar_cuenta', kwargs={'uidb64': 'test123', 'token': 'token123'})
        resolver = resolve(url)
        
        assert resolver.func == views.activar_cuenta, "La URL de activar cuenta no se resuelve a la vista correcta"
        assert resolver.view_name == 'usuarios:activar_cuenta', "El nombre de la vista no es correcto"
        assert resolver.kwargs['uidb64'] == 'test123', "El parámetro uidb64 no se captura correctamente"
        assert resolver.kwargs['token'] == 'token123', "El parámetro token no se captura correctamente"

    def test_perfil_url_resolve(self):
        """Test que verifica que la URL de perfil se resuelve correctamente"""
        url = reverse('usuarios:perfil')
        resolver = resolve(url)
        
        assert resolver.func == views.perfil, "La URL de perfil no se resuelve a la vista correcta"
        assert resolver.view_name == 'usuarios:perfil', "El nombre de la vista no es correcto"

    def test_recuperar_password_url_resolve(self):
        """Test que verifica que la URL de recuperar password se resuelve correctamente"""
        url = reverse('usuarios:recuperar_password')
        resolver = resolve(url)
        
        assert resolver.func == views.recuperar_password, "La URL de recuperar password no se resuelve a la vista correcta"
        assert resolver.view_name == 'usuarios:recuperar_password', "El nombre de la vista no es correcto"

    def test_reset_password_confirm_url_resolve(self):
        """Test que verifica que la URL de reset password confirm se resuelve correctamente"""
        url = reverse('usuarios:reset_password_confirm', kwargs={'uidb64': 'test123', 'token': 'token123'})
        resolver = resolve(url)
        
        assert resolver.func == views.reset_password_confirm, "La URL de reset password confirm no se resuelve a la vista correcta"
        assert resolver.view_name == 'usuarios:reset_password_confirm', "El nombre de la vista no es correcto"
        assert resolver.kwargs['uidb64'] == 'test123', "El parámetro uidb64 no se captura correctamente"
        assert resolver.kwargs['token'] == 'token123', "El parámetro token no se captura correctamente"

    def test_administrar_usuarios_url_resolve(self):
        """Test que verifica que la URL de administrar usuarios se resuelve correctamente"""
        url = reverse('usuarios:administrar_usuarios')
        resolver = resolve(url)
        
        assert resolver.func == views.administrar_usuarios, "La URL de administrar usuarios no se resuelve a la vista correcta"
        assert resolver.view_name == 'usuarios:administrar_usuarios', "El nombre de la vista no es correcto"

    def test_usuario_detalle_url_resolve(self):
        """Test que verifica que la URL de detalle de usuario se resuelve correctamente"""
        url = reverse('usuarios:usuario_detalle', kwargs={'pk': 1})
        resolver = resolve(url)
        
        assert resolver.func == views.usuario_detalle, "La URL de detalle de usuario no se resuelve a la vista correcta"
        assert resolver.view_name == 'usuarios:usuario_detalle', "El nombre de la vista no es correcto"
        assert resolver.kwargs['pk'] == 1, "El parámetro pk no se captura correctamente"

    def test_bloquear_usuario_url_resolve(self):
        """Test que verifica que la URL de bloquear usuario se resuelve correctamente"""
        url = reverse('usuarios:bloquear_usuario', kwargs={'pk': 1})
        resolver = resolve(url)
        
        assert resolver.func == views.bloquear_usuario, "La URL de bloquear usuario no se resuelve a la vista correcta"
        assert resolver.view_name == 'usuarios:bloquear_usuario', "El nombre de la vista no es correcto"
        assert resolver.kwargs['pk'] == 1, "El parámetro pk no se captura correctamente"

    def test_asignar_rol_url_resolve(self):
        """Test que verifica que la URL de asignar rol se resuelve correctamente"""
        url = reverse('usuarios:asignar_rol', kwargs={'pk': 1})
        resolver = resolve(url)
        
        assert resolver.func == views.asignar_rol, "La URL de asignar rol no se resuelve a la vista correcta"
        assert resolver.view_name == 'usuarios:asignar_rol', "El nombre de la vista no es correcto"
        assert resolver.kwargs['pk'] == 1, "El parámetro pk no se captura correctamente"

    def test_remover_rol_url_resolve(self):
        """Test que verifica que la URL de remover rol se resuelve correctamente"""
        url = reverse('usuarios:remover_rol', kwargs={'pk': 1, 'rol_id': 2})
        resolver = resolve(url)
        
        assert resolver.func == views.remover_rol, "La URL de remover rol no se resuelve a la vista correcta"
        assert resolver.view_name == 'usuarios:remover_rol', "El nombre de la vista no es correcto"
        assert resolver.kwargs['pk'] == 1, "El parámetro pk no se captura correctamente"
        assert resolver.kwargs['rol_id'] == 2, "El parámetro rol_id no se captura correctamente"

    def test_asignar_clientes_url_resolve(self):
        """Test que verifica que la URL de asignar clientes se resuelve correctamente"""
        url = reverse('usuarios:asignar_clientes', kwargs={'pk': 1})
        resolver = resolve(url)
        
        assert resolver.func == views.asignar_clientes, "La URL de asignar clientes no se resuelve a la vista correcta"
        assert resolver.view_name == 'usuarios:asignar_clientes', "El nombre de la vista no es correcto"
        assert resolver.kwargs['pk'] == 1, "El parámetro pk no se captura correctamente"

    def test_remover_cliente_url_resolve(self):
        """Test que verifica que la URL de remover cliente se resuelve correctamente"""
        url = reverse('usuarios:remover_cliente', kwargs={'pk': 1, 'cliente_id': 2})
        resolver = resolve(url)
        
        assert resolver.func == views.remover_cliente, "La URL de remover cliente no se resuelve a la vista correcta"
        assert resolver.view_name == 'usuarios:remover_cliente', "El nombre de la vista no es correcto"
        assert resolver.kwargs['pk'] == 1, "El parámetro pk no se captura correctamente"
        assert resolver.kwargs['cliente_id'] == 2, "El parámetro cliente_id no se captura correctamente"

    def test_mis_clientes_url_resolve(self):
        """Test que verifica que la URL de mis clientes se resuelve correctamente"""
        url = reverse('usuarios:mis_clientes')
        resolver = resolve(url)
        
        assert resolver.func == views.ver_clientes_asociados, "La URL de mis clientes no se resuelve a la vista correcta"
        assert resolver.view_name == 'usuarios:mis_clientes', "El nombre de la vista no es correcto"

    def test_seleccionar_cliente_activo_url_resolve(self):
        """Test que verifica que la URL de seleccionar cliente activo se resuelve correctamente"""
        url = reverse('usuarios:seleccionar_cliente_activo', kwargs={'cliente_id': 1})
        resolver = resolve(url)
        
        assert resolver.func == views.seleccionar_cliente_activo, "La URL de seleccionar cliente activo no se resuelve a la vista correcta"
        assert resolver.view_name == 'usuarios:seleccionar_cliente_activo', "El nombre de la vista no es correcto"
        assert resolver.kwargs['cliente_id'] == 1, "El parámetro cliente_id no se captura correctamente"

    def test_detalle_cliente_url_resolve(self):
        """Test que verifica que la URL de detalle cliente se resuelve correctamente"""
        url = reverse('usuarios:detalle_cliente', kwargs={'cliente_id': 1})
        resolver = resolve(url)
        
        assert resolver.func == views.detalle_cliente, "La URL de detalle cliente no se resuelve a la vista correcta"
        assert resolver.view_name == 'usuarios:detalle_cliente', "El nombre de la vista no es correcto"
        assert resolver.kwargs['cliente_id'] == 1, "El parámetro cliente_id no se captura correctamente"

    def test_url_patterns_count(self):
        """Test que verifica que todas las URLs están definidas"""
        from usuarios.urls import urlpatterns
        
        expected_count = 15  # Número esperado de patrones de URL
        actual_count = len(urlpatterns)
        
        assert actual_count == expected_count, f"Se esperaban {expected_count} patrones de URL, pero se encontraron {actual_count}"

    def test_app_name(self):
        """Test que verifica que app_name está correctamente definido"""
        from usuarios import urls
        
        assert hasattr(urls, 'app_name'), "El módulo urls debería tener definido app_name"
        assert urls.app_name == 'usuarios', "El app_name debería ser 'usuarios'"

    def test_url_patterns_with_parameters(self):
        """Test que verifica que las URLs con parámetros funcionan con diferentes valores"""
        # Test con diferentes valores de pk
        url_usuario_1 = reverse('usuarios:usuario_detalle', kwargs={'pk': 1})
        url_usuario_999 = reverse('usuarios:usuario_detalle', kwargs={'pk': 999})
        
        assert '/usuario/1/' in url_usuario_1, "La URL debería contener el pk correcto"
        assert '/usuario/999/' in url_usuario_999, "La URL debería contener el pk correcto"
        
        # Test con diferentes valores de cliente_id
        url_cliente_1 = reverse('usuarios:detalle_cliente', kwargs={'cliente_id': 1})
        url_cliente_999 = reverse('usuarios:detalle_cliente', kwargs={'cliente_id': 999})
        
        assert '/cliente/1/' in url_cliente_1, "La URL debería contener el cliente_id correcto"
        assert '/cliente/999/' in url_cliente_999, "La URL debería contener el cliente_id correcto"

    def test_url_patterns_with_string_parameters(self):
        """Test que verifica que las URLs con parámetros string funcionan correctamente"""
        # Test con diferentes valores de uidb64 y token
        url_activar = reverse('usuarios:activar_cuenta', kwargs={'uidb64': 'abc123', 'token': 'def456'})
        url_reset = reverse('usuarios:reset_password_confirm', kwargs={'uidb64': 'xyz789', 'token': 'uvw012'})
        
        assert 'activar/abc123/def456/' in url_activar, "La URL de activar debería contener los parámetros correctos"
        assert 'reset-password/xyz789/uvw012/' in url_reset, "La URL de reset debería contener los parámetros correctos"

    def test_unique_url_names(self):
        """Test que verifica que todos los nombres de URL son únicos"""
        from usuarios.urls import urlpatterns
        
        url_names = []
        for pattern in urlpatterns:
            if hasattr(pattern, 'name') and pattern.name:
                url_names.append(pattern.name)
        
        unique_names = set(url_names)
        assert len(url_names) == len(unique_names), "Todos los nombres de URL deberían ser únicos"
