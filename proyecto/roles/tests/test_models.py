import pytest
from django.test import TestCase
from django.contrib.auth.models import Permission
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from roles.models import Roles


@pytest.mark.django_db
class TestRolesModel(TestCase):
    """Pruebas para el modelo Roles"""

    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.rol_data = {
            'name': 'Rol Test',
            'descripcion': 'Descripción del rol de prueba'
        }

    def test_crear_rol_exitoso(self):
        """Prueba que se puede crear un rol correctamente"""
        rol = Roles.objects.create(**self.rol_data)
        
        assert rol.name == 'Rol Test', f"Se esperaba 'Rol Test', pero se obtuvo '{rol.name}'"
        assert rol.descripcion == 'Descripción del rol de prueba', f"Se esperaba 'Descripción del rol de prueba', pero se obtuvo '{rol.descripcion}'"
        assert str(rol) == 'Rol Test', f"Se esperaba 'Rol Test' en __str__, pero se obtuvo '{str(rol)}'"

    def test_propiedad_nombre_alias(self):
        """Prueba que la propiedad nombre funciona como alias de name"""
        rol = Roles.objects.create(**self.rol_data)
        
        assert rol.nombre == rol.name, f"Se esperaba que nombre ({rol.nombre}) fuera igual a name ({rol.name})"

    def test_str_representation(self):
        """Prueba que la representación string del rol es correcta"""
        rol = Roles.objects.create(**self.rol_data)
        
        assert str(rol) == 'Rol Test', f"Se esperaba 'Rol Test' como representación string, pero se obtuvo '{str(rol)}'"

    def test_meta_configuration(self):
        """Prueba que la configuración Meta del modelo es correcta"""
        rol = Roles.objects.create(**self.rol_data)
        
        assert rol._meta.verbose_name == 'Rol', f"Se esperaba verbose_name 'Rol', pero se obtuvo '{rol._meta.verbose_name}'"
        assert rol._meta.verbose_name_plural == 'Roles', f"Se esperaba verbose_name_plural 'Roles', pero se obtuvo '{rol._meta.verbose_name_plural}'"
        assert rol._meta.db_table == 'roles', f"Se esperaba db_table 'roles', pero se obtuvo '{rol._meta.db_table}'"

    def test_permissions_configuration(self):
        """Prueba que los permisos personalizados están configurados correctamente"""
        permissions = [perm[0] for perm in Roles._meta.permissions]
        
        assert 'gestion' in permissions, f"Se esperaba el permiso 'gestion' en {permissions}"
        
        # Verificar que no tiene permisos por defecto
        default_permissions = Roles._meta.default_permissions
        assert default_permissions == [], f"Se esperaban permisos por defecto vacíos, pero se obtuvo {default_permissions}"

    def test_descripcion_opcional(self):
        """Prueba que el campo descripcion es opcional"""
        rol_sin_descripcion = Roles.objects.create(name='Rol Sin Descripción')
        
        assert rol_sin_descripcion.descripcion is None, f"Se esperaba descripcion None, pero se obtuvo '{rol_sin_descripcion.descripcion}'"

    def test_descripcion_puede_ser_vacia(self):
        """Prueba que el campo descripcion puede ser una cadena vacía"""
        rol_descripcion_vacia = Roles.objects.create(
            name='Rol Descripción Vacía',
            descripcion=''
        )
        
        assert rol_descripcion_vacia.descripcion == '', f"Se esperaba descripcion vacía, pero se obtuvo '{rol_descripcion_vacia.descripcion}'"

    def test_asignar_permisos_a_rol(self):
        """Prueba que se pueden asignar permisos a un rol"""
        rol = Roles.objects.create(**self.rol_data)
        
        # Obtener un permiso existente
        permission = Permission.objects.filter(codename='gestion').first()
        if permission:
            rol.permissions.add(permission)
            
            assert permission in rol.permissions.all(), f"Se esperaba que el permiso '{permission}' estuviera asignado al rol"

    def test_heredencia_de_group(self):
        """Prueba que Roles hereda correctamente de Group"""
        from django.contrib.auth.models import Group
        
        rol = Roles.objects.create(**self.rol_data)
        
        assert isinstance(rol, Group), f"Se esperaba que el rol fuera una instancia de Group, pero es {type(rol)}"
        
        # Verificar que aparece también en la tabla de Groups
        group_exists = Group.objects.filter(name='Rol Test').exists()
        assert group_exists, "Se esperaba que el rol también apareciera en la tabla de Groups"


@pytest.mark.django_db 
class TestRolesPredefinidos(TestCase):
    """Pruebas para verificar los roles predefinidos creados por la señal"""

    def test_roles_predefinidos_existen(self):
        """Prueba que los roles predefinidos se crean correctamente"""
        # Los roles se crean automáticamente con la señal post_migrate
        roles_esperados = ['Operador', 'Analista cambiario', 'Administrador']
        
        for nombre_rol in roles_esperados:
            rol_existe = Roles.objects.filter(name=nombre_rol).exists()
            assert rol_existe, f"Se esperaba que existiera el rol predefinido '{nombre_rol}'"

    def test_descripcion_roles_predefinidos(self):
        """Prueba que los roles predefinidos tienen las descripciones correctas"""
        descripciones_esperadas = {
            'Operador': 'Rol encargado de realizar operaciones básicas del sistema, incluyendo registro de transacciones y consultas de clientes.',
            'Analista cambiario': 'Rol responsable del análisis de tipos de cambio, generación de reportes financieros y supervisión de operaciones cambiarias.',
            'Administrador': 'Rol con acceso completo al sistema, incluyendo gestión de usuarios, configuración del sistema y supervisión general.'
        }
        
        for nombre_rol, descripcion_esperada in descripciones_esperadas.items():
            try:
                rol = Roles.objects.get(name=nombre_rol)
                assert rol.descripcion == descripcion_esperada, f"Se esperaba descripción '{descripcion_esperada}' para el rol '{nombre_rol}', pero se obtuvo '{rol.descripcion}'"
            except Roles.DoesNotExist:
                pytest.fail(f"No se encontró el rol predefinido '{nombre_rol}'")