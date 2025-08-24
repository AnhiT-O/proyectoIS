import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from clientes.models import Cliente, UsuarioCliente
from usuarios.models import Usuario


class TestClienteModel(TestCase):
    """Pruebas para el modelo Cliente"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.cliente_data = {
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'tipoDocCliente': 'CI',
            'docCliente': '12345678',
            'correoElecCliente': 'juan.perez@example.com',
            'telefono': '0981123456',
            'tipoCliente': 'F',
            'direccion': 'Asunción, Paraguay',
            'ocupacion': 'Ingeniero'
        }
    
    def test_crear_cliente_valido(self):
        """Test crear cliente con datos válidos"""
        cliente = Cliente.objects.create(**self.cliente_data)
        
        self.assertEqual(cliente.nombre, 'Juan')
        self.assertEqual(cliente.apellido, 'Pérez')
        self.assertEqual(cliente.docCliente, '12345678')
        self.assertEqual(str(cliente), 'Juan Pérez')
    
    def test_cliente_str_representation(self):
        """Test representación en string del cliente"""
        cliente = Cliente.objects.create(**self.cliente_data)
        self.assertEqual(str(cliente), 'Juan Pérez')
    
    def test_documento_cliente_unico(self):
        """Test que el documento del cliente debe ser único"""
        Cliente.objects.create(**self.cliente_data)
        
        # Intentar crear otro cliente con el mismo documento
        cliente_duplicado = self.cliente_data.copy()
        cliente_duplicado['correoElecCliente'] = 'otro@example.com'
        
        with self.assertRaises(IntegrityError):
            Cliente.objects.create(**cliente_duplicado)
    
    def test_correo_cliente_unico(self):
        """Test que el correo del cliente debe ser único"""
        Cliente.objects.create(**self.cliente_data)
        
        # Intentar crear otro cliente con el mismo correo
        cliente_duplicado = self.cliente_data.copy()
        cliente_duplicado['docCliente'] = '87654321'
        
        with self.assertRaises(IntegrityError):
            Cliente.objects.create(**cliente_duplicado)
    
    def test_campos_opcionales(self):
        """Test que los campos opcionales pueden ser nulos"""
        cliente_data_minimo = self.cliente_data.copy()
        cliente_data_minimo['direccion'] = None
        cliente_data_minimo['ocupacion'] = None
        
        cliente = Cliente.objects.create(**cliente_data_minimo)
        self.assertIsNone(cliente.direccion)
        self.assertIsNone(cliente.ocupacion)
    
    def test_declaracion_jurada_default_false(self):
        """Test que declaración jurada tiene valor por defecto False"""
        cliente = Cliente.objects.create(**self.cliente_data)
        self.assertFalse(cliente.declaracion_jurada)


class TestUsuarioClienteModel(TestCase):
    """Pruebas para el modelo UsuarioCliente"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='11111111'
        )
        
        self.cliente = Cliente.objects.create(
            nombre='Juan',
            apellido='Pérez',
            tipoDocCliente='CI',
            docCliente='12345678',
            correoElecCliente='juan.perez@example.com',
            telefono='0981123456',
            tipoCliente='F'
        )
    
    def test_crear_relacion_usuario_cliente(self):
        """Test crear relación usuario-cliente"""
        relacion = UsuarioCliente.objects.create(
            usuario=self.usuario,
            cliente=self.cliente
        )
        
        self.assertEqual(relacion.usuario, self.usuario)
        self.assertEqual(relacion.cliente, self.cliente)
        self.assertEqual(str(relacion), f"{self.usuario.email} - {self.cliente.nombre}")
    
    def test_relacion_usuario_cliente_unica(self):
        """Test que la relación usuario-cliente debe ser única"""
        UsuarioCliente.objects.create(
            usuario=self.usuario,
            cliente=self.cliente
        )
        
        # Intentar crear relación duplicada
        with self.assertRaises(IntegrityError):
            UsuarioCliente.objects.create(
                usuario=self.usuario,
                cliente=self.cliente
            )
    
    def test_str_representation(self):
        """Test representación en string de la relación"""
        relacion = UsuarioCliente.objects.create(
            usuario=self.usuario,
            cliente=self.cliente
        )
        
        expected = f"{self.usuario.email} - {self.cliente.nombre}"
        self.assertEqual(str(relacion), expected)
