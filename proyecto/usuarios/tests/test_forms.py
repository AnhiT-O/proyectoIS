import pytest
from django.test import TestCase
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
    """Pruebas para el formulario de registro de usuarios."""
    
    def test_registro_exitoso_con_datos_validos(self):
        """Prueba 1: RegistroUsuarioForm: registro exitoso con datos válidos."""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'numero_documento': '12345678',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert form.is_valid()
        
        user = form.save()
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.numero_documento == '12345678'

    def test_error_cedula_no_numerica(self):
        """Prueba 2: RegistroUsuarioForm: error si la cédula no es numérica."""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'tipo_documento': 'CI',
            'numero_documento': 'abcd1234',  # No numérica
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'numero_documento' in form.errors
        assert 'El número de documento debe ser numérico.' in form.errors['numero_documento']

    def test_error_cedula_muy_corta(self):
        """Prueba 2: RegistroUsuarioForm: error si la cédula es muy corta."""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'tipo_documento': 'CI',
            'numero_documento': '123',  # Muy corta
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'numero_documento' in form.errors
        assert 'El número de documento debe tener al menos 4 dígitos.' in form.errors['numero_documento']

    def test_error_cedula_ya_existe(self):
        """Prueba 2: RegistroUsuarioForm: error si la cédula ya existe."""
        # Crear usuario existente
        existing_user = Usuario(
            username='existing',
            email='existing@example.com',
            first_name='Existing',
            last_name='User',
            tipo_documento='CI',
            numero_documento='87654321'
        )
        existing_user.set_password('existingpass')
        existing_user.save()
        
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'tipo_documento': 'CI',
            'numero_documento': '87654321',  # Ya existe
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'numero_documento' in form.errors

    def test_error_email_ya_registrado(self):
        """Prueba 3: RegistroUsuarioForm: error si el email ya está registrado."""
        # Crear usuario existente
        existing_user = Usuario(
            username='existing',
            email='test@example.com',
            first_name='Existing',
            last_name='User',
            tipo_documento='CI',
            numero_documento='87654321'
        )
        existing_user.set_password('existingpass')
        existing_user.save()
        
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',  # Ya existe
            'first_name': 'Test',
            'last_name': 'User',
            'tipo_documento': 'CI',
            'numero_documento': '12345678',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_error_email_invalido(self):
        """Prueba 3: RegistroUsuarioForm: error si el email es inválido."""
        form_data = {
            'username': 'testuser',
            'email': 'invalid-email',  # Email inválido
            'first_name': 'Test',
            'last_name': 'User',
            'tipo_documento': 'CI',
            'numero_documento': '12345678',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_error_passwords_no_coinciden(self):
        """Prueba 4: RegistroUsuarioForm: error si las contraseñas no coinciden."""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'tipo_documento': 'CI',
            'numero_documento': '12345678',
            'password1': 'TestPass123!',
            'password2': 'DifferentPass456!'  # No coincide
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'password2' in form.errors
        assert 'Las contraseñas no coinciden.' in form.errors['password2']

    def test_error_password_muy_corta(self):
        """Prueba 4: RegistroUsuarioForm: error si la contraseña no tiene más de 8 caracteres."""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'tipo_documento': 'CI',
            'numero_documento': '12345678',
            'password1': 'Test12!',  # 7 caracteres
            'password2': 'Test12!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'password1' in form.errors
        assert 'La contraseña debe tener más de 8 caracteres.' in form.errors['password1']

    def test_error_password_sin_numero(self):
        """Prueba 4: RegistroUsuarioForm: error si la contraseña no tiene número."""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'tipo_documento': 'CI',
            'numero_documento': '12345678',
            'password1': 'TestPassword!',  # Sin número
            'password2': 'TestPassword!'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'password1' in form.errors
        assert 'La contraseña debe contener al menos un número.' in form.errors['password1']

    def test_error_password_sin_caracter_especial(self):
        """Prueba 4: RegistroUsuarioForm: error si la contraseña no tiene caracter especial."""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'tipo_documento': 'CI',
            'numero_documento': '12345678',
            'password1': 'TestPassword123',  # Sin caracter especial
            'password2': 'TestPassword123'
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'password1' in form.errors
        assert 'La contraseña debe contener al menos un caracter especial.' in form.errors['password1']


@pytest.mark.django_db
class TestRecuperarPasswordForm:
    """Pruebas para el formulario de recuperación de contraseña."""
    
    def test_error_email_no_existe(self):
        """Prueba 5: RecuperarPasswordForm: error si el email no existe."""
        form_data = {
            'email': 'noexiste@example.com'
        }
        form = RecuperarPasswordForm(data=form_data)
        assert not form.is_valid()
        assert 'email' in form.errors
        assert 'No existe una cuenta activa asociada a este correo electrónico.' in form.errors['email']

    def test_error_usuario_inactivo(self):
        """Prueba 5: RecuperarPasswordForm: error si el usuario está inactivo."""
        # Crear usuario inactivo
        inactive_user = Usuario(
            username='inactiveuser',
            email='inactive@example.com',
            first_name='Inactive',
            last_name='User',
            tipo_documento='CI',
            numero_documento='12345678',
            is_active=False
        )
        inactive_user.set_password('password123')
        inactive_user.save()
        
        form_data = {
            'email': 'inactive@example.com'
        }
        form = RecuperarPasswordForm(data=form_data)
        assert not form.is_valid()
        assert 'email' in form.errors
        assert 'No existe una cuenta activa asociada a este correo electrónico.' in form.errors['email']


@pytest.mark.django_db
class TestEstablecerPasswordForm:
    """Pruebas para el formulario de establecer nueva contraseña."""
    
    def test_error_password_no_cumple_requisitos_longitud(self):
        """Prueba 6: EstablecerPasswordForm: error si la nueva contraseña no tiene más de 8 caracteres."""
        user = Usuario(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            tipo_documento='CI',
            numero_documento='12345678'
        )
        user.set_password('oldpassword')
        user.save()
        
        form_data = {
            'new_password1': 'Short1!',  # 7 caracteres
            'new_password2': 'Short1!'
        }
        form = EstablecerPasswordForm(user=user, data=form_data)
        assert not form.is_valid()
        assert 'new_password1' in form.errors
        assert 'La contraseña debe tener más de 8 caracteres.' in form.errors['new_password1']

    def test_error_password_sin_numero(self):
        """Prueba 6: EstablecerPasswordForm: error si la nueva contraseña no tiene número."""
        user = Usuario(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            tipo_documento='CI',
            numero_documento='12345678'
        )
        user.set_password('oldpassword')
        user.save()
        
        form_data = {
            'new_password1': 'NewPassword!',  # Sin número
            'new_password2': 'NewPassword!'
        }
        form = EstablecerPasswordForm(user=user, data=form_data)
        assert not form.is_valid()
        assert 'new_password1' in form.errors
        assert 'La contraseña debe contener al menos un número.' in form.errors['new_password1']

    def test_error_password_sin_caracter_especial(self):
        """Prueba 6: EstablecerPasswordForm: error si la nueva contraseña no tiene caracter especial."""
        user = Usuario(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            tipo_documento='CI',
            numero_documento='12345678'
        )
        user.set_password('oldpassword')
        user.save()
        
        form_data = {
            'new_password1': 'NewPassword123',  # Sin caracter especial
            'new_password2': 'NewPassword123'
        }
        form = EstablecerPasswordForm(user=user, data=form_data)
        assert not form.is_valid()
        assert 'new_password1' in form.errors
        assert 'La contraseña debe contener al menos un caracter especial.' in form.errors['new_password1']


@pytest.mark.django_db
class TestAsignarRolForm:
    """Pruebas para el formulario de asignación de roles."""
    
    def test_solo_muestra_roles_no_asignados_y_no_administrador(self):
        """Prueba 7: AsignarRolForm: solo muestra roles no asignados y no permite asignar "Administrador"."""
        # Crear roles si no existen
        operador_role, _ = Group.objects.get_or_create(name='Operador')
        supervisor_role, _ = Group.objects.get_or_create(name='Supervisor')
        admin_role, _ = Group.objects.get_or_create(name='Administrador')
        
        # Crear usuario con rol Operador
        user = Usuario(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            numero_documento='12345678'
        )
        user.set_password('password')
        user.save()
        user.groups.add(operador_role)
        
        form = AsignarRolForm(usuario=user)
        
        # Verificar que solo muestra Supervisor (no Operador que ya tiene, ni Administrador)
        queryset = form.fields['rol'].queryset
        role_names = list(queryset.values_list('name', flat=True))
        
        assert 'Supervisor' in role_names
        assert 'Operador' not in role_names  # Ya lo tiene asignado
        assert 'Administrador' not in role_names  # Excluido por defecto


@pytest.mark.django_db
class TestAsignarClienteForm:
    """Pruebas para el formulario de asignación de clientes."""
    
    def test_solo_muestra_clientes_no_asignados_y_etiqueta_personalizada(self):
        """Prueba 8: AsignarClienteForm: solo muestra clientes no asignados y etiqueta personalizada."""
        # Crear clientes
        cliente1 = Cliente.objects.create(
            nombre='Cliente 1',
            tipo_documento='CI',
            numero_documento='12345678',
            correo_electronico='cliente1@example.com',
            telefono='123456789',
            tipo='F',
            direccion='Direccion 1',
            ocupacion='Ocupacion 1'
        )
        cliente2 = Cliente.objects.create(
            nombre='Cliente 2',
            tipo_documento='CI',
            numero_documento='87654321',
            correo_electronico='cliente2@example.com',
            telefono='987654321',
            tipo='F',
            direccion='Direccion 2',
            ocupacion='Ocupacion 2'
        )
        
        # Crear usuario
        user = Usuario(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            tipo_documento='CI',
            numero_documento='11111111'
        )
        user.set_password('password')
        user.save()
        
        # Asignar cliente1 al usuario
        user.clientes_operados.add(cliente1)
        
        form = AsignarClienteForm(usuario=user)
        
        # Verificar que solo muestra cliente2 (cliente1 ya está asignado)
        queryset = form.fields['clientes'].queryset
        clientes_disponibles = list(queryset.values_list('nombre', flat=True))
        
        assert 'Cliente 2' in clientes_disponibles
        assert 'Cliente 1' not in clientes_disponibles  # Ya está asignado
        
        # Verificar etiqueta personalizada
        label_func = form.fields['clientes'].label_from_instance
        etiqueta = label_func(cliente2)
        assert etiqueta == f"{cliente2.nombre} ({cliente2.numero_documento})"