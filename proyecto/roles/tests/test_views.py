import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.contrib.auth import get_user_model
from roles.models import Roles

User = get_user_model()


@pytest.mark.django_db
class TestRolesViews:
    
    @pytest.fixture
    def client(self):
        return Client()
    
    @pytest.fixture
    def user_with_permission(self):
        """Usuario con permiso de gestión de roles"""
        user = User(
            username='test_user',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            tipo_cedula='CI',
            cedula_identidad='1234567890',
            is_active=True
        )
        user.set_password('testpass123')
        user.save()
        
        permission = Permission.objects.get(codename='gestion', content_type__app_label='roles')
        user.user_permissions.add(permission)
        return user
    
    @pytest.fixture
    def user_without_permission(self):
        """Usuario sin permiso de gestión de roles"""
        user = User(
            username='no_perm_user',
            first_name='No Permission',
            last_name='User',
            email='noperm@example.com',
            tipo_cedula='CI',
            cedula_identidad='9876543210',
            is_active=True
        )
        user.set_password('testpass123')
        user.save()
        return user
    
    @pytest.fixture
    def test_rol(self):
        """Rol de prueba"""
        return Roles.objects.create(name='Test Rol', descripcion='Rol de prueba')

    def test_listar_roles_usuario_autenticado_con_permiso(self, client, user_with_permission):
        """7. Vista listar_roles: solo usuarios autenticados y con permiso pueden acceder."""
        client.login(username='test_user', password='testpass123')
        response = client.get(reverse('roles:listar_roles'))
        assert response.status_code == 200
    
    def test_listar_roles_usuario_sin_autenticar(self, client):
        """7. Vista listar_roles: usuarios no autenticados no pueden acceder."""
        response = client.get(reverse('roles:listar_roles'))
        assert response.status_code == 302  # Redirección a login
    
    def test_listar_roles_usuario_sin_permiso(self, client, user_without_permission):
        """7. Vista listar_roles: usuarios sin permiso no pueden acceder."""
        client.login(username='no_perm_user', password='testpass123')
        response = client.get(reverse('roles:listar_roles'))
        assert response.status_code == 403  # Forbidden
    
    def test_listar_roles_no_muestra_administrador(self, client, user_with_permission):
        """8. Vista listar_roles: no muestra el rol "Administrador" en la lista."""
        client.login(username='test_user', password='testpass123')
        response = client.get(reverse('roles:listar_roles'))
        
        assert response.status_code == 200
        roles_en_contexto = response.context['roles']
        nombres_roles = [rol.name for rol in roles_en_contexto]
        assert 'Administrador' not in nombres_roles
    
    def test_crear_rol_con_datos_validos(self, client, user_with_permission):
        """9. Vista crear_rol: permite crear un rol si el usuario tiene permiso y datos válidos."""
        client.login(username='test_user', password='testpass123')
        
        data = {
            'name': 'Nuevo Rol Test',
            'descripcion': 'Descripción del nuevo rol'
        }
        response = client.post(reverse('roles:crear_rol'), data)
        
        assert response.status_code == 302  # Redirección después de crear
        assert Roles.objects.filter(name='Nuevo Rol Test').exists()
    
    def test_crear_rol_muestra_errores_datos_invalidos(self, client, user_with_permission):
        """10. Vista crear_rol: muestra errores si los datos del formulario son inválidos."""
        client.login(username='test_user', password='testpass123')
        
        # Datos inválidos (nombre vacío)
        data = {
            'name': '',
            'descripcion': 'Descripción válida'
        }
        response = client.post(reverse('roles:crear_rol'), data)
        
        assert response.status_code == 200  # Se queda en la misma página
        assert 'form' in response.context
        assert response.context['form'].errors
    
    def test_editar_rol_permite_edicion_con_permiso(self, client, user_with_permission, test_rol):
        """11. Vista editar_rol: permite editar un rol existente si el usuario tiene permiso."""
        client.login(username='test_user', password='testpass123')
        
        data = {
            'name': 'Rol Editado',
            'descripcion': 'Descripción editada'
        }
        response = client.post(reverse('roles:editar_rol', kwargs={'pk': test_rol.pk}), data)
        
        assert response.status_code == 302  # Redirección después de editar
        test_rol.refresh_from_db()
        assert test_rol.name == 'Rol Editado'
        assert test_rol.descripcion == 'Descripción editada'
    
    def test_editar_rol_no_existente_muestra_error(self, client, user_with_permission):
        """12. Vista editar_rol: muestra error y redirige si el rol no existe."""
        client.login(username='test_user', password='testpass123')
        
        response = client.get(reverse('roles:editar_rol', kwargs={'pk': 999}))
        
        assert response.status_code == 302  # Redirección
        messages = list(get_messages(response.wsgi_request))
        assert any('Rol no encontrado' in str(message) for message in messages)
    
    def test_detalle_rol_muestra_detalles_rol_existente(self, client, user_with_permission, test_rol):
        """13. Vista detalle_rol: muestra detalles de un rol existente."""
        client.login(username='test_user', password='testpass123')
        
        response = client.get(reverse('roles:detalle_rol', kwargs={'pk': test_rol.pk}))
        
        assert response.status_code == 200
        assert response.context['rol'] == test_rol
    
    def test_detalle_rol_no_existente_muestra_error(self, client, user_with_permission):
        """14. Vista detalle_rol: muestra error y redirige si el rol no existe."""
        client.login(username='test_user', password='testpass123')
        
        response = client.get(reverse('roles:detalle_rol', kwargs={'pk': 999}))
        
        assert response.status_code == 302  # Redirección
        messages = list(get_messages(response.wsgi_request))
        assert any('Rol no encontrado' in str(message) for message in messages)
    
    def test_crear_rol_sin_permiso_acceso_denegado(self, client, user_without_permission):
        """15. Vista crear_rol: redirige o muestra error si el usuario no tiene el permiso roles.gestion."""
        client.login(username='no_perm_user', password='testpass123')
        
        response = client.get(reverse('roles:crear_rol'))
        assert response.status_code == 403  # Forbidden
    
    def test_editar_rol_sin_permiso_acceso_denegado(self, client, user_without_permission, test_rol):
        """15. Vista editar_rol: redirige o muestra error si el usuario no tiene el permiso roles.gestion."""
        client.login(username='no_perm_user', password='testpass123')
        
        response = client.get(reverse('roles:editar_rol', kwargs={'pk': test_rol.pk}))
        assert response.status_code == 403  # Forbidden
    
    def test_detalle_rol_sin_permiso_acceso_denegado(self, client, user_without_permission, test_rol):
        """15. Vista detalle_rol: redirige o muestra error si el usuario no tiene el permiso roles.gestion."""
        client.login(username='no_perm_user', password='testpass123')
        
        response = client.get(reverse('roles:detalle_rol', kwargs={'pk': test_rol.pk}))
        assert response.status_code == 403  # Forbidden