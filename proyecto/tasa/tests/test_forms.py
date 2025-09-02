"""
Test unitarios para los formularios de TasaCambio.
"""
from django.test import TestCase
from decimal import Decimal
from ..forms import TasaCambioForm
from monedas.models import Moneda

class TasaCambioFormTest(TestCase):
    """Pruebas para el formulario TasaCambioForm"""

    def setUp(self):
        """Configuración inicial para las pruebas del formulario"""
        self.moneda = Moneda.objects.create(
            nombre="Dólar",
            simbolo="USD",
            activa=True
        )

    def test_formulario_valido(self):
        """Verifica que el formulario acepte datos válidos"""
        form_data = {
            'moneda': self.moneda.id,
            'precio_base': '4500.0000',
            'comision_compra': '0.100',
            'comision_venta': '0.150'
        }
        form = TasaCambioForm(data=form_data)
        self.assertTrue(form.is_valid(),
                       f"Error: El formulario debería ser válido. Errores: {form.errors}")

    def test_formulario_comision_invalida(self):
        """Verifica que el formulario rechace comisiones inválidas"""
        form_data = {
            'moneda': self.moneda.id,
            'precio_base': '4500.0000',
            'comision_compra': '1.500',  # 150% no debería ser válido
            'comision_venta': '0.150'
        }
        form = TasaCambioForm(data=form_data)
        self.assertFalse(form.is_valid(),
                        "Error: El formulario no debería aceptar comisiones mayores a 1")
        self.assertIn('comision_compra', form.errors,
                     "Error: No se generó error para comisión de compra inválida")

    def test_formulario_precio_base_invalido(self):
        """Verifica que el formulario rechace precios base inválidos"""
        form_data = {
            'moneda': self.moneda.id,
            'precio_base': '-100',  # Precio negativo no debería ser válido
            'comision_compra': '0.100',
            'comision_venta': '0.150'
        }
        form = TasaCambioForm(data=form_data)
        self.assertFalse(form.is_valid(),
                        "Error: El formulario no debería aceptar precios base negativos")
        self.assertIn('precio_base', form.errors,
                     "Error: No se generó error para precio base inválido")
