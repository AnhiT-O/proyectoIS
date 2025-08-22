from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from clientes.models import Cliente

class ClienteViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@test.com'
        )
        self.cliente = Cliente.objects.create(
            nombre="Test",
            tipo="Persona",
            email="cliente@test.com",
            telefono="123456789",
            direccion="Test Address"
        )
        self.client.login(username='testuser', password='testpass123')

    def test_cliente_lista_view(self):
        response = self.client.get(reverse('clientes:cliente_lista'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'clientes/cliente_lista.html')
        self.assertContains(response, self.cliente.nombre)

    def test_cliente_detalle_view(self):
        response = self.client.get(
            reverse('clientes:cliente_detalle', kwargs={'pk': self.cliente.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'clientes/cliente_detalle.html')
        self.assertContains(response, self.cliente.nombre)

    def test_cliente_crear_view(self):
        response = self.client.get(reverse('clientes:cliente_crear'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'clientes/cliente_form.html')

        # Test POST
        data = {
            'nombre': 'Nuevo Cliente',
            'tipo': 'Empresa',
            'email': 'nuevo@test.com',
            'telefono': '987654321',
            'direccion': 'Nueva dirección'
        }
        response = self.client.post(reverse('clientes:cliente_crear'), data)
        self.assertEqual(response.status_code, 302)  # Redirección después de crear
        self.assertTrue(Cliente.objects.filter(email='nuevo@test.com').exists())