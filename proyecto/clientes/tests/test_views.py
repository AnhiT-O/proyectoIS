import pytest
from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from clientes.models import Cliente, UsuarioCliente
from medios_pago.models import MedioPago, MedioPagoCliente

User = get_user_model()


@pytest.mark.django_db
class TestClienteViews:
    
    def setup_method(self):
        """Configuración inicial para cada test"""
        self.client = Client()
        
        # Crear usuario con permisos de gestión de clientes
        self.user_admin = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='1234567',
            is_active=True
        )
        self.user_admin.set_password('testpass123')
        self.user_admin.save()
        
        # Crear usuario sin permisos
        self.user_operador = User(
            username='operador',
            email='operador@example.com',
            first_name='Operador',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='7654321',
            is_active=True
        )
        self.user_operador.set_password('testpass123')
        self.user_operador.save()
        
        # Asignar permiso de gestión de clientes al admin
        from django.contrib.contenttypes.models import ContentType
        cliente_content_type = ContentType.objects.get_for_model(Cliente)
        perm_gestion, created = Permission.objects.get_or_create(
            codename='gestion',
            name='Puede gestionar clientes (crear y editar)',
            content_type=cliente_content_type
        )
        self.user_admin.user_permissions.add(perm_gestion)
        
        # Crear cliente de prueba
        self.cliente = Cliente.objects.create(
            nombre='Cliente Prueba',
            tipoDocCliente='CI',
            docCliente='1111111',
            correoElecCliente='cliente@example.com',
            telefono='0981123456',
            tipoCliente='F',
            direccion='Asunción',
            ocupacion='Empleado',
            segmento='minorista'
        )

    def test_vista_cliente_crear_solo_usuarios_con_permiso_pueden_crear(self):
        """Prueba 9: Vista cliente_crear: solo usuarios con permiso pueden crear clientes."""
        
        # Usuario sin permisos intenta acceder
        self.client.login(username='operador', password='testpass123')
        response = self.client.get(reverse('clientes:cliente_crear'))
        assert response.status_code == 403  # Forbidden
        
        # Usuario con permisos puede acceder
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('clientes:cliente_crear'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_vista_cliente_crear_muestra_errores_si_datos_invalidos(self):
        """Prueba 10: Vista cliente_crear: muestra errores si los datos del formulario son inválidos."""
        
        self.client.login(username='admin', password='testpass123')
        
        # Datos inválidos (documento no numérico)
        form_data = {
            'nombre': 'Test Cliente',
            'tipoDocCliente': 'CI',
            'docCliente': '123ABC',  # Inválido
            'correoElecCliente': 'test@example.com',
            'telefono': '0981123456',
            'tipoCliente': 'F',
            'direccion': 'Test Address',
            'ocupacion': 'Test Job',
            'segmento': 'minorista',
        }
        
        response = self.client.post(reverse('clientes:cliente_crear'), data=form_data)
        
        # Debe volver al formulario con errores
        assert response.status_code == 200
        assert 'form' in response.context
        assert not response.context['form'].is_valid()
        assert 'docCliente' in response.context['form'].errors

    def test_vista_cliente_lista_filtra_correctamente_por_segmento(self):
        """Prueba 11: Vista cliente_lista: filtra correctamente por segmento."""
        
        self.client.login(username='admin', password='testpass123')
        
        # Crear clientes con diferentes segmentos
        Cliente.objects.create(
            nombre='Cliente VIP',
            tipoDocCliente='CI',
            docCliente='2222222',
            correoElecCliente='vip@example.com',
            telefono='0981111111',
            tipoCliente='F',
            direccion='Asunción',
            ocupacion='Ejecutivo',
            segmento='vip'
        )
        
        Cliente.objects.create(
            nombre='Cliente Corporativo',
            tipoDocCliente='RUC',
            docCliente='80012345-1',
            correoElecCliente='corp@example.com',
            telefono='0981222222',
            tipoCliente='J',
            direccion='Asunción',
            ocupacion='Empresa',
            segmento='corporativo'
        )
        
        # Filtrar por segmento VIP
        response = self.client.get(reverse('clientes:cliente_lista') + '?segmento=vip')
        assert response.status_code == 200
        clientes = response.context['clientes']
        assert clientes.count() == 1
        assert clientes.first().segmento == 'vip'

    def test_vista_cliente_lista_filtra_correctamente_por_busqueda(self):
        """Prueba 11: Vista cliente_lista: filtra correctamente por búsqueda."""
        
        self.client.login(username='admin', password='testpass123')
        
        # Búsqueda por nombre
        response = self.client.get(reverse('clientes:cliente_lista') + '?busqueda=Cliente Prueba')
        assert response.status_code == 200
        clientes = response.context['clientes']
        assert clientes.count() == 1
        assert 'Cliente Prueba' in clientes.first().nombre

    def test_vista_cliente_detalle_usuarios_asociados_pueden_ver_detalle(self):
        """Prueba 12: Vista cliente_detalle: usuarios asociados pueden ver el detalle."""
        
        # Asociar usuario operador al cliente
        UsuarioCliente.objects.create(
            usuario=self.user_operador,
            cliente=self.cliente
        )
        
        self.client.login(username='operador', password='testpass123')
        response = self.client.get(reverse('clientes:cliente_detalle', kwargs={'pk': self.cliente.pk}))
        assert response.status_code == 200
        assert response.context['cliente'] == self.cliente

    def test_vista_cliente_detalle_usuarios_con_permiso_pueden_ver_detalle(self):
        """Prueba 12: Vista cliente_detalle: usuarios con permiso pueden ver el detalle."""
        
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('clientes:cliente_detalle', kwargs={'pk': self.cliente.pk}))
        assert response.status_code == 200
        assert response.context['cliente'] == self.cliente

    def test_vista_cliente_agregar_tarjeta_limite_maximo_3_tarjetas(self):
        """Prueba 13: Vista cliente_agregar_tarjeta: no permite agregar más de 3 tarjetas activas por cliente."""
        
        self.client.login(username='admin', password='testpass123')
        
        # Crear medio de pago tarjeta
        medio_tarjeta, _ = MedioPago.objects.get_or_create(
            tipo='tarjeta_credito',
            defaults={'activo': True}
        )
        
        # Crear 3 tarjetas para el cliente
        for i in range(3):
            MedioPagoCliente.objects.create(
                medio_pago=medio_tarjeta,
                cliente=self.cliente,
                numero_tarjeta=f'123456789012345{i}',
                cvv_tarjeta='123',
                nombre_titular_tarjeta='Test User',
                fecha_vencimiento_tc='12/25',
                descripcion_tarjeta=f'Tarjeta {i+1}',
                activo=True,
                is_deleted=False
            )
        
        # Intentar agregar una cuarta tarjeta
        response = self.client.get(reverse('clientes:cliente_agregar_tarjeta', kwargs={'pk': self.cliente.pk}))
        
        # Debe redirigir con mensaje de error
        assert response.status_code == 302
        messages = list(get_messages(response.wsgi_request))
        assert any('máximo de 3 tarjetas' in str(message) for message in messages)

    def test_vista_cliente_agregar_cuenta_no_duplica_cuentas(self):
        """Prueba 14: Vista cliente_agregar_cuenta: no permite duplicar cuentas bancarias para el mismo cliente."""
        
        self.client.login(username='admin', password='testpass123')
        
        # Crear medio de pago transferencia
        medio_transferencia, _ = MedioPago.objects.get_or_create(
            tipo='transferencia',
            defaults={'activo': True}
        )
        
        # Crear cuenta existente
        MedioPagoCliente.objects.create(
            medio_pago=medio_transferencia,
            cliente=self.cliente,
            numero_cuenta='1234567890',
            nombre_titular_cuenta='TEST USER',  # El formulario convierte a mayúsculas
            banco='Banco Test',  # El formulario convierte a Title Case
            tipo_cuenta='ahorro',
            activo=True,
            is_deleted=False
        )
        
        # Intentar crear cuenta con datos idénticos
        form_data = {
            'numero_cuenta': '1234567890',
            'nombre_titular_cuenta': 'Test User',
            'banco': 'Banco Test',
            'tipo_cuenta': 'ahorro',
        }
        
        response = self.client.post(
            reverse('clientes:cliente_agregar_cuenta', kwargs={'pk': self.cliente.pk}),
            data=form_data
        )
        
        # Debe redirigir con mensaje de advertencia sobre cuenta existente
        assert response.status_code == 302
        messages = list(get_messages(response.wsgi_request))
        assert any('ya está activa' in str(message) for message in messages)

    def test_vista_cliente_cambiar_estado_medio_pago_activa_desactiva(self):
        """Prueba 15: Vista cliente_cambiar_estado_medio_pago: activa/desactiva correctamente el medio de pago del cliente."""
        
        self.client.login(username='admin', password='testpass123')
        
        # Crear medio de pago
        medio_efectivo, _ = MedioPago.objects.get_or_create(
            tipo='efectivo',
            defaults={'activo': True}
        )
        
        # Crear medio de pago para cliente (activo inicialmente)
        medio_cliente = MedioPagoCliente.objects.create(
            medio_pago=medio_efectivo,
            cliente=self.cliente,
            activo=True,
            is_deleted=False
        )
        
        # Cambiar estado a inactivo
        response = self.client.post(
            reverse('clientes:cliente_cambiar_estado_medio_pago', 
                   kwargs={'pk': self.cliente.pk, 'medio_id': medio_cliente.id})
        )
        
        # Verificar redirección
        assert response.status_code == 302
        
        # Verificar que el estado cambió
        medio_cliente.refresh_from_db()
        assert not medio_cliente.activo
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        assert any('desactivado exitosamente' in str(message) for message in messages)
        
        # Cambiar estado de vuelta a activo
        response = self.client.post(
            reverse('clientes:cliente_cambiar_estado_medio_pago', 
                   kwargs={'pk': self.cliente.pk, 'medio_id': medio_cliente.id})
        )
        
        # Verificar que el estado cambió de nuevo
        medio_cliente.refresh_from_db()
        assert medio_cliente.activo
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        assert any('activado exitosamente' in str(message) for message in messages)
