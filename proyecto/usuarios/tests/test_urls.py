import pytest
from django.urls import reverse, resolve
from usuarios import views


class TestUsuariosUrls():
    """Pruebas para las URLs del módulo usuarios"""

    def test_url_registro_resuelve_correctamente(self):
        """Verifica que la URL de registro resuelve a la vista correcta"""
        url = reverse('usuarios:registro')
        resolver = resolve(url)
        assert resolver.func == views.registro_usuario
        assert resolver.namespace == 'usuarios'
        assert resolver.url_name == 'registro'

    def test_url_registro_exitoso_resuelve_correctamente(self):
        """Verifica que la URL de registro exitoso resuelve a la vista correcta"""
        url = reverse('usuarios:registro_exitoso')
        resolver = resolve(url)
        assert resolver.func == views.registro_exitoso
        assert resolver.namespace == 'usuarios'
        assert resolver.url_name == 'registro_exitoso'

    def test_url_activar_cuenta_resuelve_correctamente(self):
        """Verifica que la URL de activación de cuenta resuelve a la vista correcta"""
        uidb64_ejemplo = 'MTIz'
        token_ejemplo = 'abc123-def456'
        url = reverse('usuarios:activar_cuenta', args=[uidb64_ejemplo, token_ejemplo])
        resolver = resolve(url)
        assert resolver.func == views.activar_cuenta
        assert resolver.namespace == 'usuarios'
        assert resolver.url_name == 'activar_cuenta'
        assert resolver.kwargs['uidb64'] == uidb64_ejemplo
        assert resolver.kwargs['token'] == token_ejemplo

    def test_url_perfil_resuelve_correctamente(self):
        """Verifica que la URL de perfil resuelve a la vista correcta"""
        url = reverse('usuarios:perfil')
        resolver = resolve(url)
        assert resolver.func == views.perfil
        assert resolver.namespace == 'usuarios'
        assert resolver.url_name == 'perfil'

    def test_urls_generan_rutas_esperadas(self):
        """Verifica que las URLs generan las rutas esperadas"""
        assert reverse('usuarios:registro') == '/usuarios/registro/'
        assert reverse('usuarios:registro_exitoso') == '/usuarios/registro-exitoso/'
        assert reverse('usuarios:perfil') == '/usuarios/perfil/'

    def test_url_activar_cuenta_con_parametros_genera_ruta_esperada(self):
        """Verifica que la URL de activación genera la ruta esperada con parámetros"""
        uidb64 = 'abc123'
        token = 'token456'
        url_esperada = f'/usuarios/activar/{uidb64}/{token}/'
        url_generada = reverse('usuarios:activar_cuenta', args=[uidb64, token])
        assert url_generada == url_esperada

    def test_namespace_usuarios_existe(self):
        """Verifica que el namespace 'usuarios' está configurado correctamente"""
        url = reverse('usuarios:registro')
        resolver = resolve(url)
        assert resolver.namespace == 'usuarios'

    @pytest.mark.parametrize("url_name,expected_pattern", [
        ('registro', 'registro/'),
        ('registro_exitoso', 'registro-exitoso/'),
        ('perfil', 'perfil/'),
    ])
    def test_patrones_url_simples(self, url_name, expected_pattern):
        """Verifica que los patrones de URL simples son correctos"""
        url = reverse(f'usuarios:{url_name}')
        assert url.endswith(expected_pattern)

    def test_url_activar_cuenta_acepta_parametros_validos(self):
        """Verifica que la URL de activación acepta parámetros con formato válido"""
        # Prueba con diferentes formatos válidos
        parametros_validos = [
            ('MTIz', 'abc123-def456'),
            ('ABC123', 'token_123'),
            ('123abc', '456def789'),
        ]
        
        for uidb64, token in parametros_validos:
            try:
                url = reverse('usuarios:activar_cuenta', args=[uidb64, token])
                resolver = resolve(url)
                assert resolver.url_name == 'activar_cuenta'
                assert resolver.kwargs['uidb64'] == uidb64
                assert resolver.kwargs['token'] == token
            except Exception as e:
                pytest.fail(f"Error al resolver URL con parámetros ({uidb64}, {token}): {e}")
