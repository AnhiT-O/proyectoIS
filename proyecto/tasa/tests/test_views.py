"""
Test unitarios para las vistas de TasaCambio.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from decimal import Decimal
from ..models import TasaCambio
from monedas.models import Moneda

class TasaCambioViewTest(TestCase):
    """Pruebas para las vistas de TasaCambio"""

    def setUp(self):
        """Configuración inicial para las pruebas de las vistas"""
        self.client = Client()
        self.moneda = Moneda.objects.create(
            nombre="Dólar",
            simbolo="USD",
            activa=True
        )
        
        # Crear usuario y asignar permisos
        self.usuario = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            tipo_cedula='CI',
            cedula_identidad='1234567'
        )
        
        # Crear grupo y asignar permisos
        self.grupo = Group.objects.create(name='analista_cambiario')
        permisos = Permission.objects.filter(codename__in=['crear_tasa', 'editar_tasa', 'ver_tasa'])
        self.grupo.permissions.set(permisos)
        self.usuario.groups.add(self.grupo)

    def test_lista_tasas_sin_autenticar(self):
        """Verifica que usuarios no autenticados sean redirigidos"""
        response = self.client.get(reverse('tasa:lista_tasas'))
        self.assertEqual(response.status_code, 302,
                        "Error: Usuario no autenticado debería ser redirigido")
        self.assertRedirects(response, 
                           f'/usuarios/login/?next={reverse("tasa:lista_tasas")}',
                           msg_prefix="Error: La redirección no es correcta")

    def test_lista_tasas_autenticado(self):
        """Verifica que usuarios autenticados puedan ver la lista"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tasa:lista_tasas'))
        self.assertEqual(response.status_code, 200,
                        "Error: Usuario autenticado debería poder ver la lista de tasas")
        self.assertTemplateUsed(response, 'tasa/lista_tasas.html',
                              "Error: No se está usando la plantilla correcta")

    def test_crear_tasa_valida(self):
        """Verifica que se pueda crear una tasa válida"""
        self.client.login(username='testuser', password='testpass123')
        data = {
            'moneda': self.moneda.id,
            'precio_base': '4500.0000',
            'comision_compra': '0.100',
            'comision_venta': '0.150'
        }
        response = self.client.post(reverse('tasa:crear_tasa'), data)
        self.assertEqual(response.status_code, 302,
                        "Error: La creación de tasa debería redirigir después de éxito")
        self.assertTrue(TasaCambio.objects.filter(precio_base='4500.0000').exists(),
                       "Error: La tasa no se creó correctamente en la base de datos")

    def test_editar_tasa(self):
        """Verifica que se pueda editar una tasa existente"""
        self.client.login(username='testuser', password='testpass123')
        tasa = TasaCambio.objects.create(
            moneda=self.moneda,
            precio_base=Decimal('4500.0000'),
            comision_compra=Decimal('0.100'),
            comision_venta=Decimal('0.150'),
            ultimo_editor=self.usuario
        )
        data = {
            'moneda': self.moneda.id,
            'precio_base': '4600.0000',
            'comision_compra': '0.120',
            'comision_venta': '0.170'
        }
        response = self.client.post(reverse('tasa:editar_tasa', args=[tasa.id]), data)
        self.assertEqual(response.status_code, 302,
                        "Error: La edición de tasa debería redirigir después de éxito")
        tasa.refresh_from_db()
        self.assertEqual(tasa.precio_base, Decimal('4600.0000'),
                        "Error: El precio base no se actualizó correctamente")
        self.assertEqual(tasa.comision_compra, Decimal('0.120'),
                        "Error: La comisión de compra no se actualizó correctamente")
