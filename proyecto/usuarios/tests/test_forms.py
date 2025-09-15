import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from usuarios.forms import (
    RegistroUsuarioForm, 
    RecuperarPasswordForm, 
    EstablecerPasswordForm,
    AsignarRolForm,
    AsignarClienteForm
)
from usuarios.models import Usuario
from clientes.models import Cliente


@pytest.mark.django_db
class TestRegistroUsuarioForm:
    """Pruebas unitarias para el formulario RegistroUsuarioForm"""

    def test_formulario_valido_con_datos_correctos(self):
        """Test que verifica que el formulario es válido con datos correctos"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Perez',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'password123!',
            'password2': 'password123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        
        assert form.is_valid(), f"El formulario debería ser válido. Errores: {form.errors}"

    def test_username_requerido(self):
        """Test que verifica que username es requerido"""
        form_data = {
            'first_name': 'Juan',
            'last_name': 'Perez',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'password123!',
            'password2': 'password123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido sin username"
        assert 'username' in form.errors, "Debería haber un error en el campo username"
        assert 'El nombre de usuario es obligatorio.' in str(form.errors['username']), "El mensaje de error no es el esperado"

    def test_email_requerido(self):
        """Test que verifica que email es requerido"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Perez',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'password123!',
            'password2': 'password123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido sin email"
        assert 'email' in form.errors, "Debería haber un error en el campo email"
        assert 'El correo electrónico es obligatorio.' in str(form.errors['email']), "El mensaje de error no es el esperado"

    def test_email_formato_invalido(self):
        """Test que verifica validación de formato de email"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Perez',
            'email': 'email_invalido',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'password123!',
            'password2': 'password123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con email inválido"
        assert 'email' in form.errors, "Debería haber un error en el campo email"
        assert 'Introduce un correo electrónico válido.' in str(form.errors['email']), "El mensaje de error no es el esperado"

    def test_first_name_requerido(self):
        """Test que verifica que first_name es requerido"""
        form_data = {
            'username': 'testuser',
            'last_name': 'Perez',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'password123!',
            'password2': 'password123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido sin first_name"
        assert 'first_name' in form.errors, "Debería haber un error en el campo first_name"
        assert 'El nombre es obligatorio.' in str(form.errors['first_name']), "El mensaje de error no es el esperado"

    def test_last_name_requerido(self):
        """Test que verifica que last_name es requerido"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'password123!',
            'password2': 'password123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido sin last_name"
        assert 'last_name' in form.errors, "Debería haber un error en el campo last_name"
        assert 'El apellido es obligatorio.' in str(form.errors['last_name']), "El mensaje de error no es el esperado"

    def test_cedula_identidad_requerida(self):
        """Test que verifica que cedula_identidad es requerida"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Perez',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'password1': 'password123!',
            'password2': 'password123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido sin cedula_identidad"
        assert 'cedula_identidad' in form.errors, "Debería haber un error en el campo cedula_identidad"
        assert 'La cédula de identidad es obligatoria.' in str(form.errors['cedula_identidad']), "El mensaje de error no es el esperado"

    def test_cedula_identidad_solo_numeros(self):
        """Test que verifica que cedula_identidad debe ser numérica"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Perez',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': 'abc123',
            'password1': 'password123!',
            'password2': 'password123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con cedula no numérica"
        assert 'cedula_identidad' in form.errors, "Debería haber un error en el campo cedula_identidad"
        assert 'La cédula de identidad debe ser numérica.' in str(form.errors['cedula_identidad']), "El mensaje de error no es el esperado"

    def test_cedula_identidad_minimo_digitos(self):
        """Test que verifica que cedula_identidad debe tener al menos 4 dígitos"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Perez',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '123',
            'password1': 'password123!',
            'password2': 'password123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con cedula muy corta"
        assert 'cedula_identidad' in form.errors, "Debería haber un error en el campo cedula_identidad"
        assert 'La cédula de identidad debe tener al menos 4 dígitos.' in str(form.errors['cedula_identidad']), "El mensaje de error no es el esperado"

    def test_password_longitud_minima(self):
        """Test que verifica que password1 debe tener más de 8 caracteres"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Perez',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'pass123!',
            'password2': 'pass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con password muy corta"
        assert 'password1' in form.errors, "Debería haber un error en el campo password1"
        assert 'La contraseña debe tener más de 8 caracteres.' in str(form.errors['password1']), "El mensaje de error no es el esperado"

    def test_password_sin_caracter_especial(self):
        """Test que verifica que password1 debe contener un caracter especial"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Perez',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'password123',
            'password2': 'password123'
        }
        form = RegistroUsuarioForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido sin caracter especial"
        assert 'password1' in form.errors, "Debería haber un error en el campo password1"
        assert 'La contraseña debe contener al menos un caracter especial.' in str(form.errors['password1']), "El mensaje de error no es el esperado"

    def test_password_sin_numero(self):
        """Test que verifica que password1 debe contener un número"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Perez',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'password!',
            'password2': 'password!'
        }
        form = RegistroUsuarioForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido sin número"
        assert 'password1' in form.errors, "Debería haber un error en el campo password1"
        assert 'La contraseña debe contener al menos un número.' in str(form.errors['password1']), "El mensaje de error no es el esperado"

    def test_passwords_no_coinciden(self):
        """Test que verifica que password1 y password2 deben coincidir"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Perez',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'password123!',
            'password2': 'password456!'
        }
        form = RegistroUsuarioForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con passwords diferentes"
        assert 'password2' in form.errors, "Debería haber un error en el campo password2"
        assert 'Las contraseñas no coinciden.' in str(form.errors['password2']), "El mensaje de error no es el esperado"

    def test_save_method(self):
        """Test que verifica que el método save funciona correctamente"""
        form_data = {
            'username': 'testuser',
            'first_name': 'Juan',
            'last_name': 'Perez',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'password123!',
            'password2': 'password123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        
        assert form.is_valid(), f"El formulario debería ser válido. Errores: {form.errors}"
        
        user = form.save()
        
        assert user.username == 'testuser', "El username no se guardó correctamente"
        assert user.email == 'test@example.com', "El email no se guardó correctamente"
        assert user.first_name == 'Juan', "El first_name no se guardó correctamente"
        assert user.last_name == 'Perez', "El last_name no se guardó correctamente"
        assert user.tipo_cedula == 'CI', "El tipo_cedula no se guardó correctamente"
        assert user.cedula_identidad == '12345678', "La cedula_identidad no se guardó correctamente"


@pytest.mark.django_db
class TestRecuperarPasswordForm:
    """Pruebas unitarias para el formulario RecuperarPasswordForm"""

    def test_email_requerido(self):
        """Test que verifica que email es requerido"""
        form_data = {}
        form = RecuperarPasswordForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido sin email"
        assert 'email' in form.errors, "Debería haber un error en el campo email"
        assert 'El correo electrónico es obligatorio.' in str(form.errors['email']), "El mensaje de error no es el esperado"

    def test_email_formato_invalido(self):
        """Test que verifica validación de formato de email"""
        form_data = {'email': 'email_invalido'}
        form = RecuperarPasswordForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con email inválido"
        assert 'email' in form.errors, "Debería haber un error en el campo email"
        assert 'Ingrese un correo electrónico válido.' in str(form.errors['email']), "El mensaje de error no es el esperado"

    def test_email_usuario_inexistente(self):
        """Test que verifica validación para usuario inexistente"""
        form_data = {'email': 'noexiste@example.com'}
        form = RecuperarPasswordForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con email inexistente"
        assert 'email' in form.errors, "Debería haber un error en el campo email"
        assert 'No existe una cuenta activa asociada a este correo electrónico.' in str(form.errors['email']), "El mensaje de error no es el esperado"
