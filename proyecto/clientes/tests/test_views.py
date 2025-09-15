import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages import get_messages
from clientes.models import Cliente, UsuarioCliente
from usuarios.models import Usuario
from medios_pago.models import MedioPago, MedioPagoCliente


@pytest.mark.django_db
class TestBaseClienteView:
    """
    Clase base para tests de vistas con configuración común
    """
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Configuración inicial común para todos los tests de vistas"""
        self.client = Client()
        
        # Crear usuario administrador con permisos
        self.admin_user = Usuario.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='1111111111'
        )
        
        # Asignar permiso de gestión de clientes
        content_type = ContentType.objects.get_for_model(Cliente)
        permission = Permission.objects.get_or_create(
            codename='gestion',
            name='Puede gestionar clientes (crear y editar)',
            content_type=content_type,
        )[0]
        self.admin_user.user_permissions.add(permission)
        
        # Crear usuario operador sin permisos administrativos
        self.operador_user = Usuario.objects.create_user(
            username='operador',
            email='operador@example.com',
            password='operador123',
            first_name='Operador',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='2222222222'
        )
        
        # Crear usuario sin permisos
        self.user_sin_permisos = Usuario.objects.create_user(
            username='usuario',
            email='usuario@example.com',
            password='usuario123',
            first_name='Usuario',
            last_name='Normal',
            tipo_cedula='CI',
            cedula_identidad='3333333333'
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
        
        # Asociar operador con cliente
        UsuarioCliente.objects.create(
            usuario=self.operador_user,
            cliente=self.cliente
        )
        
        # Datos válidos para formularios
        self.datos_cliente_validos = {
            'nombre': 'María García',
            'tipoDocCliente': 'CI',
            'docCliente': '0987654321',
            'correoElecCliente': 'maria@example.com',
            'telefono': '0984567890',
            'tipoCliente': 'F',
            'direccion': 'Ciudad del Este, Paraguay',
            'ocupacion': 'Doctora',
            'declaracion_jurada': True,
            'segmento': 'vip'
        }


@pytest.mark.django_db
class TestClienteCrearView(TestBaseClienteView):
    """
    Tests para la vista de crear cliente
    """
    
    def test_acceso_sin_autenticacion(self):
        """Test para verificar que requiere autenticación"""
        url = reverse('clientes:cliente_crear')
        response = self.client.get(url)
        
        assert response.status_code == 302
        assert '/login/' in response.url
        print("✓ Test acceso_sin_autenticacion: Redirige a login correctamente")
    
    def test_acceso_sin_permisos(self):
        """Test para verificar que requiere permisos de gestión"""
        self.client.login(username='usuario', password='usuario123')
        url = reverse('clientes:cliente_crear')
        response = self.client.get(url)
        
        assert response.status_code == 403
        print("✓ Test acceso_sin_permisos: Devuelve 403 correctamente")
    
    def test_acceso_con_permisos(self):
        """Test para verificar acceso con permisos correctos"""
        self.client.login(username='admin', password='admin123')
        url = reverse('clientes:cliente_crear')
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert 'form' in response.content.decode()
        print("✓ Test acceso_con_permisos: Acceso permitido con permisos")
    
    def test_crear_cliente_valido(self):
        """Test para crear cliente con datos válidos"""
        self.client.login(username='admin', password='admin123')
        url = reverse('clientes:cliente_crear')
        
        response = self.client.post(url, data=self.datos_cliente_validos)
        
        # Verificar que se creó el cliente
        assert Cliente.objects.filter(docCliente='0987654321').exists()
        
        # Verificar redirección
        cliente = Cliente.objects.get(docCliente='0987654321')
        assert response.status_code == 302
        assert f'/clientes/{cliente.pk}/' in response.url
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        assert any('exitosamente' in str(m) for m in messages)
        
        print("✓ Test crear_cliente_valido: Cliente creado correctamente")
    
    def test_crear_cliente_datos_invalidos(self):
        """Test para crear cliente con datos inválidos"""
        self.client.login(username='admin', password='admin123')
        url = reverse('clientes:cliente_crear')
        
        datos_invalidos = self.datos_cliente_validos.copy()
        datos_invalidos['correoElecCliente'] = 'correo_invalido'
        datos_invalidos['telefono'] = 'abc123'
        
        response = self.client.post(url, data=datos_invalidos)
        
        # Verificar que no se creó el cliente
        assert not Cliente.objects.filter(docCliente='0987654321').exists()
        
        # Verificar que muestra errores del formulario
        assert response.status_code == 200
        content = response.content.decode()
        assert 'correo electrónico válido' in content
        assert 'solo números' in content
        
        print("✓ Test crear_cliente_datos_invalidos: Validación de datos funcionando")


@pytest.mark.django_db  
class TestClienteListaView(TestBaseClienteView):
    """
    Tests para la vista de lista de clientes
    """
    
    def test_acceso_sin_autenticacion(self):
        """Test para verificar que requiere autenticación"""
        url = reverse('clientes:cliente_lista')
        response = self.client.get(url)
        
        assert response.status_code == 302
        assert '/login/' in response.url
        print("✓ Test acceso_sin_autenticacion: Redirige a login correctamente")
    
    def test_acceso_sin_permisos(self):
        """Test para verificar que requiere permisos de gestión"""
        self.client.login(username='usuario', password='usuario123')
        url = reverse('clientes:cliente_lista')
        response = self.client.get(url)
        
        assert response.status_code == 403
        print("✓ Test acceso_sin_permisos: Devuelve 403 correctamente")
    
    def test_lista_vacia(self):
        """Test para lista vacía"""
        # Eliminar cliente creado en setup
        Cliente.objects.all().delete()
        
        self.client.login(username='admin', password='admin123')
        url = reverse('clientes:cliente_lista')
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert 'No hay clientes' in response.content.decode()
        print("✓ Test lista_vacia: Mensaje de lista vacía mostrado")
    
    def test_lista_con_clientes(self):
        """Test para lista con clientes"""
        self.client.login(username='admin', password='admin123')
        url = reverse('clientes:cliente_lista')
        response = self.client.get(url)
        
        assert response.status_code == 200
        content = response.content.decode()
        assert self.cliente.nombre in content
        assert self.cliente.docCliente in content
        print("✓ Test lista_con_clientes: Lista de clientes mostrada correctamente")
    
    def test_filtro_por_segmento(self):
        """Test para filtro por segmento"""
        # Crear cliente VIP
        cliente_vip = Cliente.objects.create(
            nombre='Cliente VIP',
            tipoDocCliente='CI',
            docCliente='5555555555',
            correoElecCliente='vip@example.com',
            telefono='0985555555',
            tipoCliente='F',
            direccion='Asunción',
            ocupacion='CEO',
            segmento='vip'
        )
        
        self.client.login(username='admin', password='admin123')
        url = reverse('clientes:cliente_lista')
        
        # Filtrar por segmento VIP
        response = self.client.get(url, {'segmento': 'vip'})
        
        assert response.status_code == 200
        content = response.content.decode()
        assert cliente_vip.nombre in content
        assert self.cliente.nombre not in content
        
        print("✓ Test filtro_por_segmento: Filtro por segmento funcionando")
    
    def test_busqueda_por_nombre(self):
        """Test para búsqueda por nombre"""
        self.client.login(username='admin', password='admin123')
        url = reverse('clientes:cliente_lista')
        
        response = self.client.get(url, {'busqueda': 'Juan'})
        
        assert response.status_code == 200
        assert self.cliente.nombre in response.content.decode()
        
        # Buscar nombre que no existe
        response = self.client.get(url, {'busqueda': 'NoExiste'})
        assert self.cliente.nombre not in response.content.decode()
        
        print("✓ Test busqueda_por_nombre: Búsqueda por nombre funcionando")
    
    def test_busqueda_por_documento(self):
        """Test para búsqueda por documento"""
        self.client.login(username='admin', password='admin123')
        url = reverse('clientes:cliente_lista')
        
        response = self.client.get(url, {'busqueda': '1234567890'})
        
        assert response.status_code == 200
        assert self.cliente.nombre in response.content.decode()
        
        print("✓ Test busqueda_por_documento: Búsqueda por documento funcionando")


@pytest.mark.django_db
class TestClienteDetalleView(TestBaseClienteView):
    """
    Tests para la vista de detalle de cliente
    """
    
    def test_acceso_sin_autenticacion(self):
        """Test para verificar que requiere autenticación"""
        url = reverse('clientes:cliente_detalle', kwargs={'pk': self.cliente.pk})
        response = self.client.get(url)
        
        assert response.status_code == 302
        assert '/login/' in response.url
        print("✓ Test acceso_sin_autenticacion: Redirige a login correctamente")
    
    def test_acceso_administrador(self):
        """Test para acceso de administrador"""
        self.client.login(username='admin', password='admin123')
        url = reverse('clientes:cliente_detalle', kwargs={'pk': self.cliente.pk})
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert self.cliente.nombre in response.content.decode()
        print("✓ Test acceso_administrador: Administrador puede ver cliente")
    
    def test_acceso_operador_asociado(self):
        """Test para acceso de operador asociado al cliente"""
        self.client.login(username='operador', password='operador123')
        url = reverse('clientes:cliente_detalle', kwargs={'pk': self.cliente.pk})
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert self.cliente.nombre in response.content.decode()
        print("✓ Test acceso_operador_asociado: Operador asociado puede ver cliente")
    
    def test_acceso_denegado_usuario_sin_permisos(self):
        """Test para denegar acceso a usuario sin permisos"""
        self.client.login(username='usuario', password='usuario123')
        url = reverse('clientes:cliente_detalle', kwargs={'pk': self.cliente.pk})
        response = self.client.get(url)
        
        assert response.status_code == 302
        
        # Verificar mensaje de error
        messages = list(get_messages(response.wsgi_request))
        assert any('No tienes permisos' in str(m) for m in messages)
        
        print("✓ Test acceso_denegado_usuario_sin_permisos: Acceso denegado correctamente")
    
    def test_cliente_no_existe(self):
        """Test para cliente que no existe"""
        self.client.login(username='admin', password='admin123')
        url = reverse('clientes:cliente_detalle', kwargs={'pk': 99999})
        response = self.client.get(url)
        
        assert response.status_code == 404
        print("✓ Test cliente_no_existe: Devuelve 404 para cliente inexistente")


@pytest.mark.django_db
class TestClienteEditarView(TestBaseClienteView):
    """
    Tests para la vista de editar cliente
    """
    
    def test_acceso_sin_autenticacion(self):
        """Test para verificar que requiere autenticación"""
        url = reverse('clientes:cliente_editar', kwargs={'pk': self.cliente.pk})
        response = self.client.get(url)
        
        assert response.status_code == 302
        assert '/login/' in response.url
        print("✓ Test acceso_sin_autenticacion: Redirige a login correctamente")
    
    def test_acceso_sin_permisos(self):
        """Test para verificar que requiere permisos de gestión"""
        self.client.login(username='operador', password='operador123')
        url = reverse('clientes:cliente_editar', kwargs={'pk': self.cliente.pk})
        response = self.client.get(url)
        
        assert response.status_code == 403
        print("✓ Test acceso_sin_permisos: Devuelve 403 correctamente")
    
    def test_editar_cliente_get(self):
        """Test para mostrar formulario de edición"""
        self.client.login(username='admin', password='admin123')
        url = reverse('clientes:cliente_editar', kwargs={'pk': self.cliente.pk})
        response = self.client.get(url)
        
        assert response.status_code == 200
        content = response.content.decode()
        assert self.cliente.nombre in content
        assert self.cliente.correoElecCliente in content
        print("✓ Test editar_cliente_get: Formulario de edición mostrado correctamente")
    
    def test_editar_cliente_post_valido(self):
        """Test para editar cliente con datos válidos"""
        self.client.login(username='admin', password='admin123')
        url = reverse('clientes:cliente_editar', kwargs={'pk': self.cliente.pk})
        
        datos_editados = {
            'nombre': 'Juan Carlos Pérez',
            'tipoDocCliente': 'CI',
            'docCliente': '1234567890',  # Mismo documento
            'correoElecCliente': 'juan.carlos@example.com',
            'telefono': '0981999888',
            'tipoCliente': 'F',
            'direccion': 'Nueva dirección',
            'ocupacion': 'Ingeniero Senior',
            'declaracion_jurada': True,
            'segmento': 'corporativo'
        }
        
        response = self.client.post(url, data=datos_editados)
        
        # Verificar redirección
        assert response.status_code == 302
        assert f'/clientes/{self.cliente.pk}/' in response.url
        
        # Verificar que se actualizó
        self.cliente.refresh_from_db()
        assert self.cliente.nombre == 'Juan Carlos Pérez'
        assert self.cliente.correoElecCliente == 'juan.carlos@example.com'
        assert self.cliente.beneficio_segmento == 5  # Corporativo = 5%
        
        print("✓ Test editar_cliente_post_valido: Cliente editado correctamente")
    
    def test_editar_cliente_post_invalido(self):
        """Test para editar cliente con datos inválidos"""
        self.client.login(username='admin', password='admin123')
        url = reverse('clientes:cliente_editar', kwargs={'pk': self.cliente.pk})
        
        datos_invalidos = {
            'nombre': '',  # Nombre vacío
            'tipoDocCliente': 'CI',
            'docCliente': '1234567890',
            'correoElecCliente': 'correo_invalido',  # Correo inválido
            'telefono': 'abc123',  # Teléfono inválido
            'tipoCliente': 'F',
            'direccion': 'Dirección',
            'ocupacion': 'Ocupación',
            'segmento': 'minorista'
        }
        
        response = self.client.post(url, data=datos_invalidos)
        
        # Verificar que no se actualizó
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Debes ingresar el nombre' in content
        assert 'correo electrónico válido' in content
        assert 'solo números' in content
        
        print("✓ Test editar_cliente_post_invalido: Validación de datos funcionando")


@pytest.mark.django_db
class TestFuncionesAuxiliares(TestBaseClienteView):
    """
    Tests para funciones auxiliares de las vistas
    """
    
    def test_verificar_acceso_cliente_administrador(self):
        """Test para verificar acceso de administrador"""
        from clientes.views import verificar_acceso_cliente
        
        tiene_acceso = verificar_acceso_cliente(self.admin_user, self.cliente)
        assert tiene_acceso
        print("✓ Test verificar_acceso_cliente_administrador: Administrador tiene acceso")
    
    def test_verificar_acceso_cliente_operador_asociado(self):
        """Test para verificar acceso de operador asociado"""
        from clientes.views import verificar_acceso_cliente
        
        tiene_acceso = verificar_acceso_cliente(self.operador_user, self.cliente)
        assert tiene_acceso
        print("✓ Test verificar_acceso_cliente_operador_asociado: Operador asociado tiene acceso")
    
    def test_verificar_acceso_cliente_sin_permisos(self):
        """Test para verificar que usuario sin permisos no tiene acceso"""
        from clientes.views import verificar_acceso_cliente
        
        tiene_acceso = verificar_acceso_cliente(self.user_sin_permisos, self.cliente)
        assert not tiene_acceso
        print("✓ Test verificar_acceso_cliente_sin_permisos: Usuario sin permisos no tiene acceso")
    
    def test_procesar_medios_pago_cliente_administrador(self):
        """Test para procesar medios de pago como administrador"""
        from clientes.views import procesar_medios_pago_cliente
        
        # Crear medio de pago para testing
        medio_pago = MedioPago.objects.create(
            tipo='tarjeta_credito',
            nombre='Tarjeta de Crédito'
        )
        
        MedioPagoCliente.objects.create(
            cliente=self.cliente,
            medio_pago=medio_pago,
            numero_tarjeta='1234567812345678',
            cvv_tarjeta='123',
            activo=True
        )
        
        resultado = procesar_medios_pago_cliente(self.cliente, self.admin_user)
        
        assert resultado['es_administrador']
        assert 'medios_pago' in resultado
        
        print("✓ Test procesar_medios_pago_cliente_administrador: Procesamiento para admin funcionando")
    
    def test_procesar_medios_pago_cliente_operador(self):
        """Test para procesar medios de pago como operador"""
        from clientes.views import procesar_medios_pago_cliente
        
        # Crear medio de pago para testing
        medio_pago = MedioPago.objects.create(
            tipo='tarjeta_credito',
            nombre='Tarjeta de Crédito'
        )
        
        medio_cliente = MedioPagoCliente.objects.create(
            cliente=self.cliente,
            medio_pago=medio_pago,
            numero_tarjeta='1234567812345678',
            cvv_tarjeta='123',
            activo=True
        )
        
        resultado = procesar_medios_pago_cliente(self.cliente, self.operador_user)
        
        assert not resultado['es_administrador']
        
        # Verificar que los datos sensibles están ocultos
        medios = resultado['medios_pago']
        if medios:
            medio = medios[0]
            assert medio.numero_tarjeta_oculto == '**** **** **** 5678'
            assert medio.cvv_tarjeta_oculto == '***'
        
        print("✓ Test procesar_medios_pago_cliente_operador: Datos sensibles ocultos para operador")