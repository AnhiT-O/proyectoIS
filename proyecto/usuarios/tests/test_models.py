import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
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
    
    def test_campo_bloqueado_default(self):
        """Prueba que el campo bloqueado tiene valor por defecto False"""
        usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Juan',
            last_name='Pérez',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            password='password123'
        )
        
        assert usuario.bloqueado is False
    
    def test_esta_bloqueado_metodo(self):
        """Prueba el método esta_bloqueado"""
        usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Juan',
            last_name='Pérez',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            password='password123'
        )
        
        # Por defecto no está bloqueado
        assert not usuario.esta_bloqueado()
        
        # Bloquear usuario
        usuario.bloqueado = True
        usuario.save()
        
        assert usuario.esta_bloqueado()
    
    def test_asignar_grupo_exitoso(self):
        """Prueba que se pueda asignar un grupo a un usuario"""
        # Crear grupo
        grupo, created = Group.objects.get_or_create(name='test_grupo')
        
        usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Juan',
            last_name='Pérez',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            password='password123'
        )
        
        resultado = usuario.asignar_grupo('test_grupo')
        
        assert resultado is True
        assert usuario.groups.filter(name='test_grupo').exists()
    
    def test_asignar_grupo_inexistente(self):
        """Prueba que asignar un grupo inexistente lance excepción"""
        usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Juan',
            last_name='Pérez',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            password='password123'
        )
        
        with pytest.raises(ValidationError):
            usuario.asignar_grupo('grupo_inexistente')
    
    def test_remover_grupo_exitoso(self):
        """Prueba que se pueda remover un grupo de un usuario"""
        # Crear grupo
        grupo, created = Group.objects.get_or_create(name='test_grupo2')
        
        usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Juan',
            last_name='Pérez',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            password='password123'
        )
        
        # Asignar y luego remover
        usuario.asignar_grupo('test_grupo2')
        resultado = usuario.remover_grupo('test_grupo2')
        
        assert resultado is True
        assert not usuario.groups.filter(name='test_grupo2').exists()
    
    def test_remover_grupo_inexistente(self):
        """Prueba que remover un grupo inexistente lance excepción"""
        usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Juan',
            last_name='Pérez',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            password='password123'
        )
        
        with pytest.raises(ValidationError):
            usuario.remover_grupo('grupo_inexistente')
    
    def test_es_administrador(self):
        """Prueba el método es_administrador"""
        # Crear grupo administrador
        Group.objects.get_or_create(name='administrador')
        
        usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Juan',
            last_name='Pérez',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            password='password123'
        )
        
        # Por defecto no es administrador
        assert not usuario.es_administrador()
        
        # Asignar grupo administrador
        usuario.asignar_grupo('administrador')
        
        assert usuario.es_administrador()
    
    def test_es_analista_cambiario(self):
        """Prueba el método es_analista_cambiario"""
        # Crear grupo analista cambiario
        Group.objects.get_or_create(name='analista cambiario')
        
        usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Juan',
            last_name='Pérez',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            password='password123'
        )
        
        # Por defecto no es analista cambiario
        assert not usuario.es_analista_cambiario()
        
        # Asignar grupo analista cambiario
        usuario.asignar_grupo('analista cambiario')
        
        assert usuario.es_analista_cambiario()
    
    def test_es_operador(self):
        """Prueba el método es_operador"""
        # Crear grupo operador
        Group.objects.get_or_create(name='operador')
        
        usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Juan',
            last_name='Pérez',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            password='password123'
        )
        
        # Por defecto se asigna el grupo operador automáticamente
        assert usuario.es_operador()
        
        # Remover grupo operador para probar el método
        usuario.remover_grupo('operador')
        assert not usuario.es_operador()
        
        # Asignar grupo operador nuevamente
        usuario.asignar_grupo('operador')
        assert usuario.es_operador()
    
    def test_obtener_grupos(self):
        """Prueba el método obtener_grupos"""
        # Crear grupos
        Group.objects.get_or_create(name='administrador')
        Group.objects.get_or_create(name='operador')
        
        usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Juan',
            last_name='Pérez',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            password='password123'
        )
        
        # Por defecto se asigna grupo operador automáticamente
        grupos_iniciales = usuario.obtener_grupos()
        assert 'operador' in grupos_iniciales
        
        # Limpiar grupos para probar desde cero
        usuario.groups.clear()
        assert usuario.obtener_grupos() == []
        
        # Asignar grupos
        usuario.asignar_grupo('administrador')
        usuario.asignar_grupo('operador')
        
        grupos = usuario.obtener_grupos()
        assert 'administrador' in grupos
        assert 'operador' in grupos
        assert len(grupos) == 2
    
    def test_asignar_grupo_por_defecto(self):
        """Prueba el método asignar_grupo_por_defecto"""
        # Crear grupo operador
        Group.objects.get_or_create(name='operador')
        
        usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Juan',
            last_name='Pérez',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            password='password123'
        )
        
        # Remover todos los grupos para probar el método
        usuario.groups.clear()
        
        usuario.asignar_grupo_por_defecto()
        
        assert usuario.es_operador()
    
    def test_asignar_grupo_por_defecto_no_sobrescribe(self):
        """Prueba que asignar_grupo_por_defecto no sobrescribe grupos existentes"""
        # Crear grupos
        Group.objects.get_or_create(name='operador')
        Group.objects.get_or_create(name='administrador')
        
        usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Juan',
            last_name='Pérez',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            password='password123'
        )
        
        # Limpiar grupos primero
        usuario.groups.clear()
        
        # Asignar grupo administrador primero
        usuario.asignar_grupo('administrador')
        
        # Llamar método que asigna grupo por defecto
        usuario.asignar_grupo_por_defecto()
        
        # No debería asignar operador porque ya tiene grupos
        assert usuario.es_administrador()
        assert not usuario.es_operador()
    
    def test_save_asigna_grupo_por_defecto_usuario_nuevo(self):
        """Prueba que save() asigne grupo por defecto a usuario nuevo"""
        # Crear grupo operador
        Group.objects.get_or_create(name='operador')
        
        # Crear usuario sin save()
        usuario = Usuario(
            username='testuser',
            email='test@example.com',
            first_name='Juan',
            last_name='Pérez',
            tipo_cedula='CI',
            cedula_identidad='12345678'
        )
        usuario.set_password('password123')
        
        # Al guardar debe asignar grupo por defecto
        usuario.save()
        
        assert usuario.es_operador()
    
    def test_save_no_asigna_grupo_superusuario(self):
        """Prueba que save() no asigne grupo por defecto a superusuarios"""
        # Crear grupo operador
        Group.objects.get_or_create(name='operador')
        
        # Crear superusuario
        usuario = Usuario(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='87654321',
            is_superuser=True
        )
        usuario.set_password('password123')
        usuario.save()
        
        # No debe asignar grupo por defecto
        assert not usuario.es_operador()
        assert usuario.obtener_grupos() == []

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
