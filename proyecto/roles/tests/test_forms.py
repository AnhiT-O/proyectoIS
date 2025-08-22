import pytest
from django.test import TestCase
from django.contrib.auth.models import Permission
from roles.forms import RolForm
from roles.models import Roles


class TestRolForm(TestCase):
    """Pruebas para el formulario RolForm"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Obtener algunos permisos para las pruebas
        self.permisos = Permission.objects.all()[:3]
    
    def test_form_valido(self):
        """Test formulario con datos válidos"""
        form_data = {
            'name': 'test_rol',
            'descripcion': 'Descripción del rol de prueba',
            'permisos': [p.id for p in self.permisos]
        }
        form = RolForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_sin_nombre(self):
        """Test formulario sin nombre (campo requerido)"""
        form_data = {
            'name': '',
            'descripcion': 'Descripción del rol',
            'permisos': []
        }
        form = RolForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
    
    def test_form_sin_descripcion(self):
        """Test formulario sin descripción (campo opcional)"""
        form_data = {
            'name': 'rol_sin_descripcion',
            'descripcion': '',
            'permisos': []
        }
        form = RolForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_sin_permisos(self):
        """Test formulario sin permisos (campo opcional)"""
        form_data = {
            'name': 'rol_sin_permisos',
            'descripcion': 'Rol sin permisos específicos',
            'permisos': []
        }
        form = RolForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_widgets(self):
        """Test widgets del formulario"""
        form = RolForm()
        
        # Verificar widget del campo name
        name_widget = form.fields['name'].widget
        self.assertIn('form-control', name_widget.attrs.get('class', ''))
        self.assertEqual(name_widget.attrs.get('placeholder'), 'Ingrese el nombre del rol')
        
        # Verificar widget del campo descripcion
        desc_widget = form.fields['descripcion'].widget
        self.assertIn('form-control', desc_widget.attrs.get('class', ''))
        self.assertEqual(desc_widget.attrs.get('placeholder'), 'Ingrese una descripción para el rol')
        self.assertEqual(desc_widget.attrs.get('rows'), '4')
        
        # Verificar widget del campo permisos
        permisos_widget = form.fields['permisos'].widget
        self.assertEqual(permisos_widget.__class__.__name__, 'CheckboxSelectMultiple')
    
    def test_form_save_crear_nuevo(self):
        """Test método save para crear nuevo rol"""
        form_data = {
            'name': 'nuevo_rol',
            'descripcion': 'Nuevo rol de prueba',
            'permisos': [self.permisos[0].id, self.permisos[1].id]
        }
        form = RolForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        rol = form.save()
        
        # Verificar que se creó el rol
        self.assertEqual(rol.name, 'nuevo_rol')
        self.assertEqual(rol.descripcion, 'Nuevo rol de prueba')
        
        # Verificar que se asignaron los permisos
        permisos_asignados = list(rol.permissions.all())
        self.assertEqual(len(permisos_asignados), 2)
        self.assertIn(self.permisos[0], permisos_asignados)
        self.assertIn(self.permisos[1], permisos_asignados)
    
    def test_form_save_editar_existente(self):
        """Test método save para editar rol existente"""
        # Crear rol existente
        rol_existente = Roles.objects.create(
            name='rol_existente',
            descripcion='Descripción original'
        )
        rol_existente.permissions.add(self.permisos[0])
        
        # Crear formulario con instancia existente
        form_data = {
            'name': 'rol_actualizado',
            'descripcion': 'Descripción actualizada',
            'permisos': [self.permisos[1].id, self.permisos[2].id]
        }
        form = RolForm(data=form_data, instance=rol_existente)
        self.assertTrue(form.is_valid())
        
        rol_actualizado = form.save()
        
        # Verificar que se actualizó
        self.assertEqual(rol_actualizado.pk, rol_existente.pk)
        self.assertEqual(rol_actualizado.name, 'rol_actualizado')
        self.assertEqual(rol_actualizado.descripcion, 'Descripción actualizada')
        
        # Verificar que se actualizaron los permisos
        permisos_actualizados = list(rol_actualizado.permissions.all())
        self.assertEqual(len(permisos_actualizados), 2)
        self.assertIn(self.permisos[1], permisos_actualizados)
        self.assertIn(self.permisos[2], permisos_actualizados)
        self.assertNotIn(self.permisos[0], permisos_actualizados)
    
    def test_form_init_con_instancia(self):
        """Test inicialización del formulario con instancia existente"""
        # Crear rol con permisos
        rol_existente = Roles.objects.create(
            name='rol_con_permisos',
            descripcion='Rol con permisos'
        )
        rol_existente.permissions.add(self.permisos[0], self.permisos[1])
        
        # Crear formulario con instancia
        form = RolForm(instance=rol_existente)
        
        # Verificar que los permisos iniciales están establecidos
        permisos_iniciales = form.fields['permisos'].initial
        self.assertEqual(len(permisos_iniciales), 2)
        self.assertIn(self.permisos[0], permisos_iniciales)
        self.assertIn(self.permisos[1], permisos_iniciales)
    
    def test_form_queryset_permisos(self):
        """Test que el queryset de permisos incluye todos los permisos"""
        form = RolForm()
        
        # Verificar que el queryset incluye todos los permisos
        permisos_queryset = form.fields['permisos'].queryset
        total_permisos = Permission.objects.count()
        self.assertEqual(permisos_queryset.count(), total_permisos)
    
    def test_form_labels(self):
        """Test etiquetas de los campos"""
        form = RolForm()
        
        # Verificar label del campo permisos
        self.assertEqual(form.fields['permisos'].label, 'Permisos')
    
    def test_form_meta_fields(self):
        """Test campos especificados en Meta"""
        form = RolForm()
        expected_fields = ['name', 'descripcion']
        
        # Verificar que los campos del modelo están en Meta.fields
        self.assertEqual(form._meta.fields, expected_fields)
        
        # Verificar que el modelo es correcto
        self.assertEqual(form._meta.model, Roles)
