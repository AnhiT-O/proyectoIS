from django.test import TestCase
from django.core.exceptions import ValidationError
from medios_pago.forms import MedioPagoForm, MedioPagoSearchForm


class MedioPagoFormTest(TestCase):
    """Tests para el formulario MedioPagoForm"""

    def test_formulario_efectivo_valido(self):
        """Test formulario válido para efectivo"""
        form_data = {
            'nombre': 'Efectivo General',
            'tipo': 'efectivo',
            'activo': True
        }
        form = MedioPagoForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_formulario_transferencia_valido(self):
        """Test formulario válido para transferencia"""
        form_data = {
            'nombre': 'Transferencia Bancaria',
            'tipo': 'transferencia',
            'moneda_transferencia': 'PYG',
            'activo': True
        }
        form = MedioPagoForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_formulario_transferencia_sin_moneda(self):
        """Test formulario inválido para transferencia sin moneda"""
        form_data = {
            'nombre': 'Transferencia',
            'tipo': 'transferencia',
            'activo': True
        }
        form = MedioPagoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('moneda_transferencia', form.errors)

    def test_formulario_transferencia_moneda_invalida(self):
        """Test formulario inválido para transferencia con moneda USD"""
        form_data = {
            'nombre': 'Transferencia USD',
            'tipo': 'transferencia',
            'moneda_transferencia': 'USD',
            'activo': True
        }
        form = MedioPagoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('moneda_transferencia', form.errors)

    def test_formulario_billetera_valido(self):
        """Test formulario válido para billetera electrónica"""
        form_data = {
            'nombre': 'Tigo Money',
            'tipo': 'billetera_electronica',
            'tipo_billetera': 'tigo_money',
            'numero_billetera': '0981123456',
            'activo': True
        }
        form = MedioPagoForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_formulario_billetera_sin_tipo(self):
        """Test formulario inválido para billetera sin tipo"""
        form_data = {
            'nombre': 'Billetera',
            'tipo': 'billetera_electronica',
            'numero_billetera': '0981123456',
            'activo': True
        }
        form = MedioPagoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('tipo_billetera', form.errors)

    def test_formulario_billetera_numero_invalido(self):
        """Test validación de número de billetera solo números"""
        form_data = {
            'nombre': 'Billetera',
            'tipo': 'billetera_electronica',
            'tipo_billetera': 'tigo_money',
            'numero_billetera': '098-abc-123',
            'activo': True
        }
        form = MedioPagoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('numero_billetera', form.errors)

    def test_formulario_tarjeta_valido(self):
        """Test formulario válido para tarjeta de crédito"""
        form_data = {
            'nombre': 'Tarjeta Visa',
            'tipo': 'tarjeta_credito',
            'cuenta_destino': 'PYG',
            'numero_cuenta': '123456789',
            'activo': True
        }
        form = MedioPagoForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_formulario_tarjeta_sin_cuenta(self):
        """Test formulario inválido para tarjeta sin cuenta destino"""
        form_data = {
            'nombre': 'Tarjeta',
            'tipo': 'tarjeta_credito',
            'numero_cuenta': '123456789',
            'activo': True
        }
        form = MedioPagoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cuenta_destino', form.errors)

    def test_formulario_cheque_valido(self):
        """Test formulario válido para cheque"""
        form_data = {
            'nombre': 'Cheque Bancario',
            'tipo': 'cheque',
            'solo_compra_extranjera': True,
            'moneda_cheque': 'PYG',
            'activo': True
        }
        form = MedioPagoForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_formulario_cheque_no_compra_extranjera(self):
        """Test formulario inválido para cheque no marcado como compra extranjera"""
        form_data = {
            'nombre': 'Cheque',
            'tipo': 'cheque',
            'solo_compra_extranjera': False,
            'moneda_cheque': 'PYG',
            'activo': True
        }
        form = MedioPagoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('solo_compra_extranjera', form.errors)

    def test_formulario_cheque_moneda_invalida(self):
        """Test formulario inválido para cheque con moneda USD"""
        form_data = {
            'nombre': 'Cheque USD',
            'tipo': 'cheque',
            'solo_compra_extranjera': True,
            'moneda_cheque': 'USD',
            'activo': True
        }
        form = MedioPagoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('moneda_cheque', form.errors)


class MedioPagoSearchFormTest(TestCase):
    """Tests para el formulario de búsqueda"""

    def test_formulario_busqueda_vacio(self):
        """Test formulario de búsqueda vacío es válido"""
        form = MedioPagoSearchForm(data={})
        self.assertTrue(form.is_valid())

    def test_formulario_busqueda_con_texto(self):
        """Test formulario de búsqueda con texto"""
        form_data = {
            'buscar': 'efectivo',
            'tipo': '',
            'activo': ''
        }
        form = MedioPagoSearchForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['buscar'], 'efectivo')

    def test_formulario_busqueda_con_filtros(self):
        """Test formulario de búsqueda con filtros"""
        form_data = {
            'buscar': '',
            'tipo': 'efectivo',
            'activo': 'true'
        }
        form = MedioPagoSearchForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['tipo'], 'efectivo')
        self.assertEqual(form.cleaned_data['activo'], 'true')
