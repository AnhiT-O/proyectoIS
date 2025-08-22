from django.test import TestCase
from django.db import IntegrityError
from clientes.models import Cliente, UsuarioCliente
from usuarios.models import Usuario

class ClienteModelTest(TestCase):
    def setUp(self):
        self.cliente_data = {
            'nombre': 'Test',
            'apellido': 'Usuario',
            'tipoDocCliente': 'CI',
            'docCliente': '1234567',
            'correoElecCliente': 'test@test.com',
            'telefono': '0981123456',
            'tipoCliente': 'F'
        }
        self.cliente = Cliente.objects.create(**self.cliente_data)
        
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            password='testpass123',
            email='user@test.com'
        )

    def test_cliente_creation(self):
        """Test cliente creation with valid data"""
        self.assertTrue(isinstance(self.cliente, Cliente))
        self.assertEqual(self.cliente.__str__(), f"{self.cliente.nombre} {self.cliente.apellido}")

    def test_documento_unique(self):
        """Test that docCliente must be unique"""
        with self.assertRaises(IntegrityError):
            Cliente.objects.create(**self.cliente_data)

    def test_email_unique(self):
        """Test that correoElecCliente must be unique"""
        self.cliente_data['docCliente'] = '7654321'
        with self.assertRaises(IntegrityError):
            Cliente.objects.create(**self.cliente_data)

class UsuarioClienteModelTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nombre='Test',
            apellido='Usuario',
            tipoDocCliente='CI',
            docCliente='1234567',
            correoElecCliente='test@test.com',
            telefono='0981123456',
            tipoCliente='F'
        )
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            password='testpass123',
            email='user@test.com'
        )

    def test_usuario_cliente_relation(self):
        """Test creation of usuario-cliente relation"""
        relacion = UsuarioCliente.objects.create(
            usuario=self.usuario,
            cliente=self.cliente
        )
        self.assertIn(self.usuario, self.cliente.usuarios.all())
        self.assertIn(self.cliente, self.usuario.clientes_operados.all())

    def test_unique_relation(self):
        """Test that usuario-cliente relation must be unique"""
        UsuarioCliente.objects.create(
            usuario=self.usuario,
            cliente=self.cliente
        )
        with self.assertRaises(IntegrityError):
            UsuarioCliente.objects.create(
                usuario=self.usuario,
                cliente=self.cliente
            )