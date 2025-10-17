import pytest
from django.urls import reverse
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from roles.models import Roles
from usuarios.models import Usuario


@pytest.mark.django_db
class TestRolesViews:
    """Pruebas para las vistas del módulo roles"""
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        # Crear usuario de prueba
        self.usuario = Usuario.objects.create(
            username='usuario_prueba',
            email='usuario@test.com',
            first_name='Usuario',
            last_name='Prueba',
            numero_documento='12345678',
            is_active=True
        )
        self.usuario.set_password('password123')
        self.usuario.save()
        
        # Crear rol administrador si no existe
        self.rol_admin, created = Roles.objects.get_or_create(
            name='Administrador',
            defaults={'descripcion': 'Rol con acceso completo al sistema'}
        )
        
        # Obtener o crear el permiso de gestión
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(Roles)
        self.permiso_gestion, created = Permission.objects.get_or_create(
            codename='gestion',
            name='Puede gestionar roles (crear y editar)',
            content_type=content_type
        )
    
    def test_listar_roles_usuario_autenticado_con_permiso(self, client):
        """Prueba 7: Vista listar_roles: solo usuarios autenticados y con permiso pueden acceder."""
        # Asignar permisos al usuario
        self.usuario.user_permissions.add(self.permiso_gestion)
        
        client.force_login(self.usuario)
        response = client.get(reverse('roles:listar_roles'))
        
        assert response.status_code == 200, 'El usuario con permiso debería acceder a la lista de roles'
    
    def test_listar_roles_usuario_sin_autenticar(self, client):
        """Prueba 7b: Vista listar_roles: usuarios no autenticados son redirigidos."""
        response = client.get(reverse('roles:listar_roles'))
        
        assert response.status_code == 302, 'El usuario no autenticado debería ser redirigido al login'
    
    def test_listar_roles_no_muestra_administrador(self, client):
        """Prueba 8: Vista listar_roles: no muestra el rol "Administrador" en la lista."""

        Roles.objects.get_or_create(name='Operador', defaults={'descripcion': 'Rol operador'})
        Roles.objects.get_or_create(name='Analista', defaults={'descripcion': 'Rol analista'})
        
        self.usuario.user_permissions.add(self.permiso_gestion)
        client.force_login(self.usuario)
        
        response = client.get(reverse('roles:listar_roles'))
        
        assert response.status_code == 200, 'El usuario con permiso debería acceder a la lista de roles'
        roles_en_contexto = response.context['roles']
        nombres_roles = [rol.name for rol in roles_en_contexto]
        
        assert 'Administrador' not in nombres_roles, 'El rol Administrador no debería mostrarse en la lista'
        assert 'Operador' in nombres_roles, 'El rol Operador debería mostrarse en la lista'
        assert 'Analista' in nombres_roles, 'El rol Analista debería mostrarse en la lista'

    def test_crear_rol_con_permiso_y_datos_validos(self, client):
        """Prueba 9: Vista crear_rol: permite crear un rol si el usuario tiene permiso y datos válidos."""
        self.usuario.user_permissions.add(self.permiso_gestion)
        client.force_login(self.usuario)
        
        datos_rol = {
            'name': 'Nuevo Rol',
            'descripcion': 'Descripción del nuevo rol'
        }
        
        response = client.post(reverse('roles:crear_rol'), data=datos_rol)
        
        assert response.status_code == 302, 'Debería redirigir tras crear el rol'
        assert Roles.objects.filter(name='Nuevo Rol').exists(), 'El rol no se creó correctamente'
    
    def test_crear_rol_formulario_invalido(self, client):
        """Prueba 10: Vista crear_rol: muestra errores si los datos del formulario son inválidos."""
        self.usuario.user_permissions.add(self.permiso_gestion)
        client.force_login(self.usuario)
        
        # Datos inválidos: nombre vacío
        datos_invalidos = {
            'name': '',
            'descripcion': 'Descripción'
        }
        
        response = client.post(reverse('roles:crear_rol'), data=datos_invalidos)
        
        assert response.status_code == 200, 'Debería mostrar el formulario con errores'
        assert not response.context['form'].is_valid(), 'El formulario debería ser inválido'
        assert 'name' in response.context['form'].errors, 'Debería haber error en el campo name'
    
    def test_editar_rol_existente_con_permiso(self, client):
        """Prueba 11: Vista editar_rol: permite editar un rol existente si el usuario tiene permiso."""
        rol = Roles.objects.create(name='Rol a Editar', descripcion='Descripción original')
        
        self.usuario.user_permissions.add(self.permiso_gestion)
        client.force_login(self.usuario)
        
        datos_editados = {
            'name': 'Rol Editado',
            'descripcion': 'Descripción editada'
        }
        
        response = client.post(reverse('roles:editar_rol', kwargs={'pk': rol.pk}), data=datos_editados)

        assert response.status_code == 302, 'Debería redirigir tras editar el rol'

        rol.refresh_from_db()
        assert rol.name == 'Rol Editado', 'El nombre del rol no se actualizó correctamente'
        assert rol.descripcion == 'Descripción editada', 'La descripción del rol no se actualizó correctamente'
   
    def test_editar_rol_inexistente(self, client):
        """Prueba 12: Vista editar_rol: muestra error y redirige si el rol no existe."""
        self.usuario.user_permissions.add(self.permiso_gestion)
        client.force_login(self.usuario)
        
        response = client.get(reverse('roles:editar_rol', kwargs={'pk': 99999}))
        
        assert response.status_code == 302, 'Debería redirigir si el rol no existe'
    
    def test_detalle_rol_existente(self, client):
        """Prueba 13: Vista detalle_rol: muestra detalles de un rol existente."""
        rol = Roles.objects.create(name='Rol Detalle', descripcion='Descripción del rol')
        
        self.usuario.user_permissions.add(self.permiso_gestion)
        client.force_login(self.usuario)
        
        response = client.get(reverse('roles:detalle_rol', kwargs={'pk': rol.pk}))
        
        assert response.status_code == 200, 'Debería mostrar la página de detalles del rol'
        assert 'rol' in response.context, 'El contexto debería contener el rol'
        assert response.context['rol'] == rol, 'El rol en el contexto no es el esperado'
    
    def test_detalle_rol_inexistente(self, client):
        """Prueba 14: Vista detalle_rol: muestra error y redirige si el rol no existe."""
        self.usuario.user_permissions.add(self.permiso_gestion)
        client.force_login(self.usuario)
        
        response = client.get(reverse('roles:detalle_rol', kwargs={'pk': 99999}))
        
        assert response.status_code == 302, 'Debería redirigir si el rol no existe'
    