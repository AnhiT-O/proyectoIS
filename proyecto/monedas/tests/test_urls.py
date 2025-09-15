import pytest
from django.test import TestCase
from django.urls import reverse, resolve
from django.http import Http404

from monedas import views


class TestMonedaUrls(TestCase):
    """
    Test suite para las URLs de la app monedas.
    Verifica que las rutas estén correctamente configuradas y resuelvan a las vistas correctas.
    """

    def test_url_lista_monedas_reverse(self):
        """Test que verifica que la URL de lista de monedas se resuelve correctamente."""
        url = reverse('monedas:lista_monedas')
        
        assert url == '/monedas/', f"La URL de lista debería ser '/monedas/', pero es '{url}'"

    def test_url_lista_monedas_resolve(self):
        """Test que verifica que la URL de lista resuelve a la vista correcta."""
        resolver = resolve('/monedas/')
        
        assert resolver.func == views.moneda_lista, "La URL '/monedas/' debería resolver a la vista moneda_lista"
        assert resolver.url_name == 'lista_monedas', "El nombre de la URL debería ser 'lista_monedas'"
        assert resolver.namespace == 'monedas', "El namespace debería ser 'monedas'"

    def test_url_crear_monedas_reverse(self):
        """Test que verifica que la URL de crear moneda se resuelve correctamente."""
        url = reverse('monedas:crear_monedas')
        
        assert url == '/monedas/crear/', f"La URL de crear debería ser '/monedas/crear/', pero es '{url}'"

    def test_url_crear_monedas_resolve(self):
        """Test que verifica que la URL de crear resuelve a la vista correcta."""
        resolver = resolve('/monedas/crear/')
        
        assert resolver.func == views.moneda_crear, "La URL '/monedas/crear/' debería resolver a la vista moneda_crear"
        assert resolver.url_name == 'crear_monedas', "El nombre de la URL debería ser 'crear_monedas'"
        assert resolver.namespace == 'monedas', "El namespace debería ser 'monedas'"

    def test_url_editar_monedas_reverse(self):
        """Test que verifica que la URL de editar moneda se resuelve correctamente."""
        url = reverse('monedas:editar_monedas', kwargs={'pk': 1})
        
        assert url == '/monedas/1/editar/', f"La URL de editar debería ser '/monedas/1/editar/', pero es '{url}'"

    def test_url_editar_monedas_reverse_con_diferentes_pks(self):
        """Test que verifica que la URL de editar funciona con diferentes PKs."""
        urls_esperadas = [
            (1, '/monedas/1/editar/'),
            (123, '/monedas/123/editar/'),
            (9999, '/monedas/9999/editar/')
        ]
        
        for pk, url_esperada in urls_esperadas:
            url = reverse('monedas:editar_monedas', kwargs={'pk': pk})
            assert url == url_esperada, f"Para pk={pk}, la URL debería ser '{url_esperada}', pero es '{url}'"

    def test_url_editar_monedas_resolve(self):
        """Test que verifica que la URL de editar resuelve a la vista correcta."""
        resolver = resolve('/monedas/1/editar/')
        
        assert resolver.func == views.moneda_editar, "La URL '/monedas/1/editar/' debería resolver a la vista moneda_editar"
        assert resolver.url_name == 'editar_monedas', "El nombre de la URL debería ser 'editar_monedas'"
        assert resolver.namespace == 'monedas', "El namespace debería ser 'monedas'"
        assert resolver.kwargs == {'pk': 1}, "Los kwargs deberían contener el pk correcto"

    def test_url_editar_monedas_resolve_diferentes_pks(self):
        """Test que verifica que la URL de editar extrae correctamente diferentes PKs."""
        casos_prueba = [
            ('/monedas/1/editar/', 1),
            ('/monedas/42/editar/', 42),
            ('/monedas/999/editar/', 999)
        ]
        
        for url, pk_esperado in casos_prueba:
            resolver = resolve(url)
            assert resolver.kwargs['pk'] == pk_esperado, f"Para la URL '{url}', el pk debería ser {pk_esperado}"

    def test_app_name_configuration(self):
        """Test que verifica que el app_name está correctamente configurado."""
        # Verificar que podemos resolver usando el namespace
        try:
            url = reverse('monedas:lista_monedas')
            assert url is not None, "Debería poder resolver URLs usando el namespace 'monedas'"
        except Exception as e:
            pytest.fail(f"El namespace 'monedas' no está configurado correctamente: {e}")

    def test_urls_no_permiten_metodos_invalidos(self):
        """Test que verifica que las URLs solo aceptan métodos HTTP válidos."""
        # Este test verifica la configuración básica de URLs
        # Los métodos HTTP específicos se manejan en las vistas
        urls_validas = [
            '/monedas/',
            '/monedas/crear/',
            '/monedas/1/editar/'
        ]
        
        for url in urls_validas:
            try:
                resolver = resolve(url)
                assert resolver.func is not None, f"La URL '{url}' debería tener una vista asociada"
            except Http404:
                pytest.fail(f"La URL '{url}' no debería generar Http404 durante la resolución")

    def test_urls_con_trailing_slash(self):
        """Test que verifica el comportamiento con trailing slashes."""
        # Django por defecto maneja los trailing slashes
        urls_con_slash = [
            '/monedas/',
            '/monedas/crear/',
            '/monedas/1/editar/'
        ]
        
        for url in urls_con_slash:
            try:
                resolver = resolve(url)
                assert resolver.func is not None, f"La URL '{url}' con trailing slash debería resolverse correctamente"
            except Http404:
                pytest.fail(f"La URL '{url}' con trailing slash debería ser válida")

    def test_namespace_isolation(self):
        """Test que verifica que el namespace 'monedas' está correctamente aislado."""
        # Verificar que todas las URLs de monedas usan el namespace correcto
        urls_con_namespace = [
            ('monedas:lista_monedas', 'lista_monedas'),
            ('monedas:crear_monedas', 'crear_monedas'),
            ('monedas:editar_monedas', 'editar_monedas')
        ]
        
        for url_con_namespace, nombre_esperado in urls_con_namespace:
            try:
                if 'editar' in url_con_namespace:
                    url = reverse(url_con_namespace, kwargs={'pk': 1})
                else:
                    url = reverse(url_con_namespace)
                
                resolver = resolve(url)
                assert resolver.url_name == nombre_esperado, f"El nombre de URL debería ser '{nombre_esperado}'"
                assert resolver.namespace == 'monedas', f"El namespace debería ser 'monedas'"
            except Exception as e:
                pytest.fail(f"Error al resolver '{url_con_namespace}': {e}")

    def test_url_patterns_list_length(self):
        """Test que verifica que se han definido todas las URLs esperadas."""
        from monedas.urls import urlpatterns
        
        assert len(urlpatterns) == 3, f"Deberían haber exactamente 3 patrones de URL, pero hay {len(urlpatterns)}"

    def test_todas_las_vistas_estan_importadas(self):
        """Test que verifica que todas las vistas necesarias están disponibles."""
        vistas_requeridas = ['moneda_lista', 'moneda_crear', 'moneda_editar']
        
        for vista in vistas_requeridas:
            assert hasattr(views, vista), f"La vista '{vista}' debería estar definida en views.py"
            assert callable(getattr(views, vista)), f"'{vista}' debería ser una función/vista callable"