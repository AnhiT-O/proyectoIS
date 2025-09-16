import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core import mail
from unittest.mock import patch, Mock
from usuarios.models import Usuario
from usuarios.forms import RegistroUsuarioForm
from clientes.models import Cliente, UsuarioCliente


class TestRegistroUsuarioView:
    """Pruebas para la vista de registro de usuario"""
    
    @pytest.fixture
    def client(self):
        """Cliente HTTP para las pruebas"""
        return Client()
    
    @pytest.fixture
    def datos_registro(self):
        """Datos válidos para el registro"""
        return {
            'username': 'newuser',
            'first_name': 'Nuevo',
            'last_name': 'Usuario',
            'email': 'nuevo@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
    
    @pytest.mark.django_db
    @patch('usuarios.views.enviar_email_confirmacion')
    def test_registro_usuario_exitoso(self, mock_email, client, datos_registro):
        """Prueba 9a: Vista crea usuario exitosamente"""
        url = reverse('usuarios:registro')
        response = client.post(url, data=datos_registro)
        
        # Verificar que el usuario fue creado
        assert Usuario.objects.filter(username='newuser').exists()
        usuario = Usuario.objects.get(username='newuser')
        assert usuario.email == 'nuevo@example.com'
        assert usuario.first_name == 'Nuevo'
        assert usuario.last_name == 'Usuario'
    
    @pytest.mark.django_db
    @patch('usuarios.views.enviar_email_confirmacion')
    def test_registro_usuario_envia_email(self, mock_email, client, datos_registro):
        """Prueba 9b: Vista envía email de confirmación"""
        url = reverse('usuarios:registro')
        response = client.post(url, data=datos_registro)
        
        # Verificar que se llamó a la función de envío de email
        mock_email.assert_called_once()
        
        # Verificar el usuario pasado a la función
        usuario_creado = mock_email.call_args[0][1]  # Segundo argumento (user)
        assert usuario_creado.username == 'newuser'
    
    @pytest.mark.django_db
    @patch('usuarios.views.enviar_email_confirmacion')
    def test_registro_usuario_redirige_correctamente(self, mock_email, client, datos_registro):
        """Prueba 9c: Vista redirige correctamente después del registro"""
        url = reverse('usuarios:registro')
        response = client.post(url, data=datos_registro)
        
        # Verificar redirección a login
        assert response.status_code == 302
        assert response.url == reverse('login')
    
    @pytest.mark.django_db
    def test_registro_usuario_get_muestra_formulario(self, client):
        """Prueba 9d: GET muestra el formulario de registro"""
        url = reverse('usuarios:registro')
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert isinstance(response.context['form'], RegistroUsuarioForm)


class TestActivarCuentaView:
    """Pruebas para la vista de activación de cuenta"""
    
    @pytest.fixture
    def client(self):
        """Cliente HTTP para las pruebas"""
        return Client()
    
    @pytest.fixture
    def usuario_inactivo(self, db):
        """Usuario inactivo para las pruebas"""
        return Usuario.objects.create(
            username='inactive',
            email='inactive@example.com',
            first_name='Usuario',
            last_name='Inactivo',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            is_active=False
        )
    
    @pytest.fixture
    def grupo_operador(self, db):
        """Crear grupo Operador"""
        grupo, _ = Group.objects.get_or_create(name='Operador')
        return grupo
    
    @pytest.mark.django_db
    def test_activar_cuenta_token_valido(self, client, usuario_inactivo, grupo_operador):
        """Prueba 10a: Activa usuario con token válido"""
        token = default_token_generator.make_token(usuario_inactivo)
        uidb64 = urlsafe_base64_encode(force_bytes(usuario_inactivo.pk))
        
        url = reverse('usuarios:activar_cuenta', kwargs={'uidb64': uidb64, 'token': token})
        response = client.get(url)
        
        # Verificar que el usuario está activo
        usuario_inactivo.refresh_from_db()
        assert usuario_inactivo.is_active is True
    
    @pytest.mark.django_db
    def test_activar_cuenta_asigna_rol_operador(self, client, usuario_inactivo, grupo_operador):
        """Prueba 10b: Asigna rol Operador al activar cuenta"""
        token = default_token_generator.make_token(usuario_inactivo)
        uidb64 = urlsafe_base64_encode(force_bytes(usuario_inactivo.pk))
        
        url = reverse('usuarios:activar_cuenta', kwargs={'uidb64': uidb64, 'token': token})
        response = client.get(url)
        
        # Verificar que se asignó el rol Operador
        usuario_inactivo.refresh_from_db()
        assert usuario_inactivo.groups.filter(name='Operador').exists()
    
    @pytest.mark.django_db
    def test_activar_cuenta_redirige_inicio(self, client, usuario_inactivo, grupo_operador):
        """Prueba 10c: Redirige a inicio después de activar"""
        token = default_token_generator.make_token(usuario_inactivo)
        uidb64 = urlsafe_base64_encode(force_bytes(usuario_inactivo.pk))
        
        url = reverse('usuarios:activar_cuenta', kwargs={'uidb64': uidb64, 'token': token})
        response = client.get(url)
        
        # Verificar redirección
        assert response.status_code == 302
        assert response.url == reverse('inicio')
    
    @pytest.mark.django_db
    def test_activar_cuenta_token_invalido(self, client, usuario_inactivo):
        """Prueba 10d: Token inválido redirige a registro"""
        uidb64 = urlsafe_base64_encode(force_bytes(usuario_inactivo.pk))
        token_invalido = 'token-invalido'
        
        url = reverse('usuarios:activar_cuenta', kwargs={'uidb64': uidb64, 'token': token_invalido})
        response = client.get(url)
        
        # Verificar redirección a registro
        assert response.status_code == 302
        assert response.url == reverse('usuarios:registro')


class TestRecuperarPasswordView:
    """Pruebas para la vista de recuperar contraseña"""
    
    @pytest.fixture
    def client(self):
        """Cliente HTTP para las pruebas"""
        return Client()
    
    @pytest.fixture
    def usuario_activo(self, db):
        """Usuario activo para pruebas"""
        return Usuario.objects.create(
            username='activo',
            email='activo@example.com',
            first_name='Usuario',
            last_name='Activo',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            is_active=True
        )
    
    @pytest.fixture
    def usuario_inactivo(self, db):
        """Usuario inactivo para pruebas"""
        return Usuario.objects.create(
            username='inactivo',
            email='inactivo@example.com',
            first_name='Usuario',
            last_name='Inactivo',
            tipo_cedula='CI',
            cedula_identidad='87654321',
            is_active=False
        )
    
    @pytest.mark.django_db
    @patch('usuarios.views.enviar_email_recuperacion')
    def test_recuperar_password_usuario_existente_activo(self, mock_email, client, usuario_activo):
        """Prueba 11a: Envía email si usuario existe y está activo"""
        url = reverse('usuarios:recuperar_password')
        response = client.post(url, data={'email': usuario_activo.email})
        
        # Verificar que se llamó a la función de envío de email
        mock_email.assert_called_once()
        
        # Verificar el usuario pasado a la función
        usuario_en_email = mock_email.call_args[0][1]  # Segundo argumento (user)
        assert usuario_en_email.id == usuario_activo.id
    
    @pytest.mark.django_db
    def test_recuperar_password_usuario_no_existe(self, client):
        """Prueba 11b: No envía email si usuario no existe"""
        url = reverse('usuarios:recuperar_password')
        response = client.post(url, data={'email': 'noexiste@example.com'})
        
        # Verificar que el formulario no es válido
        assert response.status_code == 200
        assert 'form' in response.context
        assert not response.context['form'].is_valid()
    
    @pytest.mark.django_db
    def test_recuperar_password_usuario_inactivo(self, client, usuario_inactivo):
        """Prueba 11c: No envía email si usuario está inactivo"""
        url = reverse('usuarios:recuperar_password')
        response = client.post(url, data={'email': usuario_inactivo.email})
        
        # Verificar que el formulario no es válido
        assert response.status_code == 200
        assert 'form' in response.context
        assert not response.context['form'].is_valid()


class TestResetPasswordConfirmView:
    """Pruebas para la vista de confirmación de reseteo de contraseña"""
    
    @pytest.fixture
    def client(self):
        """Cliente HTTP para las pruebas"""
        return Client()
    
    @pytest.fixture
    def usuario(self, db):
        """Usuario para las pruebas"""
        return Usuario.objects.create(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            is_active=True
        )
    
    @pytest.mark.django_db
    def test_reset_password_token_valido_get(self, client, usuario):
        """Prueba 12a: GET con token válido muestra formulario"""
        token = default_token_generator.make_token(usuario)
        uidb64 = urlsafe_base64_encode(force_bytes(usuario.pk))
        
        url = reverse('usuarios:reset_password_confirm', kwargs={'uidb64': uidb64, 'token': token})
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['validlink'] is True
    
    @pytest.mark.django_db
    def test_reset_password_token_valido_post(self, client, usuario):
        """Prueba 12b: POST con token válido cambia contraseña"""
        token = default_token_generator.make_token(usuario)
        uidb64 = urlsafe_base64_encode(force_bytes(usuario.pk))
        
        url = reverse('usuarios:reset_password_confirm', kwargs={'uidb64': uidb64, 'token': token})
        response = client.post(url, data={
            'new_password1': 'NewComplexPass123!',
            'new_password2': 'NewComplexPass123!'
        })
        
        # Verificar redirección a login
        assert response.status_code == 302
        assert response.url == reverse('login')
        
        # Verificar que la contraseña cambió
        usuario.refresh_from_db()
        assert usuario.check_password('NewComplexPass123!')
    
    @pytest.mark.django_db
    def test_reset_password_token_invalido(self, client, usuario):
        """Prueba 12c: Token inválido redirige a recuperar password"""
        uidb64 = urlsafe_base64_encode(force_bytes(usuario.pk))
        token_invalido = 'token-invalido'
        
        url = reverse('usuarios:reset_password_confirm', kwargs={'uidb64': uidb64, 'token': token_invalido})
        response = client.get(url)
        
        # Verificar redirección
        assert response.status_code == 302
        assert response.url == reverse('usuarios:recuperar_password')


class TestBloquearUsuarioView:
    """Pruebas para la vista de bloquear usuario"""
    
    @pytest.fixture
    def client(self):
        """Cliente HTTP para las pruebas"""
        return Client()
    
    @pytest.fixture
    def usuario_con_permiso(self, db):
        """Usuario con permiso de bloqueo"""
        usuario = Usuario.objects.create(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='11111111',
            is_active=True
        )
        
        # Crear y asignar permiso
        content_type = ContentType.objects.get_for_model(Usuario)
        permission, _ = Permission.objects.get_or_create(
            codename='bloqueo',
            name='Puede bloquear o desbloquear usuarios',
            content_type=content_type,
        )
        usuario.user_permissions.add(permission)
        return usuario
    
    @pytest.fixture
    def usuario_objetivo(self, db):
        """Usuario que será bloqueado"""
        return Usuario.objects.create(
            username='target',
            email='target@example.com',
            first_name='Target',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='22222222',
            is_active=True,
            bloqueado=False
        )
    
    @pytest.mark.django_db
    def test_bloquear_usuario_solo_post(self, client, usuario_con_permiso, usuario_objetivo):
        """Prueba 13a: Solo permite método POST"""
        client.force_login(usuario_con_permiso)
        url = reverse('usuarios:bloquear_usuario', kwargs={'pk': usuario_objetivo.pk})
        
        # GET debe fallar
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == reverse('usuarios:administrar_usuarios')
    
    @pytest.mark.django_db
    def test_bloquear_usuario_con_permiso(self, client, usuario_con_permiso, usuario_objetivo):
        """Prueba 13b: Bloquea usuario si tiene permiso"""
        client.force_login(usuario_con_permiso)
        url = reverse('usuarios:bloquear_usuario', kwargs={'pk': usuario_objetivo.pk})
        
        response = client.post(url)
        
        # Verificar que el usuario fue bloqueado
        usuario_objetivo.refresh_from_db()
        assert usuario_objetivo.bloqueado is True
        
        # Verificar redirección
        assert response.status_code == 302
        assert response.url == reverse('usuarios:administrar_usuarios')
    
    @pytest.mark.django_db
    def test_bloquear_usuario_sin_permiso_deniega_acceso(self, client, usuario_objetivo):
        """Prueba 13c: Deniega acceso si no tiene permiso"""
        usuario_sin_permiso = Usuario.objects.create(
            username='noperm',
            email='noperm@example.com',
            first_name='No',
            last_name='Permission',
            tipo_cedula='CI',
            cedula_identidad='33333333',
            is_active=True
        )
        
        client.force_login(usuario_sin_permiso)
        url = reverse('usuarios:bloquear_usuario', kwargs={'pk': usuario_objetivo.pk})
        
        response = client.post(url)
        
        # Verificar acceso denegado (403)
        assert response.status_code == 403


class TestAsignarRolView:
    """Pruebas para la vista de asignar rol"""
    
    @pytest.fixture
    def client(self):
        """Cliente HTTP para las pruebas"""
        return Client()
    
    @pytest.fixture
    def usuario_con_permiso(self, db):
        """Usuario con permiso de asignación de roles"""
        usuario = Usuario.objects.create(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='11111111',
            is_active=True
        )
        
        # Crear y asignar permiso
        content_type = ContentType.objects.get_for_model(Usuario)
        permission, _ = Permission.objects.get_or_create(
            codename='asignacion_roles',
            name='Puede asignar roles a usuarios',
            content_type=content_type,
        )
        usuario.user_permissions.add(permission)
        return usuario
    
    @pytest.fixture
    def usuario_objetivo(self, db):
        """Usuario que recibirá los roles"""
        return Usuario.objects.create(
            username='target',
            email='target@example.com',
            first_name='Target',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='22222222',
            is_active=True
        )
    
    @pytest.fixture
    def grupos(self, db):
        """Crear grupos para las pruebas"""
        admin, _ = Group.objects.get_or_create(name='Administrador')
        operador, _ = Group.objects.get_or_create(name='Operador')
        supervisor, _ = Group.objects.get_or_create(name='Supervisor')
        return {'admin': admin, 'operador': operador, 'supervisor': supervisor}
    
    @pytest.mark.django_db
    def test_asignar_rol_solo_con_permiso(self, client, usuario_con_permiso, usuario_objetivo, grupos):
        """Prueba 14a: Asigna roles solo si tiene permiso"""
        client.force_login(usuario_con_permiso)
        url = reverse('usuarios:asignar_rol', kwargs={'pk': usuario_objetivo.pk})
        
        response = client.post(url, data={'rol': [grupos['operador'].id]})
        
        # Verificar que se asignó el rol
        assert usuario_objetivo.groups.filter(name='Operador').exists()
        
        # Verificar redirección
        assert response.status_code == 302
        assert response.url == reverse('usuarios:administrar_usuarios')
    
    @pytest.mark.django_db
    def test_asignar_rol_no_administrador_a_no_admin(self, client, usuario_con_permiso, usuario_objetivo, grupos):
        """Prueba 14b: Usuario no administrador no puede modificar otros administradores"""
        # Hacer al usuario objetivo administrador
        usuario_objetivo.groups.add(grupos['admin'])
        
        client.force_login(usuario_con_permiso)
        url = reverse('usuarios:asignar_rol', kwargs={'pk': usuario_objetivo.pk})
        
        response = client.get(url)
        
        # Verificar redirección con mensaje de error
        assert response.status_code == 302
        assert response.url == reverse('usuarios:administrar_usuarios')
    
    @pytest.mark.django_db
    def test_asignar_rol_sin_permiso(self, client, usuario_objetivo, grupos):
        """Prueba 14c: Deniega acceso si no tiene permiso"""
        usuario_sin_permiso = Usuario.objects.create(
            username='noperm',
            email='noperm@example.com',
            first_name='No',
            last_name='Permission',
            tipo_cedula='CI',
            cedula_identidad='33333333',
            is_active=True
        )
        
        client.force_login(usuario_sin_permiso)
        url = reverse('usuarios:asignar_rol', kwargs={'pk': usuario_objetivo.pk})
        
        response = client.get(url)
        
        # Verificar acceso denegado
        assert response.status_code == 403


class TestAsignarClientesView:
    """Pruebas para la vista de asignar clientes"""
    
    @pytest.fixture
    def client(self):
        """Cliente HTTP para las pruebas"""
        return Client()
    
    @pytest.fixture
    def usuario_con_permiso(self, db):
        """Usuario con permiso de asignación de clientes"""
        usuario = Usuario.objects.create(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='11111111',
            is_active=True
        )
        
        # Crear y asignar permiso
        content_type = ContentType.objects.get_for_model(Usuario)
        permission, _ = Permission.objects.get_or_create(
            codename='asignacion_clientes',
            name='Puede asignar clientes a usuarios',
            content_type=content_type,
        )
        usuario.user_permissions.add(permission)
        return usuario
    
    @pytest.fixture
    def operador(self, db):
        """Usuario operador para recibir clientes"""
        usuario = Usuario.objects.create(
            username='operador',
            email='operador@example.com',
            first_name='Operador',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='22222222',
            is_active=True
        )
        
        # Asignar rol Operador
        grupo_operador, _ = Group.objects.get_or_create(name='Operador')
        usuario.groups.add(grupo_operador)
        return usuario
    
    @pytest.fixture
    def usuario_no_operador(self, db):
        """Usuario que no es operador"""
        return Usuario.objects.create(
            username='nooperador',
            email='nooperador@example.com',
            first_name='No',
            last_name='Operador',
            tipo_cedula='CI',
            cedula_identidad='33333333',
            is_active=True
        )
    
    @pytest.fixture
    def clientes(self, db):
        """Clientes para las pruebas"""
        cliente1 = Cliente.objects.create(
            nombre='Cliente 1',
            tipoDocCliente='CI',
            docCliente='12345678',
            correoElecCliente='cliente1@example.com',
            telefono='+595981123456',
            tipoCliente='F',
            direccion='Dirección 1',
            ocupacion='Ocupación 1'
        )
        cliente2 = Cliente.objects.create(
            nombre='Cliente 2',
            tipoDocCliente='RUC',
            docCliente='87654321',
            correoElecCliente='cliente2@example.com',
            telefono='+595981654321',
            tipoCliente='J',
            direccion='Dirección 2',
            ocupacion='Ocupación 2'
        )
        return [cliente1, cliente2]
    
    @pytest.mark.django_db
    def test_asignar_clientes_solo_operadores(self, client, usuario_con_permiso, usuario_no_operador, clientes):
        """Prueba 15a: Solo permite asignar clientes a operadores"""
        client.force_login(usuario_con_permiso)
        url = reverse('usuarios:asignar_clientes', kwargs={'pk': usuario_no_operador.pk})
        
        response = client.get(url)
        
        # Verificar redirección con mensaje de error
        assert response.status_code == 302
        assert response.url == reverse('usuarios:administrar_usuarios')
    
    @pytest.mark.django_db
    def test_asignar_clientes_verifica_clientes_disponibles(self, client, usuario_con_permiso, operador):
        """Prueba 15b: Verifica si hay clientes disponibles"""
        client.force_login(usuario_con_permiso)
        url = reverse('usuarios:asignar_clientes', kwargs={'pk': operador.pk})
        
        # Sin clientes en el sistema
        response = client.get(url)
        
        # Verificar redirección (no hay clientes)
        assert response.status_code == 302
        assert response.url == reverse('usuarios:administrar_usuarios')
    
    @pytest.mark.django_db
    def test_asignar_clientes_exitoso(self, client, usuario_con_permiso, operador, clientes):
        """Prueba 15c: Asigna clientes exitosamente"""
        client.force_login(usuario_con_permiso)
        url = reverse('usuarios:asignar_clientes', kwargs={'pk': operador.pk})
        
        response = client.post(url, data={'clientes': [clientes[0].id]})
        
        # Verificar que se asignó el cliente
        assert UsuarioCliente.objects.filter(usuario=operador, cliente=clientes[0]).exists()
        
        # Verificar redirección
        assert response.status_code == 302
        assert response.url == reverse('usuarios:usuario_detalle', kwargs={'pk': operador.pk})
