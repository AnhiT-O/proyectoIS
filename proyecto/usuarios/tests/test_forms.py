import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from usuarios.forms import RegistroUsuarioForm, LoginForm, RecuperarPasswordForm, EstablecerPasswordForm
from usuarios.models import Usuario

User = get_user_model()

@pytest.mark.django_db
class TestLoginForm:
    
    def test_formulario_login_valido(self):
        """Prueba que el formulario de login sea válido con datos correctos"""
        # Crear un usuario activo para las pruebas
        Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            cedula_identidad='12345678',
            tipo_cedula='CI',
            first_name='Juan',
            last_name='Pérez',
            password='TestPass123!',
            is_active=True
        )
        
        form_data = {
            'username': 'testuser',
            'password': 'TestPass123!'
        }
        form = LoginForm(data=form_data)
        assert form.is_valid(), f"El formulario debería ser válido, errores: {form.errors}"
    
    def test_formulario_login_campos_vacios(self):
        """Prueba que el formulario de login no sea válido con campos vacíos"""
        form_data = {
            'username': '',
            'password': ''
        }
        form = LoginForm(data=form_data)
        assert not form.is_valid()
        assert 'username' in form.errors
        assert 'password' in form.errors
    
    def test_formulario_login_solo_username(self):
        """Prueba que el formulario de login no sea válido solo con username"""
        form_data = {
            'username': 'testuser',
            'password': ''
        }
        form = LoginForm(data=form_data)
        assert not form.is_valid()
        assert 'password' in form.errors
    
    def test_formulario_login_solo_password(self):
        """Prueba que el formulario de login no sea válido solo con password"""
        form_data = {
            'username': '',
            'password': 'TestPass123!'
        }
        form = LoginForm(data=form_data)
        assert not form.is_valid()
        assert 'username' in form.errors
    
    def test_formulario_login_atributos_widget(self):
        """Prueba que los widgets tengan los atributos CSS correctos"""
        form = LoginForm()
        
        # Verificar atributos del campo username
        username_widget = form.fields['username'].widget
        assert 'form-control' in username_widget.attrs.get('class', '')
        assert username_widget.attrs.get('placeholder') == 'Nombre de usuario'
        
        # Verificar atributos del campo password
        password_widget = form.fields['password'].widget
        assert 'form-control' in password_widget.attrs.get('class', '')
        assert password_widget.attrs.get('placeholder') == 'Contraseña'
    
    def test_formulario_login_mensajes_error_personalizados(self):
        """Prueba que los mensajes de error estén personalizados en español"""
        form = LoginForm()
        
        # Verificar mensajes de error personalizados
        assert 'Por favor, introduce un nombre de usuario y contraseña correctos' in form.error_messages['invalid_login']
        assert 'Esta cuenta está inactiva' in form.error_messages['inactive']

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


@pytest.mark.django_db
class TestRecuperarPasswordForm:
    
    def test_formulario_valido_con_email_activo(self):
        """Prueba que el formulario sea válido con email de usuario activo"""
        # Crear usuario activo
        Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            cedula_identidad='12345678',
            tipo_cedula='CI',
            first_name='Juan',
            last_name='Pérez',
            password='TestPass123!',
            is_active=True
        )
        
        form_data = {'email': 'test@example.com'}
        form = RecuperarPasswordForm(data=form_data)
        assert form.is_valid(), f"El formulario debería ser válido, errores: {form.errors}"
    
    def test_formulario_invalido_email_inexistente(self):
        """Prueba que el formulario no sea válido con email inexistente"""
        form_data = {'email': 'inexistente@example.com'}
        form = RecuperarPasswordForm(data=form_data)
        assert not form.is_valid()
        assert 'email' in form.errors
        assert 'No existe una cuenta activa asociada a este correo electrónico.' in form.errors['email']
    
    def test_formulario_invalido_usuario_inactivo(self):
        """Prueba que el formulario no sea válido con usuario inactivo"""
        # Crear usuario inactivo
        Usuario.objects.create_user(
            username='inactive',
            email='inactive@example.com',
            cedula_identidad='87654321',
            tipo_cedula='CI',
            first_name='María',
            last_name='González',
            password='TestPass123!',
            is_active=False
        )
        
        form_data = {'email': 'inactive@example.com'}
        form = RecuperarPasswordForm(data=form_data)
        assert not form.is_valid()
        assert 'email' in form.errors
        assert 'No existe una cuenta activa asociada a este correo electrónico.' in form.errors['email']
    
    def test_formulario_invalido_email_vacio(self):
        """Prueba que el formulario no sea válido con email vacío"""
        form_data = {'email': ''}
        form = RecuperarPasswordForm(data=form_data)
        assert not form.is_valid()
        assert 'email' in form.errors
    
    def test_formulario_invalido_email_formato_incorrecto(self):
        """Prueba que el formulario no sea válido con formato de email incorrecto"""
        form_data = {'email': 'email_invalido'}
        form = RecuperarPasswordForm(data=form_data)
        assert not form.is_valid()
        assert 'email' in form.errors
    
    def test_get_users_solo_usuarios_activos(self):
        """Prueba que get_users retorne solo usuarios activos"""
        # Crear usuario activo
        user_activo = Usuario.objects.create_user(
            username='activo',
            email='test@example.com',
            cedula_identidad='12345678',
            tipo_cedula='CI',
            is_active=True
        )
        
        # Crear usuario inactivo con el mismo email (no debería pasar en la realidad)
        Usuario.objects.create_user(
            username='inactivo',
            email='TEST@EXAMPLE.COM',  # Caso diferente para probar insensibilidad
            cedula_identidad='87654321',
            tipo_cedula='CI',
            is_active=False
        )
        
        form = RecuperarPasswordForm()
        users = list(form.get_users('test@example.com'))
        
        assert len(users) == 1
        assert users[0] == user_activo
        assert users[0].is_active
    
    def test_widget_atributos_css(self):
        """Prueba que el widget tenga los atributos CSS correctos"""
        form = RecuperarPasswordForm()
        
        email_widget = form.fields['email'].widget
        assert 'form-control' in email_widget.attrs.get('class', '')
        assert email_widget.attrs.get('placeholder') == 'Correo electrónico'
        assert email_widget.attrs.get('autofocus') is True


@pytest.mark.django_db
class TestEstablecerPasswordForm:
    
    def setup_method(self):
        """Configuración para cada test"""
        self.user = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            cedula_identidad='12345678',
            tipo_cedula='CI',
            first_name='Juan',
            last_name='Pérez',
            password='OldPassword123!',
            is_active=True
        )
    
    def test_formulario_valido_con_passwords_correctos(self):
        """Prueba que el formulario sea válido con contraseñas correctas"""
        form_data = {
            'new_password1': 'NewPassword123!',
            'new_password2': 'NewPassword123!'
        }
        form = EstablecerPasswordForm(user=self.user, data=form_data)
        assert form.is_valid(), f"El formulario debería ser válido, errores: {form.errors}"
    
    def test_formulario_invalido_password_corto(self):
        """Prueba que el formulario no sea válido con contraseña corta"""
        form_data = {
            'new_password1': 'Pass1!',
            'new_password2': 'Pass1!'
        }
        form = EstablecerPasswordForm(user=self.user, data=form_data)
        assert not form.is_valid()
        assert 'new_password1' in form.errors
        assert 'La contraseña debe tener más de 8 caracteres.' in form.errors['new_password1']
    
    def test_formulario_invalido_sin_caracter_especial(self):
        """Prueba que el formulario no sea válido sin caracter especial"""
        form_data = {
            'new_password1': 'NewPassword123',
            'new_password2': 'NewPassword123'
        }
        form = EstablecerPasswordForm(user=self.user, data=form_data)
        assert not form.is_valid()
        assert 'new_password1' in form.errors
        assert 'La contraseña debe contener al menos un caracter especial.' in form.errors['new_password1']
    
    def test_formulario_invalido_sin_numero(self):
        """Prueba que el formulario no sea válido sin número"""
        form_data = {
            'new_password1': 'NewPassword!',
            'new_password2': 'NewPassword!'
        }
        form = EstablecerPasswordForm(user=self.user, data=form_data)
        assert not form.is_valid()
        assert 'new_password1' in form.errors
        assert 'La contraseña debe contener al menos un número.' in form.errors['new_password1']
    
    def test_formulario_invalido_password_vacio(self):
        """Prueba que el formulario no sea válido con contraseña vacía"""
        form_data = {
            'new_password1': '',
            'new_password2': ''
        }
        form = EstablecerPasswordForm(user=self.user, data=form_data)
        assert not form.is_valid()
        assert 'new_password1' in form.errors
        # Django por defecto usa 'Este campo es obligatorio.' para campos vacíos
        assert 'Este campo es obligatorio.' in form.errors['new_password1']
    
    def test_formulario_invalido_passwords_no_coinciden(self):
        """Prueba que el formulario no sea válido con contraseñas que no coinciden"""
        form_data = {
            'new_password1': 'NewPassword123!',
            'new_password2': 'DifferentPassword123!'
        }
        form = EstablecerPasswordForm(user=self.user, data=form_data)
        assert not form.is_valid()
        assert 'new_password2' in form.errors
        # El error viene del SetPasswordForm base de Django
        assert form.errors['new_password2']
    
    def test_save_cambia_password(self):
        """Prueba que el método save cambie efectivamente la contraseña"""
        form_data = {
            'new_password1': 'NewPassword123!',
            'new_password2': 'NewPassword123!'
        }
        form = EstablecerPasswordForm(user=self.user, data=form_data)
        assert form.is_valid()
        
        # Verificar que la contraseña antigua funciona
        assert self.user.check_password('OldPassword123!')
        
        # Guardar la nueva contraseña
        form.save()
        
        # Verificar que la nueva contraseña funciona
        assert self.user.check_password('NewPassword123!')
        
        # Verificar que la contraseña antigua ya no funciona
        assert not self.user.check_password('OldPassword123!')
    
    def test_widget_atributos_css(self):
        """Prueba que los widgets tengan los atributos CSS correctos"""
        form = EstablecerPasswordForm(user=self.user)
        
        # Verificar atributos del campo new_password1
        password1_widget = form.fields['new_password1'].widget
        assert 'form-control' in password1_widget.attrs.get('class', '')
        assert password1_widget.attrs.get('placeholder') == 'Nueva contraseña'
        
        # Verificar atributos del campo new_password2
        password2_widget = form.fields['new_password2'].widget
        assert 'form-control' in password2_widget.attrs.get('class', '')
        assert password2_widget.attrs.get('placeholder') == 'Confirmar nueva contraseña'
    
    def test_labels_en_espanol(self):
        """Prueba que los labels estén en español"""
        form = EstablecerPasswordForm(user=self.user)
        
        assert form.fields['new_password1'].label == 'Nueva contraseña'
        assert form.fields['new_password2'].label == 'Confirmar nueva contraseña'
