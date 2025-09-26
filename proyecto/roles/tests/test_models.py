import pytest
from roles.models import Roles


@pytest.mark.django_db
class TestRolesModel:
    
    def test_str_retorna_nombre_correctamente(self):
        """4. Modelo Roles: método __str__ retorna el nombre correctamente."""
        rol = Roles.objects.create(name='Test Rol', descripcion='Descripción de prueba')
        assert str(rol) == 'Test Rol'
    
    def test_propiedad_nombre_retorna_valor_name(self):
        """5. Modelo Roles: propiedad nombre retorna el mismo valor que name."""
        rol = Roles.objects.create(name='Test Rol', descripcion='Descripción de prueba')
        assert rol.nombre == rol.name
        assert rol.nombre == 'Test Rol'
    
    def test_roles_predefinidos_creados_tras_migraciones(self):
        """6. Modelo Roles: se crean los roles predefinidos tras migraciones."""
        # Verificar que los roles predefinidos existen
        roles_esperados = ['Operador', 'Analista cambiario', 'Administrador']
        
        for nombre_rol in roles_esperados:
            assert Roles.objects.filter(name=nombre_rol).exists(), f"El rol '{nombre_rol}' no existe"
        
        # Verificar descripciones específicas
        operador = Roles.objects.get(name='Operador')
        assert 'operaciones básicas' in operador.descripcion
        
        analista = Roles.objects.get(name='Analista cambiario')
        assert 'análisis de tipos de cambio' in analista.descripcion
        
        admin = Roles.objects.get(name='Administrador')
        assert 'acceso completo' in admin.descripcion