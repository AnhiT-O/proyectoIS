import pytest
from django.contrib.auth.models import Permission
from roles.forms import RolForm
from roles.models import Roles


@pytest.mark.django_db
class TestRolForm:
    
    def test_creacion_exitosa_rol_con_datos_validos(self):
        """1. RolForm: creación exitosa de un rol con nombre y descripción válidos."""
        form_data = {
            'name': 'Nuevo Rol',
            'descripcion': 'Descripción del nuevo rol'
        }
        form = RolForm(data=form_data)
        
        assert form.is_valid()
        rol = form.save()
        assert rol.name == 'Nuevo Rol'
        assert rol.descripcion == 'Descripción del nuevo rol'
    
    def test_error_nombre_rol_ya_existe(self):
        """2. RolForm: error si el nombre del rol ya existe (único)."""
        # Crear un rol existente
        Roles.objects.create(name='Rol Existente', descripcion='Test')
        
        form_data = {
            'name': 'Rol Existente',
            'descripcion': 'Otro rol con el mismo nombre'
        }
        form = RolForm(data=form_data)
        
        assert not form.is_valid()
        assert 'name' in form.errors
        assert 'Ya existe un/a Grupo con este/a Nombre' in str(form.errors['name'])
    
    def test_error_nombre_vacio(self):
        """3. RolForm: error si el nombre está vacío o excede el límite de caracteres."""
        # Prueba con nombre vacío
        form_data = {
            'name': '',
            'descripcion': 'Descripción válida'
        }
        form = RolForm(data=form_data)
        
        assert not form.is_valid()
        assert 'name' in form.errors
        assert 'Debes ingresar un nombre.' in form.errors['name']
    
    def test_error_nombre_excede_limite_caracteres(self):
        """3. RolForm: error si el nombre excede el límite de caracteres."""
        # Prueba con nombre que excede 100 caracteres
        nombre_largo = 'x' * 101
        form_data = {
            'name': nombre_largo,
            'descripcion': 'Descripción válida'
        }
        form = RolForm(data=form_data)
        
        assert not form.is_valid()
        assert 'name' in form.errors
        assert 'El nombre no puede exceder los 100 caracteres.' in form.errors['name']