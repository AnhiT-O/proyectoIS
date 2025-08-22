import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Group
from django.contrib import messages
from unittest.mock import patch
from usuarios.models import Usuario
from clientes.models import Cliente
from clientes.views import es_administrador


class TestClienteViews(TestCase):
    """Pruebas para las vistas de clientes"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.client = Client()
        
        # Crear grupo administrador
        self.admin_group, _ = Group.objects.get_or_create(name='administrador')
        
        # Crear usuario administrador
        self.admin_user = Usuario.objects.create_user(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='11111111',
            password='testpass123!'
        )
        self.admin_user.groups.add(self.admin_group)
        
        # Crear usuario no administrador
        self.regular_user = Usuario.objects.create_user(
            username='regular',
            email='regular@example.com',
            first_name='Regular',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='22222222',
            password='testpass123!'
        )
        
        # Crear cliente de prueba
        self.cliente = Cliente.objects.create(
            nombre='Juan',
            apellido='Pérez',
            tipoDocCliente='CI',
            docCliente='12345678',
            correoElecCliente='juan.perez@example.com',
            telefono='0981123456',
            tipoCliente='F',
            direccion='Asunción'
        )
    
    def test_es_administrador_function(self):
        """Test función es_administrador"""
        # Usuario administrador
        self.assertTrue(es_administrador(self.admin_user))
        
        # Usuario regular
        self.assertFalse(es_administrador(self.regular_user))
        
        # Usuario no autenticado
        from django.contrib.auth.models import AnonymousUser
        anonymous_user = AnonymousUser()
        self.assertFalse(es_administrador(anonymous_user))
    
    def test_cliente_lista_sin_autenticar(self):
        """Test acceso a lista de clientes sin autenticar"""
        url = reverse('clientes:cliente_lista')
        response = self.client.get(url)
        
        # Debe redirigir al login
        self.assertRedirects(response, f'/usuarios/login/?next={url}')
    
    def test_cliente_lista_usuario_regular(self):
        """Test acceso a lista de clientes con usuario regular"""
        self.client.login(username='regular', password='testpass123!')
        url = reverse('clientes:cliente_lista')
        response = self.client.get(url)
        
        # Debe devolver 403 (PermissionDenied)
        self.assertEqual(response.status_code, 403)
    
    def test_cliente_lista_admin(self):
        """Test acceso a lista de clientes con administrador"""
        self.client.login(username='admin', password='testpass123!')
        url = reverse('clientes:cliente_lista')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Juan Pérez')
        self.assertIn('clientes', response.context)
    
    def test_cliente_crear_get(self):
        """Test GET para crear cliente"""
        self.client.login(username='admin', password='testpass123!')
        url = reverse('clientes:cliente_crear')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
    
    def test_cliente_crear_post_valido(self):
        """Test POST para crear cliente con datos válidos"""
        self.client.login(username='admin', password='testpass123!')
        url = reverse('clientes:cliente_crear')
        
        data = {
            'nombre': 'María',
            'apellido': 'González',
            'tipoDocCliente': 'CI',
            'docCliente': '87654321',
            'correoElecCliente': 'maria@example.com',
            'telefono': '0981654321',
            'tipoCliente': 'F',
            'direccion': 'Ciudad del Este',
            'ocupacion': 'Doctora',
            'declaracion_jurada': True
        }
        
        response = self.client.post(url, data)
        
        # Verificar que se creó el cliente
        self.assertTrue(Cliente.objects.filter(docCliente='87654321').exists())
        
        # Verificar redirección
        cliente = Cliente.objects.get(docCliente='87654321')
        self.assertRedirects(response, reverse('clientes:cliente_detalle', args=[cliente.pk]))
    
    def test_cliente_detalle(self):
        """Test vista de detalle de cliente"""
        self.client.login(username='admin', password='testpass123!')
        url = reverse('clientes:cliente_detalle', args=[self.cliente.pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Juan Pérez')
        self.assertEqual(response.context['cliente'], self.cliente)
    
    def test_cliente_editar_get(self):
        """Test GET para editar cliente"""
        self.client.login(username='admin', password='testpass123!')
        url = reverse('clientes:cliente_editar', args=[self.cliente.pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertEqual(response.context['cliente'], self.cliente)
    
    def test_cliente_editar_post(self):
        """Test POST para editar cliente"""
        self.client.login(username='admin', password='testpass123!')
        url = reverse('clientes:cliente_editar', args=[self.cliente.pk])
        
        data = {
            'nombre': 'Juan Carlos',
            'apellido': 'Pérez',
            'tipoDocCliente': 'CI',
            'docCliente': '12345678',
            'correoElecCliente': 'juan.perez@example.com',
            'telefono': '0981123456',
            'tipoCliente': 'F',
            'direccion': 'Asunción Actualizada',
            'ocupacion': 'Ingeniero Senior',
            'declaracion_jurada': True
        }
        
        response = self.client.post(url, data)
        
        # Verificar que se actualizó
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.nombre, 'Juan Carlos')
        self.assertEqual(self.cliente.direccion, 'Asunción Actualizada')
        
        self.assertRedirects(response, reverse('clientes:cliente_detalle', args=[self.cliente.pk]))
    
    def test_cliente_eliminar_get(self):
        """Test GET para confirmar eliminación"""
        self.client.login(username='admin', password='testpass123!')
        url = reverse('clientes:cliente_eliminar', args=[self.cliente.pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Juan Pérez')
    
    def test_cliente_eliminar_post(self):
        """Test POST para eliminar cliente"""
        self.client.login(username='admin', password='testpass123!')
        url = reverse('clientes:cliente_eliminar', args=[self.cliente.pk])
        
        response = self.client.post(url)
        
        # Verificar que se eliminó
        self.assertFalse(Cliente.objects.filter(pk=self.cliente.pk).exists())
        
        self.assertRedirects(response, reverse('clientes:cliente_lista'))
    
    def test_cliente_no_existe(self):
        """Test acceso a cliente que no existe"""
        self.client.login(username='admin', password='testpass123!')
        url = reverse('clientes:cliente_detalle', args=[9999])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
