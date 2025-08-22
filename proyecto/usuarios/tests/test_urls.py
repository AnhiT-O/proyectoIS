import pytest
from django.urls import reverse, resolve
from usuarios import views


class TestUsuariosUrls():
    """Pruebas para las URLs del módulo usuarios"""

    def test_url_login_resuelve_correctamente(self):
        """Verifica que la URL de login resuelve a la vista correcta"""
        url = reverse('usuarios:login')
        resolver = resolve(url)
        assert resolver.func == views.login_usuario
        assert resolver.namespace == 'usuarios'
        assert resolver.url_name == 'login'

    def test_url_logout_resuelve_correctamente(self):
        """Verifica que la URL de logout resuelve a la vista correcta"""
        url = reverse('usuarios:logout')
        resolver = resolve(url)
        assert resolver.func == views.logout_usuario
        assert resolver.namespace == 'usuarios'
        assert resolver.url_name == 'logout'

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

    def test_url_recuperar_password_resuelve_correctamente(self):
        """Verifica que la URL de recuperar password resuelve a la vista correcta"""
        url = reverse('usuarios:recuperar_password')
        resolver = resolve(url)
        assert resolver.func == views.recuperar_password
        assert resolver.namespace == 'usuarios'
        assert resolver.url_name == 'recuperar_password'

    def test_url_reset_password_confirm_resuelve_correctamente(self):
        """Verifica que la URL de confirmación de reset password resuelve a la vista correcta"""
        uidb64_ejemplo = 'MTIz'
        token_ejemplo = 'abc123-def456'
        url = reverse('usuarios:reset_password_confirm', args=[uidb64_ejemplo, token_ejemplo])
        resolver = resolve(url)
        assert resolver.func == views.reset_password_confirm
        assert resolver.namespace == 'usuarios'
        assert resolver.url_name == 'reset_password_confirm'
        assert resolver.kwargs['uidb64'] == uidb64_ejemplo
        assert resolver.kwargs['token'] == token_ejemplo

    def test_url_administrar_usuarios_resuelve_correctamente(self):
        """Verifica que la URL de administrar usuarios resuelve a la vista correcta"""
        url = reverse('usuarios:administrar_usuarios')
        resolver = resolve(url)
        assert resolver.func == views.administrar_usuarios
        assert resolver.namespace == 'usuarios'
        assert resolver.url_name == 'administrar_usuarios'

    def test_url_bloquear_usuario_resuelve_correctamente(self):
        """Verifica que la URL de bloquear usuario resuelve a la vista correcta"""
        pk_ejemplo = 1
        url = reverse('usuarios:bloquear_usuario', args=[pk_ejemplo])
        resolver = resolve(url)
        assert resolver.func == views.bloquear_usuario
        assert resolver.namespace == 'usuarios'
        assert resolver.url_name == 'bloquear_usuario'
        assert resolver.kwargs['pk'] == pk_ejemplo

    def test_url_eliminar_usuario_resuelve_correctamente(self):
        """Verifica que la URL de eliminar usuario resuelve a la vista correcta"""
        pk_ejemplo = 1
        url = reverse('usuarios:eliminar_usuario', args=[pk_ejemplo])
        resolver = resolve(url)
        assert resolver.func == views.eliminar_usuario
        assert resolver.namespace == 'usuarios'
        assert resolver.url_name == 'eliminar_usuario'
        assert resolver.kwargs['pk'] == pk_ejemplo

    def test_urls_generan_rutas_esperadas(self):
        """Verifica que las URLs generan las rutas esperadas"""
        assert reverse('usuarios:login') == '/usuarios/login/'
        assert reverse('usuarios:logout') == '/usuarios/logout/'
        assert reverse('usuarios:registro') == '/usuarios/registro/'
        assert reverse('usuarios:registro_exitoso') == '/usuarios/registro-exitoso/'
        assert reverse('usuarios:perfil') == '/usuarios/perfil/'
        assert reverse('usuarios:recuperar_password') == '/usuarios/recuperar-password/'
        assert reverse('usuarios:administrar_usuarios') == '/usuarios/administrar/'

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
        ('login', 'login/'),
        ('logout', 'logout/'),
        ('registro', 'registro/'),
        ('registro_exitoso', 'registro-exitoso/'),
        ('perfil', 'perfil/'),
        ('recuperar_password', 'recuperar-password/'),
        ('administrar_usuarios', 'administrar/'),
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

    def test_url_reset_password_confirm_acepta_parametros_validos(self):
        """Verifica que la URL de reset password acepta parámetros con formato válido"""
        # Prueba con diferentes formatos válidos
        parametros_validos = [
            ('MTIz', 'abc123-def456'),
            ('ABC123', 'token_123'),
            ('123abc', '456def789'),
        ]
        
        for uidb64, token in parametros_validos:
            try:
                url = reverse('usuarios:reset_password_confirm', args=[uidb64, token])
                resolver = resolve(url)
                assert resolver.url_name == 'reset_password_confirm'
                assert resolver.kwargs['uidb64'] == uidb64
                assert resolver.kwargs['token'] == token
            except Exception as e:
                pytest.fail(f"Error al resolver URL con parámetros ({uidb64}, {token}): {e}")

    def test_url_bloquear_usuario_con_pk_genera_ruta_esperada(self):
        """Verifica que la URL de bloquear usuario genera la ruta esperada con pk"""
        pk = 123
        url_esperada = f'/usuarios/usuario/{pk}/bloquear/'
        url_generada = reverse('usuarios:bloquear_usuario', args=[pk])
        assert url_generada == url_esperada

    def test_url_eliminar_usuario_con_pk_genera_ruta_esperada(self):
        """Verifica que la URL de eliminar usuario genera la ruta esperada con pk"""
        pk = 456
        url_esperada = f'/usuarios/usuario/{pk}/eliminar/'
        url_generada = reverse('usuarios:eliminar_usuario', args=[pk])
        assert url_generada == url_esperada

    def test_url_reset_password_confirm_con_parametros_genera_ruta_esperada(self):
        """Verifica que la URL de reset password genera la ruta esperada con parámetros"""
        uidb64 = 'abc123'
        token = 'token456'
        url_esperada = f'/usuarios/reset-password/{uidb64}/{token}/'
        url_generada = reverse('usuarios:reset_password_confirm', args=[uidb64, token])
        assert url_generada == url_esperada
