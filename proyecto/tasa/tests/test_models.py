"""
Test unitarios para el modelo TasaCambio.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from ..models import TasaCambio
from monedas.models import Moneda

class TasaCambioModelTest(TestCase):
    """Pruebas para el modelo TasaCambio"""

    def setUp(self):
        """Configuración inicial para las pruebas del modelo"""
        # Crear una moneda para las pruebas
        self.moneda = Moneda.objects.create(
            nombre="Dólar",
            simbolo="USD",
            activa=True
        )
        
        # Crear un usuario para las pruebas
        self.usuario = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            tipo_cedula='CI',
            cedula_identidad='1234567'
        )

        # Crear una tasa de cambio válida
        self.tasa = TasaCambio.objects.create(
            moneda=self.moneda,
            precio_base=Decimal('4500.0000'),
            comision_compra=Decimal('0.100'),
            comision_venta=Decimal('0.150'),
            ultimo_editor=self.usuario
        )

    def test_creacion_tasa(self):
        """Verifica que se pueda crear una tasa de cambio correctamente"""
        self.assertEqual(self.tasa.moneda.simbolo, "USD",
                        "Error: La moneda de la tasa no coincide")
        self.assertEqual(self.tasa.precio_base, Decimal('4500.0000'),
                        "Error: El precio base no coincide")
        self.assertEqual(self.tasa.comision_compra, Decimal('0.100'),
                        "Error: La comisión de compra no coincide")
        self.assertEqual(self.tasa.comision_venta, Decimal('0.150'),
                        "Error: La comisión de venta no coincide")

    def test_validacion_comisiones(self):
        """Verifica que las comisiones no puedan ser mayores a 1 (100%)"""
        with self.assertRaises(Exception) as context:
            TasaCambio.objects.create(
                moneda=self.moneda,
                precio_base=Decimal('4500.0000'),
                comision_compra=Decimal('1.5'),  # 150% no debería ser válido
                comision_venta=Decimal('0.150'),
                ultimo_editor=self.usuario
            )
        self.assertTrue('La comisión debe ser menor o igual a 1' in str(context.exception),
                       "Error: No se validó correctamente el límite superior de la comisión")

    def test_str_representation(self):
        """Verifica la representación en cadena del modelo"""
        expected_str = f'USD - Base: 4500.0000 (Compra: 0.100, Venta: 0.150)'
        self.assertEqual(str(self.tasa), expected_str,
                        "Error: La representación en cadena del modelo no es correcta")
