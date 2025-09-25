"""
Tests para la aplicación de medios de acreditación.

Este módulo contiene los 5 tests más importantes para validar la funcionalidad
core de los medios de acreditación.
"""

from django.test import TestCase
from clientes.models import Cliente
from .models import CuentaBancaria, Billetera
from .forms import CuentaBancariaForm, BilleteraForm


class CuentaBancariaModelTest(TestCase):
    """Test básico para el modelo CuentaBancaria."""
    
    def setUp(self):
        """Configuración inicial."""
        self.cliente = Cliente.objects.create(
            nombre='Juan Pérez',
            tipoDocCliente='CI',
            docCliente='12345678',
            correoElecCliente='juan@test.com',
            telefono='0981123456',
            tipoCliente='F',
            direccion='Asunción, Paraguay',
            ocupacion='Ingeniero',
            declaracion_jurada=True,
            segmento='minorista'
        )
    
    def test_crear_cuenta_bancaria_y_str_method(self):
        """Test para crear una cuenta bancaria válida y verificar el método __str__."""
        cuenta = CuentaBancaria.objects.create(
            banco='ITAU',
            numero_cuenta='1234567890',
            nombre_titular='Juan Pérez',
            nro_documento='12345678',
            cliente=self.cliente
        )
        
        # Verificar creación correcta
        self.assertEqual(cuenta.banco, 'ITAU')
        self.assertEqual(cuenta.numero_cuenta, '1234567890')
        self.assertEqual(cuenta.cliente, self.cliente)
        
        # Verificar método __str__ y display
        expected_str = "Banco Itaú - 1234567890 (Juan Pérez)"
        self.assertEqual(str(cuenta), expected_str)
        self.assertEqual(cuenta.get_banco_display(), 'Banco Itaú')
        
        # Verificar relación con cliente
        self.assertIn(cuenta, self.cliente.cuentas_bancarias.all())


class BilleteraModelTest(TestCase):
    """Test básico para el modelo Billetera."""
    
    def setUp(self):
        """Configuración inicial."""
        self.cliente = Cliente.objects.create(
            nombre='María García',
            tipoDocCliente='CI',
            docCliente='87654321',
            correoElecCliente='maria@test.com',
            telefono='0985987654',
            tipoCliente='F',
            direccion='Asunción, Paraguay',
            ocupacion='Doctora',
            declaracion_jurada=True,
            segmento='vip'
        )
    
    def test_crear_billetera_y_display_methods(self):
        """Test para crear una billetera válida y verificar métodos display."""
        billetera = Billetera.objects.create(
            tipo_billetera='tigo',
            telefono='0985123456',
            nombre_titular='María García',
            nro_documento='87654321',
            cliente=self.cliente
        )
        
        # Verificar creación correcta
        self.assertEqual(billetera.tipo_billetera, 'tigo')
        self.assertEqual(billetera.telefono, '0985123456')
        self.assertEqual(billetera.cliente, self.cliente)
        
        # Verificar métodos display personalizados
        self.assertEqual(billetera.get_tipo_billetera_display(), 'Tigo Money')
        expected_str = "Tigo Money - 0985123456 (María García)"
        self.assertEqual(str(billetera), expected_str)
        
        # Verificar relación con cliente
        self.assertIn(billetera, self.cliente.billeteras.all())


class CuentaBancariaFormTest(TestCase):
    """Test básico para el formulario CuentaBancariaForm."""
    
    def test_formulario_valido_e_invalido(self):
        """Test para formulario válido e inválido con validaciones básicas."""
        # Test formulario válido
        form_data = {
            'banco': 'ITAU',
            'numero_cuenta': '1234567890',
            'nombre_titular': 'Juan Pérez',
            'nro_documento': '12345678'
        }
        form = CuentaBancariaForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Test campos requeridos
        form_empty = CuentaBancariaForm(data={})
        self.assertFalse(form_empty.is_valid())
        self.assertIn('banco', form_empty.errors)
        self.assertIn('numero_cuenta', form_empty.errors)
        
        # Test validación custom del banco
        form_data['banco'] = '-------'  # Opción por defecto
        form_invalid = CuentaBancariaForm(data=form_data)
        self.assertFalse(form_invalid.is_valid())
        self.assertEqual(form_invalid.errors['banco'][0], 'Debes seleccionar un banco válido.')


class BilleteraFormTest(TestCase):
    """Test básico para el formulario BilleteraForm."""
    
    def test_formulario_billetera_validaciones(self):
        """Test para validaciones del formulario de billetera."""
        # Test formulario válido
        form_data = {
            'tipo_billetera': 'tigo',
            'telefono': '0985123456',
            'nombre_titular': 'María García',
            'nro_documento': '87654321'
        }
        form = BilleteraForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Test validación custom del tipo de billetera
        form_data['tipo_billetera'] = '-------'  # Opción por defecto
        form_invalid = BilleteraForm(data=form_data)
        self.assertFalse(form_invalid.is_valid())
        self.assertEqual(form_invalid.errors['tipo_billetera'][0], 'Debes seleccionar un tipo de billetera válido.')
        
        # Test diferentes tipos válidos
        tipos_validos = ['tigo', 'personal', 'zimple']
        for tipo in tipos_validos:
            form_data['tipo_billetera'] = tipo
            form = BilleteraForm(data=form_data)
            self.assertTrue(form.is_valid(), f"El tipo {tipo} debería ser válido")


class MediosAcreditacionIntegrationTest(TestCase):
    """Test de integración para medios de acreditación."""
    
    def setUp(self):
        """Configuración inicial."""
        self.cliente = Cliente.objects.create(
            nombre='Ana López',
            tipoDocCliente='CI',
            docCliente='11111111',
            correoElecCliente='ana@test.com',
            telefono='0981111111',
            tipoCliente='F',
            direccion='Asunción, Paraguay',
            ocupacion='Contadora',
            declaracion_jurada=True,
            segmento='corporativo'
        )
    
    def test_cliente_con_multiples_medios_y_eliminacion_cascada(self):
        """Test para cliente con múltiples medios y eliminación en cascada."""
        # Crear múltiples cuentas bancarias
        cuenta1 = CuentaBancaria.objects.create(
            banco='ITAU',
            numero_cuenta='1111111111',
            nombre_titular='Ana López',
            nro_documento='11111111',
            cliente=self.cliente
        )
        
        cuenta2 = CuentaBancaria.objects.create(
            banco='ATLAS',
            numero_cuenta='2222222222',
            nombre_titular='Ana López',
            nro_documento='11111111',
            cliente=self.cliente
        )
        
        # Crear múltiples billeteras
        billetera1 = Billetera.objects.create(
            tipo_billetera='tigo',
            telefono='0981111111',
            nombre_titular='Ana López',
            nro_documento='11111111',
            cliente=self.cliente
        )
        
        billetera2 = Billetera.objects.create(
            tipo_billetera='personal',
            telefono='0981111112',
            nombre_titular='Ana López',
            nro_documento='11111111',
            cliente=self.cliente
        )
        
        # Verificar que el cliente tiene múltiples medios
        self.assertEqual(self.cliente.cuentas_bancarias.count(), 2)
        self.assertEqual(self.cliente.billeteras.count(), 2)
        
        # Verificar que todos los medios existen
        self.assertTrue(CuentaBancaria.objects.filter(id=cuenta1.id).exists())
        self.assertTrue(CuentaBancaria.objects.filter(id=cuenta2.id).exists())
        self.assertTrue(Billetera.objects.filter(id=billetera1.id).exists())
        self.assertTrue(Billetera.objects.filter(id=billetera2.id).exists())
        
        # Eliminar cliente y verificar eliminación en cascada
        self.cliente.delete()
        
        # Verificar que todos los medios fueron eliminados
        self.assertFalse(CuentaBancaria.objects.filter(id=cuenta1.id).exists())
        self.assertFalse(CuentaBancaria.objects.filter(id=cuenta2.id).exists())
        self.assertFalse(Billetera.objects.filter(id=billetera1.id).exists())
        self.assertFalse(Billetera.objects.filter(id=billetera2.id).exists())
