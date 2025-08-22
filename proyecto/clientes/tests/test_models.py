from django.test import TestCase
from django.db import IntegrityError
from clientes.models import Cliente
from usuarios.models import Usuario

class ClienteModelTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nombre="Test",
            tipo="Persona",
            email="test@test.com",
            telefono="123456789",
            direccion="Test Address"
        )
        
        self.usuario = Usuario.objects.create_user(
            username="testuser",
            password="testpass123",
            email="user@test.com"
        )

    def test_cliente_creation(self):
        self.assertTrue(isinstance(self.cliente, Cliente))
        self.assertEqual(self.cliente.__str__(), f"{self.cliente.nombre}")

    def test_email_unique(self):
        with self.assertRaises(IntegrityError):
            Cliente.objects.create(
                nombre="Test2",
                tipo="Persona",
                email="test@test.com",
                telefono="987654321"
            )

    def test_cliente_usuario_relation(self):
        self.cliente.usuarios.add(self.usuario)
        self.assertIn(self.usuario, self.cliente.usuarios.all())
        self.assertIn(self.cliente, self.usuario.clientes.all())