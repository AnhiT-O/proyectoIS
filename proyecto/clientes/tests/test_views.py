import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.http import Http404
from unittest.mock import patch, MagicMock
from clientes.models import Cliente, UsuarioCliente
from clientes.views import verificar_acceso_cliente, get_cliente_detalle_redirect, get_cliente_detalle_url
from usuarios.models import Usuario
from roles.models import Rol


@pytest.mark.django_db
class TestClienteViews:
    """
    Tests para las vistas de clientes
    """
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Configuración inicial para los tests"""
        self.client = Client()
        
        # Crear rol de administrador
        self.rol_admin = Rol.objects.create(
            nombre='Administrador',
            descripcion='Administrador del sistema'
        )
        
        # Crear usuario administrador con permisos
        self.usuario_admin = Usuario.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='1111111111',
            rol=self.rol_admin
        )
        
        # Crear usuario operador sin permisos especiales
        self.usuario_operador = Usuario.objects.create_user(
            username='operador',
            email='operador@example.com',
            password='testpass123',
            first_name='Operador',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='2222222222'
        )
        
        # Crear cliente de prueba
        self.cliente = Cliente.objects.create(
            nombre='Juan Pérez',
            tipoDocCliente='CI',
            docCliente='1234567890',
            correoElecCliente='juan@example.com',
            telefono='0981123456',
            tipoCliente='F',
            direccion='Asunción, Paraguay',
            ocupacion='Ingeniero',
            declaracion_jurada=True,
            segmento='minorista'
        )
        
        # Crear segundo cliente
        self.cliente2 = Cliente.objects.create(
            nombre='María García',
            tipoDocCliente='CI',
            docCliente='0987654321',
            correoElecCliente='maria@example.com',
            telefono='0985555555',
            tipoCliente='F',
            direccion='Luque, Paraguay',
            ocupacion='Doctora',
            declaracion_jurada=True,
            segmento='vip'
        )
    
    def test_cliente_crear_get_sin_login(self):
        """Test para verificar redirección al login si no está autenticado"""
        response = self.client.get(reverse('clientes:cliente_crear'))
        
        assert response.status_code == 302, "Debería redirigir al login si no está autenticado"
        assert '/login/' in response.url, "Debería redirigir a la página de login"
        print("✓ Test cliente_crear_get_sin_login: Redirección correcta sin autenticación")
    
    def test_cliente_crear_get_con_login(self):
        """Test para verificar que usuarios autenticados pueden acceder al formulario de creación"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('clientes:cliente_crear'))
        
        assert response.status_code == 200, "Debería mostrar el formulario de creación"
        assert 'form' in response.context, "Debería incluir el formulario en el contexto"
        assert 'clientes/cliente_form.html' in [t.name for t in response.templates], "Debería usar el template correcto"
        print("✓ Test cliente_crear_get_con_login: Acceso al formulario de creación correcto")
    
    def test_cliente_crear_post_datos_validos(self):
        """Test para crear cliente con datos válidos"""
        self.client.login(username='admin', password='testpass123')
        
        datos_cliente = {
            'nombre': 'Carlos López',
            'tipoDocCliente': 'CI',
            'docCliente': '5555555555',
            'correoElecCliente': 'carlos@example.com',
            'telefono': '0987777777',
            'tipoCliente': 'F',
            'direccion': 'San Lorenzo, Paraguay',
            'ocupacion': 'Contador',
            'segmento': 'corporativo',
            'declaracion_jurada': True
        }
        
        response = self.client.post(reverse('clientes:cliente_crear'), data=datos_cliente)
        
        # Verificar que se creó el cliente
        assert Cliente.objects.filter(docCliente='5555555555').exists(), "El cliente debería haberse creado"
        cliente_creado = Cliente.objects.get(docCliente='5555555555')
        
        # Verificar redirección
        assert response.status_code == 302, "Debería redirigir después de crear"
        assert response.url == reverse('clientes:cliente_detalle', args=[cliente_creado.pk]), "Debería redirigir al detalle del cliente"
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) > 0, "Debería haber mensajes"
        assert 'Cliente creado exitosamente' in str(messages[0]), "Debería mostrar mensaje de éxito"
        
        print("✓ Test cliente_crear_post_datos_validos: Creación de cliente exitosa")
    
    def test_cliente_crear_post_datos_invalidos(self):
        """Test para crear cliente con datos inválidos"""
        self.client.login(username='admin', password='testpass123')
        
        datos_invalidos = {
            'nombre': '',  # Campo requerido vacío
            'tipoDocCliente': 'CI',
            'docCliente': 'abc123',  # Documento inválido
            'correoElecCliente': 'email_invalido',  # Email inválido
            'telefono': '',  # Campo requerido vacío
            'tipoCliente': 'X',  # Choice inválido
            'direccion': '',  # Campo requerido vacío
            'ocupacion': '',  # Campo requerido vacío
            'segmento': 'premium'  # Choice inválido
        }
        
        response = self.client.post(reverse('clientes:cliente_crear'), data=datos_invalidos)
        
        # Verificar que no se creó el cliente
        assert not Cliente.objects.filter(docCliente='abc123').exists(), "No debería haberse creado el cliente con datos inválidos"
        
        # Verificar que se muestra el formulario con errores
        assert response.status_code == 200, "Debería mostrar el formulario con errores"
        assert 'form' in response.context, "Debería incluir el formulario en el contexto"
        assert response.context['form'].errors, "El formulario debería tener errores"
        
        print("✓ Test cliente_crear_post_datos_invalidos: Validación de datos inválidos correcta")
    
    def test_cliente_lista_sin_login(self):
        """Test para verificar que la lista requiere login"""
        response = self.client.get(reverse('clientes:cliente_lista'))
        
        assert response.status_code == 302, "Debería redirigir al login si no está autenticado"
        assert '/login/' in response.url, "Debería redirigir a la página de login"
        print("✓ Test cliente_lista_sin_login: Redirección correcta sin autenticación")
    
    @patch('clientes.views.permission_required')
    def test_cliente_lista_sin_permisos(self, mock_permission):
        """Test para verificar que la lista requiere permisos específicos"""
        # Configurar el mock para simular falta de permisos
        mock_permission.side_effect = Exception("Sin permisos")
        
        self.client.login(username='operador', password='testpass123')
        
        with pytest.raises(Exception, match="Sin permisos"):
            self.client.get(reverse('clientes:cliente_lista'))
        
        print("✓ Test cliente_lista_sin_permisos: Verificación de permisos correcta")
    
    def test_cliente_lista_con_permisos(self):
        """Test para verificar que usuarios con permisos pueden ver la lista"""
        # Asignar permiso al usuario admin
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission
        
        content_type = ContentType.objects.get_for_model(Cliente)
        permission = Permission.objects.get_or_create(
            codename='gestion',
            name='Puede gestionar clientes',
            content_type=content_type,
        )[0]
        self.usuario_admin.user_permissions.add(permission)
        
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('clientes:cliente_lista'))
        
        assert response.status_code == 200, "Debería mostrar la lista de clientes"
        assert 'clientes' in response.context, "Debería incluir los clientes en el contexto"
        assert self.cliente in response.context['clientes'], "Debería incluir el cliente de prueba"
        assert self.cliente2 in response.context['clientes'], "Debería incluir el segundo cliente"
        
        print("✓ Test cliente_lista_con_permisos: Acceso a lista con permisos correcto")
    
    def test_cliente_lista_filtro_segmento(self):
        """Test para verificar filtrado por segmento"""
        # Asignar permiso
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission
        
        content_type = ContentType.objects.get_for_model(Cliente)
        permission = Permission.objects.get_or_create(
            codename='gestion',
            name='Puede gestionar clientes',
            content_type=content_type,
        )[0]
        self.usuario_admin.user_permissions.add(permission)
        
        self.client.login(username='admin', password='testpass123')
        
        # Filtrar por segmento VIP
        response = self.client.get(reverse('clientes:cliente_lista'), {'segmento': 'vip'})
        
        assert response.status_code == 200, "Debería mostrar la lista filtrada"
        clientes_filtrados = list(response.context['clientes'])
        
        assert len(clientes_filtrados) == 1, "Debería mostrar solo un cliente VIP"
        assert clientes_filtrados[0] == self.cliente2, "Debería mostrar solo el cliente VIP"
        assert self.cliente not in clientes_filtrados, "No debería mostrar clientes no VIP"
        
        print("✓ Test cliente_lista_filtro_segmento: Filtrado por segmento correcto")
    
    def test_cliente_lista_busqueda(self):
        """Test para verificar funcionalidad de búsqueda"""
        # Asignar permiso
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission
        
        content_type = ContentType.objects.get_for_model(Cliente)
        permission = Permission.objects.get_or_create(
            codename='gestion',
            name='Puede gestionar clientes',
            content_type=content_type,
        )[0]
        self.usuario_admin.user_permissions.add(permission)
        
        self.client.login(username='admin', password='testpass123')
        
        # Buscar por nombre
        response = self.client.get(reverse('clientes:cliente_lista'), {'busqueda': 'Juan'})
        
        assert response.status_code == 200, "Debería mostrar los resultados de búsqueda"
        clientes_encontrados = list(response.context['clientes'])
        
        assert len(clientes_encontrados) == 1, "Debería encontrar un cliente"
        assert clientes_encontrados[0] == self.cliente, "Debería encontrar a Juan Pérez"
        
        # Buscar por documento
        response = self.client.get(reverse('clientes:cliente_lista'), {'busqueda': '0987654321'})
        
        clientes_encontrados = list(response.context['clientes'])
        assert len(clientes_encontrados) == 1, "Debería encontrar un cliente por documento"
        assert clientes_encontrados[0] == self.cliente2, "Debería encontrar a María García"
        
        print("✓ Test cliente_lista_busqueda: Búsqueda funcionando correctamente")
    
    def test_cliente_detalle_sin_login(self):
        """Test para verificar que el detalle requiere login"""
        response = self.client.get(reverse('clientes:cliente_detalle', args=[self.cliente.pk]))
        
        assert response.status_code == 302, "Debería redirigir al login si no está autenticado"
        assert '/login/' in response.url, "Debería redirigir a la página de login"
        print("✓ Test cliente_detalle_sin_login: Redirección correcta sin autenticación")
    
    def test_cliente_detalle_sin_acceso(self):
        """Test para verificar que usuarios sin acceso no pueden ver el detalle"""
        self.client.login(username='operador', password='testpass123')
        response = self.client.get(reverse('clientes:cliente_detalle', args=[self.cliente.pk]))
        
        # Debería redirigir porque no tiene acceso
        assert response.status_code == 302, "Debería redirigir si no tiene acceso"
        
        # Verificar mensaje de error
        messages = list(get_messages(response.wsgi_request))
        assert any('No tienes permisos' in str(msg) for msg in messages), "Debería mostrar mensaje de error de permisos"
        
        print("✓ Test cliente_detalle_sin_acceso: Verificación de acceso correcta")
    
    def test_cliente_detalle_con_acceso_admin(self):
        """Test para verificar que admin puede ver cualquier cliente"""
        # Asignar permiso de gestión
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission
        
        content_type = ContentType.objects.get_for_model(Cliente)
        permission = Permission.objects.get_or_create(
            codename='gestion',
            name='Puede gestionar clientes',
            content_type=content_type,
        )[0]
        self.usuario_admin.user_permissions.add(permission)
        
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('clientes:cliente_detalle', args=[self.cliente.pk]))
        
        assert response.status_code == 200, "Admin debería poder ver el detalle del cliente"
        assert response.context['cliente'] == self.cliente, "Debería mostrar el cliente correcto"
        
        print("✓ Test cliente_detalle_con_acceso_admin: Acceso de admin correcto")
    
    def test_cliente_detalle_con_acceso_operador_asociado(self):
        """Test para verificar que operador asociado puede ver el cliente"""
        # Asociar operador al cliente
        self.cliente.usuarios.add(self.usuario_operador)
        
        self.client.login(username='operador', password='testpass123')
        response = self.client.get(reverse('clientes:cliente_detalle', args=[self.cliente.pk]))
        
        assert response.status_code == 200, "Operador asociado debería poder ver el detalle del cliente"
        assert response.context['cliente'] == self.cliente, "Debería mostrar el cliente correcto"
        
        print("✓ Test cliente_detalle_con_acceso_operador_asociado: Acceso de operador asociado correcto")
    
    def test_cliente_detalle_cliente_inexistente(self):
        """Test para verificar manejo de cliente inexistente"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('clientes:cliente_detalle', args=[9999]))
        
        assert response.status_code == 404, "Debería devolver 404 para cliente inexistente"
        print("✓ Test cliente_detalle_cliente_inexistente: Manejo de 404 correcto")
    
    def test_cliente_editar_sin_permisos(self):
        """Test para verificar que editar requiere permisos específicos"""
        self.client.login(username='operador', password='testpass123')
        response = self.client.get(reverse('clientes:cliente_editar', args=[self.cliente.pk]))
        
        # Verificar que se niega el acceso (puede ser 403 o redirección dependiendo de la configuración)
        assert response.status_code in [302, 403], "Debería negar el acceso sin permisos"
        print("✓ Test cliente_editar_sin_permisos: Verificación de permisos para edición correcta")
    
    def test_verificar_acceso_cliente_function(self):
        """Test para la función helper verificar_acceso_cliente"""
        # Asignar permiso de gestión al admin
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission
        
        content_type = ContentType.objects.get_for_model(Cliente)
        permission = Permission.objects.get_or_create(
            codename='gestion',
            name='Puede gestionar clientes',
            content_type=content_type,
        )[0]
        self.usuario_admin.user_permissions.add(permission)
        
        # Test admin tiene acceso
        assert verificar_acceso_cliente(self.usuario_admin, self.cliente), "Admin debería tener acceso"
        
        # Test operador sin asociación no tiene acceso
        assert not verificar_acceso_cliente(self.usuario_operador, self.cliente), "Operador sin asociación no debería tener acceso"
        
        # Test operador con asociación tiene acceso
        self.cliente.usuarios.add(self.usuario_operador)
        assert verificar_acceso_cliente(self.usuario_operador, self.cliente), "Operador asociado debería tener acceso"
        
        print("✓ Test verificar_acceso_cliente_function: Función de verificación de acceso correcta")
    
    def test_get_cliente_detalle_redirect_function(self):
        """Test para la función helper get_cliente_detalle_redirect"""
        # Crear request mock
        request_mock = MagicMock()
        request_mock.META = {'HTTP_REFERER': '/usuarios/cliente/1/'}
        request_mock.user = self.usuario_operador
        
        # Test redirección para operador
        response = get_cliente_detalle_redirect(request_mock, self.cliente.pk)
        assert response.status_code == 302, "Debería redirigir"
        assert f'/usuarios/cliente/{self.cliente.pk}/' in response.url, "Debería redirigir a la vista de usuario"
        
        print("✓ Test get_cliente_detalle_redirect_function: Función de redirección correcta")
    
    def test_get_cliente_detalle_url_function(self):
        """Test para la función helper get_cliente_detalle_url"""
        # Crear request mock para operador
        request_mock = MagicMock()
        request_mock.META = {'HTTP_REFERER': '/usuarios/cliente/1/'}
        request_mock.user = self.usuario_operador
        
        url = get_cliente_detalle_url(request_mock, self.cliente.pk)
        assert url == f'/usuarios/cliente/{self.cliente.pk}/', "Debería devolver URL de usuario para operador"
        
        # Asignar permiso de gestión al admin
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission
        
        content_type = ContentType.objects.get_for_model(Cliente)
        permission = Permission.objects.get_or_create(
            codename='gestion',
            name='Puede gestionar clientes',
            content_type=content_type,
        )[0]
        self.usuario_admin.user_permissions.add(permission)
        
        # Test para admin
        request_mock.user = self.usuario_admin
        request_mock.META = {'HTTP_REFERER': '/clientes/'}
        
        url = get_cliente_detalle_url(request_mock, self.cliente.pk)
        assert url == f'/clientes/{self.cliente.pk}/', "Debería devolver URL de admin para admin"
        
        print("✓ Test get_cliente_detalle_url_function: Función de URL correcta")
