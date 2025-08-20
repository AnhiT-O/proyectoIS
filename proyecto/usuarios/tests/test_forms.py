import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from usuarios.forms import RegistroUsuarioForm
from usuarios.models import Usuario

User = get_user_model()

@pytest.mark.django_db
class TestRegistroUsuarioForm:
    
    def test_formulario_valido_con_datos_correctos(self):
        """Prueba que el formulario sea válido con datos correctos"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert form.is_valid(), f"El formulario debería ser válido, errores: {form.errors}"
    
    def test_validacion_cedula_solo_numeros(self):
        """Prueba que la cédula solo acepte números"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': 'abc123',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'La cédula debe contener solo números.' in form.errors['cedula_identidad']
    
    def test_validacion_longitud_ci_minima(self):
        """Prueba validación de longitud mínima para CI"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '123',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'La Cédula de Identidad debe tener entre 4 y 12 dígitos.' in form.errors['cedula_identidad']
    
    def test_validacion_longitud_ci_maxima(self):
        """Prueba validación de longitud máxima para CI"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '1234567890123',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'La Cédula de Identidad debe tener entre 4 y 12 dígitos.' in form.errors['cedula_identidad']
    
    def test_validacion_longitud_ruc_minima(self):
        """Prueba validación de longitud mínima para RUC"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@example.com',
            'tipo_cedula': 'RUC',
            'cedula_identidad': '1234',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'El RUC debe tener entre 5 y 13 dígitos.' in form.errors['cedula_identidad']
    
    def test_validacion_longitud_ruc_maxima(self):
        """Prueba validación de longitud máxima para RUC"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@example.com',
            'tipo_cedula': 'RUC',
            'cedula_identidad': '12345678901234',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'El RUC debe tener entre 5 y 13 dígitos.' in form.errors['cedula_identidad']
    
    def test_validacion_cedula_duplicada_usuario_activo(self):
        """Prueba que no se permita cédula duplicada con usuario activo"""
        # Crear usuario activo existente
        Usuario.objects.create_user(
            username='existing_user',
            email='existing@example.com',
            cedula_identidad='12345678',
            tipo_cedula='CI',
            is_active=True
        )
        
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'Ya existe un usuario registrado con esta cédula.' in form.errors['cedula_identidad']
    
    def test_validacion_email_duplicado_usuario_activo(self):
        """Prueba que no se permita email duplicado con usuario activo"""
        # Crear usuario activo existente
        Usuario.objects.create_user(
            username='existing_user',
            email='juan@example.com',
            cedula_identidad='87654321',
            tipo_cedula='CI',
            is_active=True
        )
        
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'Ya existe un usuario registrado con este correo electrónico.' in form.errors['email']
    
    def test_validacion_email_duplicado_usuario_inactivo(self):
        """Prueba que no se permita email duplicado con usuario inactivo y muestre mensaje específico"""
        # Crear usuario inactivo existente
        Usuario.objects.create_user(
            username='inactive_user',
            email='juan@example.com',
            cedula_identidad='87654321',
            tipo_cedula='CI',
            is_active=False
        )
        
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'Una cuenta con este correo electrónico ya existe, pero no está activada. Revisa su bandeja de entrada' in form.errors['email']
    
    def test_permite_cedula_duplicada_usuario_inactivo(self):
        """Prueba que sí se permita cédula duplicada con usuario inactivo"""
        # Crear usuario inactivo existente
        Usuario.objects.create_user(
            username='inactive_user',
            email='inactive@example.com',
            cedula_identidad='12345678',
            tipo_cedula='CI',
            is_active=False
        )
        
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert form.is_valid(), f"El formulario debería ser válido con usuario inactivo, errores: {form.errors}"
    
    def test_validacion_password_longitud_minima(self):
        """Prueba validación de longitud mínima de contraseña"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'Test123!',
            'password2': 'Test123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'La contraseña debe tener más de 8 caracteres.' in form.errors['password1']
    
    def test_validacion_password_caracter_especial(self):
        """Prueba validación de caracter especial en contraseña"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'TestPass123',
            'password2': 'TestPass123'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'La contraseña debe contener al menos un caracter especial.' in form.errors['password1']
    
    def test_validacion_password_numero(self):
        """Prueba validación de número en contraseña"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'TestPassword!',
            'password2': 'TestPassword!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'La contraseña debe contener al menos un número.' in form.errors['password1']
    
    def test_validacion_passwords_no_coinciden(self):
        """Prueba validación de confirmación de contraseña"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'TestPass123!',
            'password2': 'TestPass456!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'Las contraseñas no coinciden.' in form.errors['password2']
    
    def test_cedula_obligatoria(self):
        """Prueba que la cédula sea obligatoria"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'La cédula es obligatoria.' in form.errors['cedula_identidad']
    
    def test_save_usuario_inactivo(self):
        """Prueba que el método save cree un usuario inactivo"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert form.is_valid()
        
        user = form.save()
        assert user.username == 'testuser'
        assert user.first_name == 'Juan'
        assert user.last_name == 'Pérez'
        assert user.email == 'juan@example.com'
        assert user.tipo_cedula == 'CI'
        assert user.cedula_identidad == '12345678'
        assert not user.is_active, "El usuario debería estar inactivo"
    
    def test_save_sin_commit(self):
        """Prueba que el método save funcione sin commit"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert form.is_valid()
        
        user = form.save(commit=False)
        assert user.pk is None, "El usuario no debería tener ID si no se hizo commit"
        assert user.email == 'juan@example.com'
