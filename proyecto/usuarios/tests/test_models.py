import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from usuarios.models import Usuario

Usuario = get_user_model()

@pytest.mark.django_db
class TestUsuarioModel:
    
    def test_crear_usuario_exitoso(self):
        """Prueba que se puede crear un usuario con datos válidos"""
        usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Juan',
            last_name='Pérez',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            password='password123'
        )
        
        assert usuario.username == 'testuser'
        assert usuario.email == 'test@example.com'
        assert usuario.first_name == 'Juan'
        assert usuario.last_name == 'Pérez'
        assert usuario.tipo_cedula == 'CI'
        assert usuario.cedula_identidad == '12345678'
        assert usuario.check_password('password123')
    
    def test_str_representacion(self):
        """Prueba que la representación string del usuario es correcta"""
        usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='María',
            last_name='González',
            tipo_cedula='RUC',
            cedula_identidad='87654321',
            password='password123'
        )
        
        expected = "María González (testuser)"
        assert str(usuario) == expected
    
    def test_tipo_cedula_choices(self):
        """Prueba que los tipos de cédula disponibles son correctos"""
        choices = dict(Usuario.TIPO_CEDULA_CHOICES)
        assert 'RUC' in choices
        assert 'CI' in choices
        assert choices['RUC'] == 'Registro Único de Contribuyente'
        assert choices['CI'] == 'Cédula de Identidad'
    
    def test_crear_usuario_con_ruc(self):
        """Prueba crear usuario con tipo de cédula RUC"""
        usuario = Usuario.objects.create_user(
            username='empresa',
            email='empresa@example.com',
            first_name='Empresa',
            last_name='SA',
            tipo_cedula='RUC',
            cedula_identidad='20123456789',
            password='password123'
        )
        
        assert usuario.tipo_cedula == 'RUC'
    
    def test_crear_usuario_con_ci(self):
        """Prueba crear usuario con tipo de cédula CI"""
        usuario = Usuario.objects.create_user(
            username='persona',
            email='persona@example.com',
            first_name='Ana',
            last_name='López',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            password='password123'
        )
        
        assert usuario.tipo_cedula == 'CI'
    
    def test_username_field_configuracion(self):
        """Prueba que USERNAME_FIELD está configurado correctamente"""
        assert Usuario.USERNAME_FIELD == 'username'
    
    def test_required_fields_configuracion(self):
        """Prueba que REQUIRED_FIELDS contiene los campos necesarios"""
        expected_fields = ['email', 'first_name', 'last_name', 'tipo_cedula', 'cedula_identidad']
        assert Usuario.REQUIRED_FIELDS == expected_fields
    
    def test_meta_configuracion(self):
        """Prueba la configuración Meta del modelo"""
        assert Usuario._meta.db_table == 'usuarios'
        assert Usuario._meta.verbose_name == 'Usuario'
        assert Usuario._meta.verbose_name_plural == 'Usuarios'
    
    def test_username_unico(self):
        """Prueba que el username debe ser único"""
        Usuario.objects.create_user(
            username='duplicado',
            email='test1@example.com',
            first_name='Usuario',
            last_name='Uno',
            tipo_cedula='CI',
            cedula_identidad='11111111',
            password='password123'
        )
        
        with pytest.raises(IntegrityError):
            Usuario.objects.create_user(
                username='duplicado',
                email='test2@example.com',
                first_name='Usuario',
                last_name='Dos',
                tipo_cedula='CI',
                cedula_identidad='22222222',
                password='password123'
            )
    
    @pytest.mark.parametrize("campo_faltante", [
        'username', 'email', 'first_name', 'last_name', 'tipo_cedula', 'cedula_identidad'
    ])
    def test_campos_requeridos(self, campo_faltante):
        """Prueba que todos los campos requeridos son obligatorios"""
        datos_base = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
        }
        
        # Remover el campo que queremos probar
        datos_sin_campo = datos_base.copy()
        del datos_sin_campo[campo_faltante]
        
        # Crear usuario sin save() para probar validaciones
        usuario = Usuario(**datos_sin_campo)
        
        with pytest.raises((ValidationError, IntegrityError)):
            usuario.full_clean()  # Esto ejecuta las validaciones del modelo
