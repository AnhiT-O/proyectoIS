import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from .models import Usuario

@pytest.fixture
def usuario_data():
    """Fixture con datos base para crear usuarios"""
    return {
        'first_name': 'Juan',
        'last_name': 'Pérez',
        'username': 'jperez',
        'tipo_cedula': 'CI',
        'cedula_identidad': '12345678',
        'email': 'juan.perez@email.com',
        'password': 'testpass123'
    }

@pytest.mark.django_db
def test_crear_usuario_exitoso(usuario_data):
    """Prueba la creación exitosa de un usuario"""
    usuario = Usuario.objects.create_user(**usuario_data)
    
    assert usuario.first_name == 'Juan'
    assert usuario.last_name == 'Pérez'
    assert usuario.username == 'jperez'
    assert usuario.tipo_cedula == 'CI'
    assert usuario.cedula_identidad == '12345678'
    assert usuario.email == 'juan.perez@email.com'
    assert usuario.check_password('testpass123')

@pytest.mark.django_db
def test_crear_usuario_con_ruc(usuario_data):
    """Prueba la creación de usuario con tipo de cédula RUC"""
    usuario_data['tipo_cedula'] = 'RUC'
    usuario = Usuario.objects.create_user(**usuario_data)
    
    assert usuario.tipo_cedula == 'RUC'

@pytest.mark.django_db
def test_nombre_usuario_unico(usuario_data):
    """Prueba que el nombre de usuario debe ser único"""
    Usuario.objects.create_user(**usuario_data)
    
    # Intentar crear otro usuario con el mismo username
    usuario_data_duplicado = usuario_data.copy()
    usuario_data_duplicado['email'] = 'otro@email.com'
    usuario_data_duplicado['cedula_identidad'] = '87654321'
    
    with pytest.raises(IntegrityError):
        Usuario.objects.create_user(**usuario_data_duplicado)

@pytest.mark.django_db
def test_cedula_identidad_unica(usuario_data):
    """Prueba que la cédula de identidad debe ser única"""
    Usuario.objects.create_user(**usuario_data)
    
    # Intentar crear otro usuario con la misma cédula
    usuario_data_duplicado = usuario_data.copy()
    usuario_data_duplicado['username'] = 'otronombre'
    usuario_data_duplicado['email'] = 'otro@email.com'
    
    with pytest.raises(IntegrityError):
        Usuario.objects.create_user(**usuario_data_duplicado)

@pytest.mark.django_db
def test_correo_electronico_unico(usuario_data):
    """Prueba que el correo electrónico debe ser único"""
    Usuario.objects.create_user(**usuario_data)
    
    # Intentar crear otro usuario con el mismo correo
    usuario_data_duplicado = usuario_data.copy()
    usuario_data_duplicado['username'] = 'otronombre'
    usuario_data_duplicado['cedula_identidad'] = '87654321'
    
    with pytest.raises(IntegrityError):
        Usuario.objects.create_user(**usuario_data_duplicado)

@pytest.mark.django_db
def test_str_method(usuario_data):
    """Prueba el método __str__ del modelo"""
    usuario = Usuario.objects.create_user(**usuario_data)
    expected_str = "Juan Pérez (jperez)"
    
    assert str(usuario) == expected_str

def test_username_field():
    """Prueba que USERNAME_FIELD esté configurado correctamente"""
    assert Usuario.USERNAME_FIELD == 'username'

def test_required_fields():
    """Prueba que REQUIRED_FIELDS contenga los campos esperados"""
    expected_fields = ['email', 'first_name', 'last_name', 'tipo_cedula', 'cedula_identidad']
    assert Usuario.REQUIRED_FIELDS == expected_fields

def test_meta_configuracion():
    """Prueba la configuración de Meta del modelo"""
    assert Usuario._meta.db_table == 'usuarios'
    assert Usuario._meta.verbose_name == 'Usuario'
    assert Usuario._meta.verbose_name_plural == 'Usuarios'

def test_tipo_cedula_choices():
    """Prueba que las opciones de tipo_cedula sean correctas"""
    expected_choices = [
        ('RUC', 'Registro Único de Contribuyente'),
        ('CI', 'Cédula de Identidad'),
    ]
    
    field = Usuario._meta.get_field('tipo_cedula')
    assert field.choices == expected_choices

@pytest.mark.django_db
def test_campos_max_length(usuario_data):
    """Prueba las longitudes máximas de los campos"""
    usuario = Usuario.objects.create_user(**usuario_data)
    
    first_name_field = usuario._meta.get_field('first_name')
    last_name_field = usuario._meta.get_field('last_name')
    username_field = usuario._meta.get_field('username')
    tipo_cedula_field = usuario._meta.get_field('tipo_cedula')
    cedula_field = usuario._meta.get_field('cedula_identidad')
    
    assert first_name_field.max_length == 150
    assert last_name_field.max_length == 150
    assert username_field.max_length == 150
    assert tipo_cedula_field.max_length == 3
    assert cedula_field.max_length == 8

@pytest.mark.django_db
def test_campos_requeridos_validacion():
    """Prueba que los campos requeridos no puedan estar vacíos"""
    with pytest.raises(ValidationError):
        usuario = Usuario(
            username='test',
            email='',  # Email vacío
            password='testpass123'
        )
        usuario.full_clean()  # Esto ejecuta las validaciones del modelo

@pytest.mark.django_db
def test_cedula_identidad_max_length():
    """Prueba que la cédula no pueda exceder 8 caracteres"""
    usuario_data = {
        'first_name': 'Test',
        'last_name': 'User',
        'username': 'testuser',
        'tipo_cedula': 'CI',
        'cedula_identidad': '123456789',  # 9 caracteres (excede el límite)
        'email': 'test@email.com',
        'password': 'testpass123'
    }
    
    with pytest.raises(ValidationError):
        usuario = Usuario(**usuario_data)
        usuario.full_clean()  # Ejecuta validaciones del modelo

@pytest.mark.django_db
def test_tipo_cedula_choices_invalido():
    """Prueba que no se pueda usar un tipo de cédula inválido"""
    usuario_data = {
        'first_name': 'Test',
        'last_name': 'User',
        'username': 'testuser',
        'tipo_cedula': 'INVALID',  # Tipo inválido
        'cedula_identidad': '12345678',
        'email': 'test@email.com',
        'password': 'testpass123'
    }
    
    with pytest.raises(ValidationError):
        usuario = Usuario(**usuario_data)
        usuario.full_clean()

@pytest.mark.django_db
def test_email_formato_invalido():
    """Prueba que el email tenga un formato válido"""
    usuario_data = {
        'first_name': 'Test',
        'last_name': 'User',
        'username': 'testuser',
        'tipo_cedula': 'CI',
        'cedula_identidad': '12345678',
        'email': 'email-invalido',  # Email sin formato válido
        'password': 'testpass123'
    }
    
    with pytest.raises(ValidationError):
        usuario = Usuario(**usuario_data)
        usuario.full_clean()

@pytest.mark.django_db
def test_usuario_es_activo_por_defecto(usuario_data):
    """Prueba que los usuarios sean activos por defecto"""
    usuario = Usuario.objects.create_user(**usuario_data)
    assert usuario.is_active is True

@pytest.mark.django_db
def test_usuario_no_es_staff_por_defecto(usuario_data):
    """Prueba que los usuarios no sean staff por defecto"""
    usuario = Usuario.objects.create_user(**usuario_data)
    assert usuario.is_staff is False

@pytest.mark.django_db
def test_usuario_no_es_superuser_por_defecto(usuario_data):
    """Prueba que los usuarios no sean superuser por defecto"""
    usuario = Usuario.objects.create_user(**usuario_data)
    assert usuario.is_superuser is False