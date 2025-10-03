import pytest
from roles.forms import RolForm
from roles.models import Roles

@pytest.mark.django_db
class TestRolForm:
    """Pruebas para el formulario RolForm"""
    
    def test_crear_rol_exitoso_con_datos_validos(self):
        """Prueba 1: RolForm: creación exitosa de un rol con nombre y descripción válidos."""
        form_data = {
            'name': 'Rol de Prueba',
            'descripcion': 'Descripción del rol de prueba'
        }
        form = RolForm(data=form_data)
        
        assert form.is_valid(), 'El formulario debería ser válido con datos correctos'
        rol = form.save()
        
        assert rol.name == 'Rol de Prueba', 'El nombre del rol no se guardó correctamente'
        assert rol.descripcion == 'Descripción del rol de prueba', 'La descripción del rol no se guardó correctamente'
    
    def test_error_nombre_rol_duplicado(self):
        """Prueba 2: RolForm: error si el nombre del rol ya existe (único)."""
        Roles.objects.create(name='Rol Existente', descripcion='Descripción')
        
        form_data = {
            'name': 'Rol Existente',
            'descripcion': 'Nueva descripción'
        }
        form = RolForm(data=form_data)
        
        assert not form.is_valid(), 'El formulario debería ser inválido por nombre duplicado'
        assert 'name' in form.errors, 'El error debería estar en el campo name'
    
    def test_error_nombre_vacio(self):
        """Prueba 3a: RolForm: error si el nombre está vacío."""
        form_data = {
            'name': '',
            'descripcion': 'Descripción'
        }
        form = RolForm(data=form_data)

        assert not form.is_valid(), 'El formulario debería ser inválido por nombre vacío'
        assert 'name' in form.errors, 'El error debería estar en el campo name'
    
    def test_error_nombre_excede_limite(self):
        """Prueba 3b: RolForm: error si el nombre excede el límite de caracteres."""
        nombre_largo = 'x' * 101  # Excede el límite de 100 caracteres
        form_data = {
            'name': nombre_largo,
            'descripcion': 'Descripción'
        }
        form = RolForm(data=form_data)
        
        assert not form.is_valid(), 'El formulario debería ser inválido por nombre demasiado largo'
        assert 'name' in form.errors, 'El error debería estar en el campo name'