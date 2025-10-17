import pytest
from roles.models import Roles

@pytest.mark.django_db
class TestRolesModel:
    """Pruebas para el modelo Roles"""
    
    def test_str_retorna_nombre_correctamente(self):
        """Prueba 4: Modelo Roles: método __str__ retorna el nombre correctamente."""
        rol = Roles.objects.create(
            name='Rol de Prueba',
            descripcion='Descripción del rol'
        )
        
        assert str(rol) == 'Rol de Prueba', 'El método __str__ no retorna el nombre correctamente'
    
    def test_propiedad_nombre_retorna_mismo_valor_que_name(self):
        """Prueba 5: Modelo Roles: propiedad nombre retorna el mismo valor que name."""
        rol = Roles.objects.create(
            name='Analista Financiero',
            descripcion='Rol para análisis financiero'
        )
        
        assert rol.nombre == rol.name, 'La propiedad nombre no retorna el mismo valor que name'
    
    def test_creacion_roles_predefinidos_tras_migraciones(self):
        """Prueba 6: Modelo Roles: se crean los roles predefinidos tras migraciones."""
        
        roles_esperados = ['Operador', 'Analista cambiario', 'Administrador']
        
        for nombre_rol in roles_esperados:
            rol = Roles.objects.filter(name=nombre_rol).first()
            assert rol is not None, f"El rol '{nombre_rol}' debería existir"
            assert rol.descripcion is not None, f"El rol '{nombre_rol}' debería tener descripción"