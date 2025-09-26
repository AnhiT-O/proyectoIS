import pytest
from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from clientes.models import Cliente, UsuarioCliente

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


