import pytest
from django.test import TestCase
from django.urls import reverse, resolve
from django.http import Http404
from roles import views


class TestRolesUrls(TestCase):
    """Pruebas para las URLs de la app roles"""

    def test_url_listar_roles(self):
        """Prueba que la URL para listar roles funciona correctamente"""
        url = reverse('roles:listar_roles')
        
        assert url == '/roles/', f"Se esperaba URL '/roles/', pero se obtuvo '{url}'"
        
        # Verificar que la URL se resuelve a la vista correcta
        resolver = resolve(url)
        assert resolver.func == views.listar_roles, f"Se esperaba vista listar_roles, pero se obtuvo {resolver.func}"

    def test_url_crear_rol(self):
        """Prueba que la URL para crear rol funciona correctamente"""
        url = reverse('roles:crear_rol')
        
        assert url == '/roles/crear/', f"Se esperaba URL '/roles/crear/', pero se obtuvo '{url}'"
        
        # Verificar que la URL se resuelve a la vista correcta
        resolver = resolve(url)
        assert resolver.func == views.crear_rol, f"Se esperaba vista crear_rol, pero se obtuvo {resolver.func}"

    def test_urls_sin_parametros_extras(self):
        """Prueba que las URLs sin parámetros no requieren argumentos adicionales"""
        urls_sin_parametros = [
            'roles:listar_roles',
            'roles:crear_rol'
        ]
        
        for url_name in urls_sin_parametros:
            url = reverse(url_name)
            resolver = resolve(url)
            
            # Verificar que no hay parámetros adicionales requeridos
            assert resolver.kwargs == {}, f"Se esperaba que '{url_name}' no tuviera parámetros, pero se encontraron {resolver.kwargs}"

    def test_resolucion_urls_directas(self):
        """Prueba que las URLs se pueden resolver directamente sin reverse"""
        url_tests = [
            ('/roles/', views.listar_roles),
            ('/roles/crear/', views.crear_rol),
            ('/roles/editar/123/', views.editar_rol),
            ('/roles/detalle/456/', views.detalle_rol),
        ]
        
        for url_path, expected_view in url_tests:
            try:
                resolver = resolve(url_path)
                assert resolver.func == expected_view, f"Se esperaba vista {expected_view.__name__} para '{url_path}', pero se obtuvo {resolver.func.__name__}"
            except Http404:
                pytest.fail(f"No se pudo resolver la URL '{url_path}'")

    def test_app_name_configurado(self):
        """Prueba que el app_name está configurado correctamente"""
        # Verificar que podemos usar el namespace en reverse
        try:
            url = reverse('roles:listar_roles')
            assert url is not None, "Se esperaba que el namespace 'roles' estuviera configurado"
        except Exception as e:
            pytest.fail(f"El namespace 'roles' no está configurado correctamente: {e}")

    def test_todas_las_urls_definidas(self):
        """Prueba que todas las URLs esperadas están definidas en urlpatterns"""
        from roles.urls import urlpatterns
        
        # Extraer los nombres de las URLs definidas
        url_names = []
        for pattern in urlpatterns:
            if hasattr(pattern, 'name') and pattern.name:
                url_names.append(pattern.name)
        
        expected_names = ['listar_roles', 'crear_rol', 'editar_rol', 'detalle_rol']
        
        for expected_name in expected_names:
            assert expected_name in url_names, f"Se esperaba encontrar la URL '{expected_name}' en urlpatterns, pero no se encontró. URLs encontradas: {url_names}"

    def test_patron_pk_solo_acepta_enteros(self):
        """Prueba que el parámetro pk en las URLs solo acepta valores enteros"""
        # URLs que deberían funcionar con enteros
        valid_urls = [
            '/roles/editar/123/',
            '/roles/detalle/1/',
            '/roles/editar/999999/',
        ]
        
        for url in valid_urls:
            try:
                resolver = resolve(url)
                assert 'pk' in resolver.kwargs, f"Se esperaba parámetro 'pk' para URL válida '{url}'"
            except Http404:
                pytest.fail(f"La URL válida '{url}' no se pudo resolver")
        
        # URLs que NO deberían funcionar (valores no enteros)
        invalid_urls = [
            '/roles/editar/abc/',
            '/roles/detalle/test/',
            '/roles/editar/12.5/',
        ]
        
        for url in invalid_urls:
            with pytest.raises(Http404, match=".*"):
                resolve(url)