from django.test import TestCase
from django.core.exceptions import ValidationError
from medios_pago.models import MedioPago


class MedioPagoModelTest(TestCase):
    """Tests para el modelo MedioPago"""

    def test_crear_medio_pago_efectivo(self):
        """Test crear medio de pago efectivo básico"""
        medio_pago = MedioPago.objects.create(
            nombre='Efectivo General',
            tipo='efectivo',
            activo=True
        )
        self.assertEqual(medio_pago.nombre, 'Efectivo General')
        self.assertEqual(medio_pago.tipo, 'efectivo')
        self.assertTrue(medio_pago.activo)
        self.assertTrue(medio_pago.es_efectivo)
        self.assertTrue(medio_pago.requiere_tauser)

    def test_crear_transferencia_valida(self):
        """Test crear transferencia válida en PYG"""
        medio_pago = MedioPago.objects.create(
            nombre='Transferencia Bancaria',
            tipo='transferencia',
            moneda_transferencia='PYG',
            activo=True
        )
        self.assertEqual(medio_pago.tipo, 'transferencia')
        self.assertEqual(medio_pago.moneda_transferencia, 'PYG')

    def test_transferencia_solo_pyg(self):
        """Test que las transferencias solo permiten PYG"""
        with self.assertRaises(ValidationError):
            medio_pago = MedioPago(
                nombre='Transferencia USD',
                tipo='transferencia',
                moneda_transferencia='USD',
                activo=True
            )
            medio_pago.full_clean()

    def test_crear_billetera_electronica_valida(self):
        """Test crear billetera electrónica válida"""
        medio_pago = MedioPago.objects.create(
            nombre='Tigo Money Principal',
            tipo='billetera_electronica',
            tipo_billetera='tigo_money',
            numero_billetera='0981123456',
            activo=True
        )
        self.assertEqual(medio_pago.tipo_billetera, 'tigo_money')
        self.assertEqual(medio_pago.numero_billetera, '0981123456')

    def test_billetera_electronica_requiere_tipo_y_numero(self):
        """Test que billetera electrónica requiere tipo y número"""
        with self.assertRaises(ValidationError):
            medio_pago = MedioPago(
                nombre='Billetera Incompleta',
                tipo='billetera_electronica',
                activo=True
            )
            medio_pago.full_clean()

    def test_crear_tarjeta_credito_valida(self):
        """Test crear tarjeta de crédito válida"""
        medio_pago = MedioPago.objects.create(
            nombre='Tarjeta Visa',
            tipo='tarjeta_credito',
            cuenta_destino='PYG',
            numero_cuenta='123456789',
            activo=True
        )
        self.assertEqual(medio_pago.cuenta_destino, 'PYG')
        self.assertEqual(medio_pago.numero_cuenta, '123456789')

    def test_tarjeta_credito_requiere_cuenta_y_numero(self):
        """Test que tarjeta de crédito requiere cuenta y número"""
        with self.assertRaises(ValidationError):
            medio_pago = MedioPago(
                nombre='Tarjeta Incompleta',
                tipo='tarjeta_credito',
                activo=True
            )
            medio_pago.full_clean()

    def test_crear_cheque_valido(self):
        """Test crear cheque válido"""
        medio_pago = MedioPago.objects.create(
            nombre='Cheque Bancario',
            tipo='cheque',
            solo_compra_extranjera=True,
            moneda_cheque='PYG',
            activo=True
        )
        self.assertTrue(medio_pago.solo_compra_extranjera)
        self.assertEqual(medio_pago.moneda_cheque, 'PYG')

    def test_cheque_solo_para_compra_extranjera(self):
        """Test que cheques solo pueden ser para compra extranjera"""
        with self.assertRaises(ValidationError):
            medio_pago = MedioPago(
                nombre='Cheque Inválido',
                tipo='cheque',
                solo_compra_extranjera=False,
                moneda_cheque='PYG',
                activo=True
            )
            medio_pago.full_clean()

    def test_cheque_solo_pyg(self):
        """Test que cheques solo pueden ser en PYG"""
        with self.assertRaises(ValidationError):
            medio_pago = MedioPago(
                nombre='Cheque USD',
                tipo='cheque',
                solo_compra_extranjera=True,
                moneda_cheque='USD',
                activo=True
            )
            medio_pago.full_clean()

    def test_propiedades_efectivo(self):
        """Test propiedades específicas del efectivo"""
        medio_pago = MedioPago.objects.create(
            nombre='Efectivo',
            tipo='efectivo',
            activo=True
        )
        self.assertTrue(medio_pago.es_efectivo)
        self.assertTrue(medio_pago.permite_moneda_extranjera)
        self.assertTrue(medio_pago.requiere_tauser)

    def test_propiedades_cheque(self):
        """Test propiedades específicas del cheque"""
        medio_pago = MedioPago.objects.create(
            nombre='Cheque',
            tipo='cheque',
            solo_compra_extranjera=True,
            moneda_cheque='PYG',
            activo=True
        )
        self.assertFalse(medio_pago.es_efectivo)
        self.assertTrue(medio_pago.permite_moneda_extranjera)
        self.assertFalse(medio_pago.requiere_tauser)

    def test_limpieza_campos_no_aplicables(self):
        """Test que se limpian campos no aplicables según el tipo"""
        medio_pago = MedioPago(
            nombre='Efectivo',
            tipo='efectivo',
            moneda_transferencia='PYG',  # No debería mantenerse
            tipo_billetera='tigo_money',  # No debería mantenerse
            activo=True
        )
        medio_pago.full_clean()
        
        # Los campos no aplicables deberían limpiarse
        self.assertIsNone(medio_pago.moneda_transferencia)
        self.assertIsNone(medio_pago.tipo_billetera)

    def test_str_representation(self):
        """Test representación string del modelo"""
        medio_pago = MedioPago.objects.create(
            nombre='Efectivo Prueba',
            tipo='efectivo',
            activo=True
        )
        expected = "Efectivo Prueba (Efectivo)"
        self.assertEqual(str(medio_pago), expected)
