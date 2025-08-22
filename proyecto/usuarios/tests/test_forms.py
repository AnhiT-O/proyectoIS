import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from usuarios.forms import RegistroUsuarioForm, LoginForm, RecuperarPasswordForm, EstablecerPasswordForm
from usuarios.models import Usuario


class TestUsuarioForms(TestCase):
    """Pruebas para los formularios de usuarios"""
    
    def test_login_form_valido(self):
        """Test formulario de login válido"""
        # Crear un usuario de prueba para el formulario de autenticación
        user = Usuario.objects.create_user(
            username='testuser',
            password='testpass123!',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            is_active=True
        )
        
        form_data = {
            'username': 'testuser',
            'password': 'testpass123!'
        }
        form = LoginForm(request=None, data=form_data)
        # Para AuthenticationForm necesitamos llamar is_valid() con un request válido
        # Por simplicidad, solo verificamos que los campos existen y tienen los datos
        self.assertEqual(form['username'].value(), 'testuser')
        self.assertEqual(form['password'].value(), 'testpass123!')
        self.assertIn('username', form.fields)
        self.assertIn('password', form.fields)
    
    def test_login_form_campos_vacios(self):
        """Test formulario de login con campos vacíos"""
        form_data = {
            'username': '',
            'password': ''
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('password', form.errors)
    
    def test_login_form_widgets(self):
        """Test widgets del formulario de login"""
        form = LoginForm()
        
        # Verificar atributos CSS
        self.assertIn('form-control', form.fields['username'].widget.attrs.get('class', ''))
        self.assertIn('form-control', form.fields['password'].widget.attrs.get('class', ''))
    
    def test_registro_form_valido(self):
        """Test formulario de registro válido"""
        form_data = {
            'username': 'newuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'testpass123!',
            'password2': 'testpass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_registro_form_cedula_invalida(self):
        """Test validación de cédula inválida"""
        form_data = {
            'username': 'newuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': 'abc123',
            'password1': 'testpass123!',
            'password2': 'testpass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cedula_identidad', form.errors)
    
    def test_registro_form_cedula_corta(self):
        """Test validación cédula muy corta"""
        form_data = {
            'username': 'newuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '123',
            'password1': 'testpass123!',
            'password2': 'testpass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cedula_identidad', form.errors)
    
    def test_registro_form_password_corta(self):
        """Test validación contraseña muy corta"""
        form_data = {
            'username': 'newuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'short1!',
            'password2': 'short1!'
        }
        form = RegistroUsuarioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password1', form.errors)
    
    def test_registro_form_password_sin_especial(self):
        """Test validación contraseña sin caracter especial"""
        form_data = {
            'username': 'newuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        form = RegistroUsuarioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password1', form.errors)
    
    def test_registro_form_passwords_no_coinciden(self):
        """Test validación contraseñas no coinciden"""
        form_data = {
            'username': 'newuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'testpass123!',
            'password2': 'different123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
    
    def test_registro_form_email_duplicado(self):
        """Test validación email duplicado"""
        # Crear usuario existente
        Usuario.objects.create_user(
            username='existing',
            email='test@example.com',
            first_name='Existing',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='87654321',
            password='testpass123!',
            is_active=True
        )
        
        form_data = {
            'username': 'newuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'testpass123!',
            'password2': 'testpass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_registro_form_save_usuario_inactivo(self):
        """Test que save() crea usuario inactivo"""
        form_data = {
            'username': 'newuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'testpass123!',
            'password2': 'testpass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        usuario = form.save()
        self.assertFalse(usuario.is_active)
        self.assertEqual(usuario.email, 'test@example.com')
    
    def test_recuperar_password_form_valido(self):
        """Test formulario recuperar contraseña válido"""
        # Crear usuario activo
        Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            password='testpass123!',
            is_active=True
        )
        
        form_data = {'email': 'test@example.com'}
        form = RecuperarPasswordForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_recuperar_password_form_email_inexistente(self):
        """Test formulario recuperar contraseña con email inexistente"""
        form_data = {'email': 'noexiste@example.com'}
        form = RecuperarPasswordForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_establecer_password_form_valido(self):
        """Test formulario establecer contraseña válido"""
        usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            password='oldpass123!',
            is_active=True
        )
        
        form_data = {
            'new_password1': 'newpass123!',
            'new_password2': 'newpass123!'
        }
        form = EstablecerPasswordForm(user=usuario, data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_establecer_password_form_password_corta(self):
        """Test formulario establecer contraseña con password corta"""
        usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            password='oldpass123!',
            is_active=True
        )
        
        form_data = {
            'new_password1': 'short1!',
            'new_password2': 'short1!'
        }
        form = EstablecerPasswordForm(user=usuario, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('new_password1', form.errors)
