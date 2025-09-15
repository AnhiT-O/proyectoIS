import pytest
from django.test import TestCase
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from roles.models import Roles
from roles.forms import RolForm, PermissionCheckboxSelectMultiple


@pytest.mark.django_db
class TestRolForm(TestCase):
    """Pruebas para el formulario RolForm"""

    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.valid_data = {
            'name': 'Rol Test',
            'descripcion': 'Descripción del rol de prueba'
        }
        
        # Crear algunos permisos para las pruebas
        content_type = ContentType.objects.get_for_model(Roles)
        self.permission1 = Permission.objects.get_or_create(
            codename='test_permission1',
            name='Permiso de prueba 1',
            content_type=content_type
        )[0]
        self.permission2 = Permission.objects.get_or_create(
            codename='test_permission2', 
            name='Permiso de prueba 2',
            content_type=content_type
        )[0]

    def test_formulario_valido_con_datos_minimos(self):
        """Prueba que el formulario es válido con datos mínimos requeridos"""
        data = {'name': 'Rol Mínimo'}
        form = RolForm(data=data)
        
        assert form.is_valid(), f"Se esperaba que el formulario fuera válido, pero tiene errores: {form.errors}"

    def test_formulario_valido_con_datos_completos(self):
        """Prueba que el formulario es válido con todos los datos"""
        form = RolForm(data=self.valid_data)
        
        assert form.is_valid(), f"Se esperaba que el formulario fuera válido, pero tiene errores: {form.errors}"

    def test_campo_name_requerido(self):
        """Prueba que el campo name es requerido"""
        data = {'descripcion': 'Solo descripción'}
        form = RolForm(data=data)
        
        assert not form.is_valid(), "Se esperaba que el formulario fuera inválido sin el campo name"
        assert 'name' in form.errors, f"Se esperaba error en el campo 'name', pero los errores son: {form.errors}"
        assert 'Debes ingresar un nombre.' in form.errors['name'], f"Se esperaba mensaje específico de error, pero se obtuvo: {form.errors['name']}"

    def test_campo_name_longitud_maxima(self):
        """Prueba que el campo name respeta la longitud máxima"""
        data = {
            'name': 'x' * 101,  # Excede los 100 caracteres máximos
            'descripcion': 'Descripción válida'
        }
        form = RolForm(data=data)
        
        assert not form.is_valid(), "Se esperaba que el formulario fuera inválido con nombre muy largo"
        assert 'name' in form.errors, f"Se esperaba error en el campo 'name', pero los errores son: {form.errors}"
        assert 'no puede exceder los 100 caracteres' in str(form.errors['name']), f"Se esperaba mensaje de longitud máxima, pero se obtuvo: {form.errors['name']}"

    def test_campo_descripcion_opcional(self):
        """Prueba que el campo descripcion es opcional"""
        data = {'name': 'Rol Sin Descripción'}
        form = RolForm(data=data)
        
        assert form.is_valid(), f"Se esperaba que el formulario fuera válido sin descripción, pero tiene errores: {form.errors}"

    def test_campo_descripcion_vacio_valido(self):
        """Prueba que el campo descripcion puede estar vacío"""
        data = {
            'name': 'Rol Descripción Vacía',
            'descripcion': ''
        }
        form = RolForm(data=data)
        
        assert form.is_valid(), f"Se esperaba que el formulario fuera válido con descripción vacía, pero tiene errores: {form.errors}"

    def test_campo_permisos_opcional(self):
        """Prueba que el campo permisos es opcional"""
        form = RolForm(data=self.valid_data)
        
        assert form.is_valid(), f"Se esperaba que el formulario fuera válido sin permisos, pero tiene errores: {form.errors}"

    def test_guardar_formulario_sin_permisos(self):
        """Prueba que se puede guardar el formulario sin permisos"""
        form = RolForm(data=self.valid_data)
        
        assert form.is_valid(), f"Se esperaba que el formulario fuera válido, pero tiene errores: {form.errors}"
        
        rol = form.save()
        assert rol.name == 'Rol Test', f"Se esperaba nombre 'Rol Test', pero se obtuvo '{rol.name}'"
        assert rol.descripcion == 'Descripción del rol de prueba', f"Se esperaba la descripción del formulario, pero se obtuvo '{rol.descripcion}'"
        assert rol.permissions.count() == 0, f"Se esperaban 0 permisos, pero se encontraron {rol.permissions.count()}"

    def test_guardar_formulario_con_permisos(self):
        """Prueba que se puede guardar el formulario con permisos"""
        data = self.valid_data.copy()
        data['permisos'] = [self.permission1.pk, self.permission2.pk]
        
        form = RolForm(data=data)
        
        assert form.is_valid(), f"Se esperaba que el formulario fuera válido, pero tiene errores: {form.errors}"
        
        rol = form.save()
        permisos_asignados = list(rol.permissions.all())
        
        assert self.permission1 in permisos_asignados, f"Se esperaba que {self.permission1} estuviera en los permisos asignados"
        assert self.permission2 in permisos_asignados, f"Se esperaba que {self.permission2} estuviera en los permisos asignados"
        assert len(permisos_asignados) == 2, f"Se esperaban 2 permisos asignados, pero se encontraron {len(permisos_asignados)}"

    def test_inicializacion_con_instancia_existente(self):
        """Prueba que el formulario se inicializa correctamente con una instancia existente"""
        # Crear un rol con permisos
        rol = Roles.objects.create(**self.valid_data)
        rol.permissions.add(self.permission1)
        
        form = RolForm(instance=rol)
        
        assert form.initial['name'] == rol.name, f"Se esperaba nombre inicial '{rol.name}', pero se obtuvo '{form.initial.get('name')}'"
        assert form.initial['descripcion'] == rol.descripcion, f"Se esperaba descripción inicial '{rol.descripcion}', pero se obtuvo '{form.initial.get('descripcion')}'"
        
        # Verificar que los permisos iniciales están establecidos
        permisos_iniciales = form.fields['permisos'].initial
        assert self.permission1 in permisos_iniciales, f"Se esperaba que {self.permission1} estuviera en los permisos iniciales"

    def test_actualizar_rol_existente(self):
        """Prueba que se puede actualizar un rol existente"""
        # Crear rol inicial
        rol = Roles.objects.create(name='Rol Original', descripcion='Descripción original')
        rol.permissions.add(self.permission1)
        
        # Datos actualizados
        data_actualizada = {
            'name': 'Rol Actualizado',
            'descripcion': 'Descripción actualizada',
            'permisos': [self.permission2.pk]
        }
        
        form = RolForm(data=data_actualizada, instance=rol)
        
        assert form.is_valid(), f"Se esperaba que el formulario fuera válido, pero tiene errores: {form.errors}"
        
        rol_actualizado = form.save()
        
        assert rol_actualizado.name == 'Rol Actualizado', f"Se esperaba nombre actualizado 'Rol Actualizado', pero se obtuvo '{rol_actualizado.name}'"
        assert rol_actualizado.descripcion == 'Descripción actualizada', f"Se esperaba descripción actualizada, pero se obtuvo '{rol_actualizado.descripcion}'"
        
        permisos_actuales = list(rol_actualizado.permissions.all())
        assert self.permission2 in permisos_actuales, f"Se esperaba que {self.permission2} estuviera en los permisos actuales"
        assert self.permission1 not in permisos_actuales, f"Se esperaba que {self.permission1} NO estuviera en los permisos actuales"

    def test_queryset_permisos_excluye_predeterminados(self):
        """Prueba que el queryset de permisos excluye los permisos predeterminados de Django"""
        form = RolForm()
        queryset_permisos = form.fields['permisos'].queryset
        
        # Verificar que no hay permisos que empiecen con add_, change_, delete_, view_
        codenames_excluidos = ['add_', 'change_', 'delete_', 'view_']
        
        for permission in queryset_permisos:
            for prefix in codenames_excluidos:
                assert not permission.codename.startswith(prefix), f"Se encontró permiso predeterminado '{permission.codename}' que debería estar excluido"

    def test_meta_fields_configuracion(self):
        """Prueba que la configuración Meta del formulario es correcta"""
        form = RolForm()
        
        expected_fields = ['name', 'descripcion']
        assert form.Meta.fields == expected_fields, f"Se esperaban campos {expected_fields}, pero se obtuvo {form.Meta.fields}"
        assert form.Meta.model == Roles, f"Se esperaba modelo Roles, pero se obtuvo {form.Meta.model}"

    def test_widgets_css_classes(self):
        """Prueba que los campos tienen las clases CSS correctas"""
        form = RolForm()
        
        name_widget = form.fields['name'].widget
        assert 'form-control' in name_widget.attrs.get('class', ''), f"Se esperaba clase 'form-control' en el campo name, pero se obtuvo '{name_widget.attrs}'"
        
        descripcion_widget = form.fields['descripcion'].widget
        assert 'form-control' in descripcion_widget.attrs.get('class', ''), f"Se esperaba clase 'form-control' en el campo descripcion, pero se obtuvo '{descripcion_widget.attrs}'"
        assert descripcion_widget.attrs.get('rows') == 4, f"Se esperaban 4 filas en el textarea, pero se obtuvo {descripcion_widget.attrs.get('rows')}"


@pytest.mark.django_db
class TestPermissionCheckboxSelectMultiple(TestCase):
    """Pruebas para el widget personalizado PermissionCheckboxSelectMultiple"""

    def setUp(self):
        """Configuración inicial para las pruebas"""
        content_type = ContentType.objects.get_for_model(Roles)
        self.permission = Permission.objects.get_or_create(
            codename='test_permission_widget',
            name='Permiso de prueba para widget',
            content_type=content_type
        )[0]

    def test_widget_personaliza_etiquetas(self):
        """Prueba que el widget personaliza correctamente las etiquetas de los permisos"""
        widget = PermissionCheckboxSelectMultiple()
        
        # Simular la creación de una opción
        option = widget.create_option(
            name='permisos',
            value=self.permission.pk,
            label=self.permission.codename,  # Etiqueta por defecto sería el codename
            selected=False,
            index=0
        )
        
        # La etiqueta debería ser el name del permiso, no el codename
        assert option['label'] == self.permission.name, f"Se esperaba etiqueta '{self.permission.name}', pero se obtuvo '{option['label']}'"

    def test_widget_maneja_valor_none(self):
        """Prueba que el widget maneja correctamente valores None"""
        widget = PermissionCheckboxSelectMultiple()
        
        option = widget.create_option(
            name='permisos',
            value=None,
            label='Etiqueta original',
            selected=False,
            index=0
        )
        
        # Con valor None, debería mantener la etiqueta original
        assert option['label'] == 'Etiqueta original', f"Se esperaba etiqueta original, pero se obtuvo '{option['label']}'"

    def test_widget_maneja_permiso_inexistente(self):
        """Prueba que el widget maneja correctamente permisos que no existen"""
        widget = PermissionCheckboxSelectMultiple()
        
        option = widget.create_option(
            name='permisos',
            value=99999,  # ID que no existe
            label='Etiqueta original',
            selected=False,
            index=0
        )
        
        # Con permiso inexistente, debería mantener la etiqueta original
        assert option['label'] == 'Etiqueta original', f"Se esperaba etiqueta original para permiso inexistente, pero se obtuvo '{option['label']}'"