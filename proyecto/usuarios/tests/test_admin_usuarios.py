import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

# Fixtures para los tests
@pytest.fixture
def admin_user(db):
    """Crear un usuario administrador para las pruebas"""
    Usuario = get_user_model()
    admin = Usuario.objects.create_user(
        username='admin',
        password='adminpass123',
        email='admin@test.com',
        first_name='Admin',
        last_name='Test',
        tipo_cedula='CI',
        cedula_identidad='1234567',
        is_staff=True,
        is_active=True
    )
    return admin

@pytest.fixture
def normal_user(db):
    """Crear un usuario normal para las pruebas"""
    Usuario = get_user_model()
    user = Usuario.objects.create_user(
        username='usuario',
        password='userpass123',
        email='user@test.com',
        first_name='Usuario',
        last_name='Test',
        tipo_cedula='CI',
        cedula_identidad='7654321',
        is_active=True
    )
    return user

@pytest.fixture
def admin_client(client, admin_user):
    """Cliente con sesión iniciada como administrador"""
    client.login(username='admin', password='adminpass123')
    return client

@pytest.fixture
def user_client(client, normal_user):
    """Cliente con sesión iniciada como usuario normal"""
    client.login(username='usuario', password='userpass123')
    return client

class TestAdministrarUsuarios:
    """Tests para la vista de administración de usuarios"""

    def test_acceso_sin_autenticar(self, client):
        """Usuario no autenticado es redirigido al login"""
        url = reverse('usuarios:administrar_usuarios')
        response = client.get(url)
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_acceso_usuario_normal(self, user_client):
        """Usuario normal es redirigido al perfil"""
        url = reverse('usuarios:administrar_usuarios')
        response = user_client.get(url)
        assert response.status_code == 302
        assert reverse('usuarios:perfil') in response.url

        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert 'No tienes permisos' in str(messages[0])

    def test_acceso_admin(self, admin_client, normal_user):
        """Administrador puede acceder y ver lista de usuarios"""
        url = reverse('usuarios:administrar_usuarios')
        response = admin_client.get(url)

        assert response.status_code == 200
        assert 'usuarios' in response.context
        usuarios_lista = response.context['usuarios']
        assert len(usuarios_lista) == 1
        assert normal_user in usuarios_lista

class TestBloquearUsuario:
    """Tests para la funcionalidad de bloquear/desbloquear usuarios"""

    def test_bloqueo_sin_autenticar(self, client, normal_user):
        """Usuario no autenticado no puede bloquear"""
        url = reverse('usuarios:bloquear_usuario', kwargs={'pk': normal_user.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert '/login/' in response.url

        # Verificar que el usuario sigue activo
        normal_user.refresh_from_db()
        assert normal_user.is_active

    def test_bloqueo_usuario_normal(self, user_client, admin_user):
        """Usuario normal no puede bloquear a otros"""
        url = reverse('usuarios:bloquear_usuario', kwargs={'pk': admin_user.pk})
        response = user_client.post(url)
        assert response.status_code == 302
        assert reverse('usuarios:perfil') in response.url

        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert 'No tienes permisos' in str(messages[0])

    def test_bloqueo_admin(self, admin_client, normal_user):
        """Admin puede bloquear y desbloquear usuarios"""
        url = reverse('usuarios:bloquear_usuario', kwargs={'pk': normal_user.pk})

        # Bloquear usuario
        response = admin_client.post(url)
        assert response.status_code == 302
        assert reverse('usuarios:administrar_usuarios') in response.url

        # Verificar bloqueo
        normal_user.refresh_from_db()
        assert not normal_user.is_active

        # Desbloquear usuario
        response = admin_client.post(url)
        normal_user.refresh_from_db()
        assert normal_user.is_active

    def test_bloqueo_otro_admin(self, admin_client, admin_user):
        """Admin no puede bloquear a otro admin"""
        url = reverse('usuarios:bloquear_usuario', kwargs={'pk': admin_user.pk})
        response = admin_client.post(url)
        assert response.status_code == 302

        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert 'No puedes bloquear a otros administradores' in str(messages[0])

        # Verificar que sigue activo
        admin_user.refresh_from_db()
        assert admin_user.is_active

    def test_metodo_no_permitido(self, admin_client, normal_user):
        """Solo se permite método POST"""
        url = reverse('usuarios:bloquear_usuario', kwargs={'pk': normal_user.pk})
        response = admin_client.get(url)
        assert response.status_code == 302

        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert 'Método no permitido' in str(messages[0])

class TestEliminarUsuario:
    """Tests para la funcionalidad de eliminar usuarios"""

    def test_eliminar_sin_autenticar(self, client, normal_user):
        """Usuario no autenticado no puede eliminar"""
        url = reverse('usuarios:eliminar_usuario', kwargs={'pk': normal_user.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert '/login/' in response.url

        # Verificar que el usuario sigue existiendo
        assert get_user_model().objects.filter(pk=normal_user.pk).exists()

    def test_eliminar_usuario_normal(self, user_client, admin_user):
        """Usuario normal no puede eliminar"""
        url = reverse('usuarios:eliminar_usuario', kwargs={'pk': admin_user.pk})
        response = user_client.post(url)
        assert response.status_code == 302
        assert reverse('usuarios:perfil') in response.url

        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert 'No tienes permisos' in str(messages[0])

    def test_eliminar_como_admin(self, admin_client, normal_user):
        """Admin puede eliminar usuarios normales"""
        url = reverse('usuarios:eliminar_usuario', kwargs={'pk': normal_user.pk})
        response = admin_client.post(url)
        assert response.status_code == 302
        assert reverse('usuarios:administrar_usuarios') in response.url

        # Verificar que el usuario fue eliminado
        assert not get_user_model().objects.filter(pk=normal_user.pk).exists()

    def test_eliminar_otro_admin(self, admin_client, admin_user):
        """Admin no puede eliminar a otro admin"""
        url = reverse('usuarios:eliminar_usuario', kwargs={'pk': admin_user.pk})
        response = admin_client.post(url)
        assert response.status_code == 302

        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert 'No puedes eliminar a otros administradores' in str(messages[0])

        # Verificar que sigue existiendo
        assert get_user_model().objects.filter(pk=admin_user.pk).exists()

    def test_metodo_no_permitido(self, admin_client, normal_user):
        """Solo se permite método POST"""
        url = reverse('usuarios:eliminar_usuario', kwargs={'pk': normal_user.pk})
        response = admin_client.get(url)
        assert response.status_code == 302

        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert 'Método no permitido' in str(messages[0])
