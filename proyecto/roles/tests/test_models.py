import pytest
from django.test import TestCase
from django.contrib.auth.models import Group
from roles.models import Roles


class TestRolesModel(TestCase):
    """Pruebas para el modelo Roles"""
    
    def test_crear_rol_valido(self):
        """Test crear rol con datos válidos"""
        rol = Roles.objects.create(
            name='test_rol',
            descripcion='Descripción del rol de prueba'
        )
        
        self.assertEqual(rol.name, 'test_rol')
        self.assertEqual(rol.descripcion, 'Descripción del rol de prueba')
        self.assertEqual(str(rol), 'test_rol')
    
    def test_descripcion_puede_ser_nula(self):
        """Test que descripción puede ser nula o vacía"""
        rol = Roles.objects.create(name='sin_descripcion')
        
        self.assertIsNone(rol.descripcion)
        
        # También probar con descripción vacía
        rol_vacio = Roles.objects.create(
            name='descripcion_vacia',
            descripcion=''
        )
        
        self.assertEqual(rol_vacio.descripcion, '')
    
    def test_meta_configuracion(self):
        """Test configuración Meta del modelo"""
        self.assertEqual(Roles._meta.verbose_name, 'Rol')
        self.assertEqual(Roles._meta.verbose_name_plural, 'Roles')
    
    def test_campo_descripcion_help_text(self):
        """Test que el campo descripción tiene help_text"""
        field = Roles._meta.get_field('descripcion')
        expected_help_text = "Descripción detallada del rol"
        self.assertEqual(field.help_text, expected_help_text)
    
    def test_name_unico(self):
        """Test que el nombre del rol debe ser único (heredado de Group)"""
        Roles.objects.create(name='rol_unico_test')
        
        with self.assertRaises(Exception):  # Django levantará IntegrityError
            Roles.objects.create(name='rol_unico_test')
