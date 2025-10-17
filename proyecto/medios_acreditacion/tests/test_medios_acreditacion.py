"""
Pruebas unitarias para la aplicación medios_acreditacion.

Este módulo contiene las pruebas unitarias para los modelos y formularios
de la aplicación medios_acreditacion usando pytest.
"""

import pytest
from datetime import datetime
from django.core.exceptions import ValidationError
from medios_acreditacion.models import CuentaBancaria, Billetera, TarjetaLocal
from medios_acreditacion.forms import (
    CuentaBancariaForm, 
    BilleteraForm, 
    TarjetaLocalForm
)
from clientes.models import Cliente


@pytest.mark.django_db
class TestCuentaBancariaModel:
    """Pruebas para el modelo CuentaBancaria."""
    
    @pytest.fixture
    def cliente(self):
        """Fixture que crea un cliente de prueba."""
        return Cliente.objects.create(
            nombre="Juan Pérez",
            tipo_documento="CI",
            numero_documento="12345678",
            correo_electronico="juan@test.com",
            telefono="0981234567"
        )
    
    def test_crear_cuenta_bancaria(self, cliente):
        """Prueba la creación de una cuenta bancaria."""
        cuenta = CuentaBancaria.objects.create(
            cliente=cliente,
            banco="ITAU",
            numero_cuenta="1234567890",
            nombre_titular="Juan Pérez",
            nro_documento="12345678"
        )
        
        assert cuenta.banco == "ITAU"
        assert cuenta.numero_cuenta == "1234567890"
        assert cuenta.nombre_titular == "Juan Pérez"
        assert cuenta.nro_documento == "12345678"
        assert cuenta.cliente == cliente
    
    def test_cuenta_bancaria_str(self, cliente):
        """Prueba el método __str__ de CuentaBancaria."""
        cuenta = CuentaBancaria.objects.create(
            cliente=cliente,
            banco="ATLAS",
            numero_cuenta="9876543210",
            nombre_titular="Juan Pérez",
            nro_documento="12345678"
        )
        
        str_esperado = "Banco Atlas - 9876543210 (Juan Pérez)"
        assert str(cuenta) == str_esperado


@pytest.mark.django_db
class TestBilleteraModel:
    """Pruebas para el modelo Billetera."""
    
    @pytest.fixture
    def cliente(self):
        """Fixture que crea un cliente de prueba."""
        return Cliente.objects.create(
            nombre="María López",
            tipo_documento="CI",
            numero_documento="87654321",
            correo_electronico="maria@test.com",
            telefono="0987654321"
        )
    
    def test_crear_billetera(self, cliente):
        """Prueba la creación de una billetera."""
        billetera = Billetera.objects.create(
            cliente=cliente,
            tipo_billetera="tigo",
            telefono="0981234567",
            nombre_titular="María López",
            nro_documento="87654321"
        )
        
        assert billetera.tipo_billetera == "tigo"
        assert billetera.telefono == "0981234567"
        assert billetera.nombre_titular == "María López"
        assert billetera.cliente == cliente
    
    def test_billetera_get_tipo_display(self, cliente):
        """Prueba el método get_tipo_billetera_display."""
        billetera = Billetera.objects.create(
            cliente=cliente,
            tipo_billetera="personal",
            telefono="0987654321",
            nombre_titular="María López",
            nro_documento="87654321"
        )
        
        assert billetera.get_tipo_billetera_display() == "Billetera Personal"
    
    def test_billetera_str(self, cliente):
        """Prueba el método __str__ de Billetera."""
        billetera = Billetera.objects.create(
            cliente=cliente,
            tipo_billetera="zimple",
            telefono="0981111111",
            nombre_titular="María López",
            nro_documento="87654321"
        )
        
        str_esperado = "Zimple - 0981111111 (María López)"
        assert str(billetera) == str_esperado


@pytest.mark.django_db
class TestTarjetaLocalModel:
    """Pruebas para el modelo TarjetaLocal."""
    
    @pytest.fixture
    def cliente(self):
        """Fixture que crea un cliente de prueba."""
        return Cliente.objects.create(
            nombre="Carlos González",
            tipo_documento="CI",
            numero_documento="11223344",
            correo_electronico="carlos@test.com",
            telefono="0983456789"
        )
    
    def test_crear_tarjeta_local(self, cliente):
        """Prueba la creación de una tarjeta local."""
        tarjeta = TarjetaLocal.objects.create(
            cliente=cliente,
            brand="PANAL",
            numero_tarjeta="1234 5678 9012 3456",
            nombre_titular="Carlos González",
            nro_documento="11223344",
            mes_expiracion=12,
            anio_expiracion=2026,
            cvv="123"
        )
        
        assert tarjeta.brand == "PANAL"
        assert tarjeta.numero_tarjeta == "1234 5678 9012 3456"
        assert tarjeta.mes_expiracion == 12
        assert tarjeta.anio_expiracion == 2026
        assert tarjeta.cvv == "123"
        assert tarjeta.cliente == cliente
    
    def test_tarjeta_get_last4(self, cliente):
        """Prueba el método get_last4 de TarjetaLocal."""
        tarjeta = TarjetaLocal.objects.create(
            cliente=cliente,
            brand="CABAL",
            numero_tarjeta="1111 2222 3333 4444",
            nombre_titular="Carlos González",
            nro_documento="11223344",
            mes_expiracion=6,
            anio_expiracion=2027,
            cvv="456"
        )
        
        assert tarjeta.get_last4() == "4444"
    
    def test_tarjeta_save_actualiza_last4(self, cliente):
        """Prueba que el método save actualiza automáticamente last4."""
        tarjeta = TarjetaLocal.objects.create(
            cliente=cliente,
            brand="PANAL",
            numero_tarjeta="5555 6666 7777 8888",
            nombre_titular="Carlos González",
            nro_documento="11223344",
            mes_expiracion=3,
            anio_expiracion=2028,
            cvv="789"
        )
        
        assert tarjeta.last4 == "8888"


@pytest.mark.django_db
class TestCuentaBancariaForm:
    """Pruebas para el formulario CuentaBancariaForm."""
    
    def test_form_valido_con_datos_correctos(self):
        """Prueba que el formulario es válido con datos correctos."""
        form_data = {
            'banco': 'ITAU',
            'numero_cuenta': '1234567890',
            'nombre_titular': 'Juan Pérez',
            'nro_documento': '12345678'
        }
        form = CuentaBancariaForm(data=form_data)
        
        assert form.is_valid(), f"El formulario debería ser válido. Errores: {form.errors}"
    
    def test_form_invalido_banco_por_defecto(self):
        """Prueba que el formulario es inválido si se selecciona el banco por defecto."""
        form_data = {
            'banco': '-------',
            'numero_cuenta': '1234567890',
            'nombre_titular': 'Juan Pérez',
            'nro_documento': '12345678'
        }
        form = CuentaBancariaForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con banco por defecto"
        assert 'banco' in form.errors, "Debería haber un error en el campo banco"
        assert 'Debes seleccionar un banco válido.' in str(form.errors['banco'])
    
    def test_form_invalido_sin_numero_cuenta(self):
        """Prueba que el formulario es inválido sin número de cuenta."""
        form_data = {
            'banco': 'ATLAS',
            'numero_cuenta': '',
            'nombre_titular': 'Juan Pérez',
            'nro_documento': '12345678'
        }
        form = CuentaBancariaForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido sin número de cuenta"
        assert 'numero_cuenta' in form.errors, "Debería haber un error en el campo numero_cuenta"
        assert 'Debes ingresar el número de cuenta.' in str(form.errors['numero_cuenta'])


@pytest.mark.django_db
class TestBilleteraForm:
    """Pruebas para el formulario BilleteraForm."""
    
    def test_form_valido_con_datos_correctos(self):
        """Prueba que el formulario es válido con datos correctos."""
        form_data = {
            'tipo_billetera': 'tigo',
            'telefono': '0981234567',
            'nombre_titular': 'María López',
            'nro_documento': '87654321'
        }
        form = BilleteraForm(data=form_data)
        
        assert form.is_valid(), f"El formulario debería ser válido. Errores: {form.errors}"
    
    def test_form_invalido_tipo_billetera_por_defecto(self):
        """Prueba que el formulario es inválido si se selecciona el tipo por defecto."""
        form_data = {
            'tipo_billetera': '-------',
            'telefono': '0981234567',
            'nombre_titular': 'María López',
            'nro_documento': '87654321'
        }
        form = BilleteraForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con tipo_billetera por defecto"
        assert 'tipo_billetera' in form.errors, "Debería haber un error en el campo tipo_billetera"
        assert 'Debes seleccionar un tipo de billetera válido.' in str(form.errors['tipo_billetera'])
    
    def test_form_invalido_sin_telefono(self):
        """Prueba que el formulario es inválido sin teléfono."""
        form_data = {
            'tipo_billetera': 'personal',
            'telefono': '',
            'nombre_titular': 'María López',
            'nro_documento': '87654321'
        }
        form = BilleteraForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido sin teléfono"
        assert 'telefono' in form.errors, "Debería haber un error en el campo telefono"


@pytest.mark.django_db
class TestTarjetaLocalForm:
    """Pruebas para el formulario TarjetaLocalForm."""
    
    @pytest.fixture
    def cliente(self):
        """Fixture que crea un cliente de prueba."""
        return Cliente.objects.create(
            nombre="Pedro Ramírez",
            tipo_documento="CI",
            numero_documento="99887766",
            correo_electronico="pedro@test.com",
            telefono="0985556666"
        )
    
    def test_form_valido_con_datos_correctos(self, cliente):
        """Prueba que el formulario es válido con datos correctos."""
        anio_actual = datetime.now().year
        form_data = {
            'brand': 'PANAL',
            'numero_tarjeta': '1234567890123456',
            'nombre_titular': 'Pedro Ramírez',
            'nro_documento': '99887766',
            'mes_expiracion': '12',
            'anio_expiracion': str(anio_actual + 1),
            'cvv': '123'
        }
        form = TarjetaLocalForm(data=form_data, cliente=cliente)
        
        assert form.is_valid(), f"El formulario debería ser válido. Errores: {form.errors}"
    
    def test_form_invalido_numero_tarjeta_incorrecto(self, cliente):
        """Prueba que el formulario es inválido con número de tarjeta incorrecto."""
        anio_actual = datetime.now().year
        form_data = {
            'brand': 'CABAL',
            'numero_tarjeta': '12345',  # Solo 5 dígitos
            'nombre_titular': 'Pedro Ramírez',
            'nro_documento': '99887766',
            'mes_expiracion': '6',
            'anio_expiracion': str(anio_actual + 1),
            'cvv': '456'
        }
        form = TarjetaLocalForm(data=form_data, cliente=cliente)
        
        assert not form.is_valid(), "El formulario no debería ser válido con número de tarjeta incorrecto"
        assert 'numero_tarjeta' in form.errors, "Debería haber un error en el campo numero_tarjeta"
        assert 'El número de tarjeta debe tener 16 dígitos.' in str(form.errors['numero_tarjeta'])
    
    def test_form_invalido_cvv_incorrecto(self, cliente):
        """Prueba que el formulario es inválido con CVV incorrecto."""
        anio_actual = datetime.now().year
        form_data = {
            'brand': 'PANAL',
            'numero_tarjeta': '1234567890123456',
            'nombre_titular': 'Pedro Ramírez',
            'nro_documento': '99887766',
            'mes_expiracion': '3',
            'anio_expiracion': str(anio_actual + 1),
            'cvv': '12'  # Solo 2 dígitos
        }
        form = TarjetaLocalForm(data=form_data, cliente=cliente)
        
        assert not form.is_valid(), "El formulario no debería ser válido con CVV incorrecto"
        assert 'cvv' in form.errors, "Debería haber un error en el campo cvv"
        assert 'El CVV debe tener 3 o 4 dígitos.' in str(form.errors['cvv'])
    
    def test_form_invalido_tarjeta_expirada(self, cliente):
        """Prueba que el formulario es inválido con tarjeta expirada."""
        anio_actual = datetime.now().year
        mes_actual = datetime.now().month
        # Usar un mes anterior al actual en el año actual
        mes_expirado = mes_actual - 1 if mes_actual > 1 else 12
        anio_expirado = anio_actual if mes_actual > 1 else anio_actual - 1
        
        form_data = {
            'brand': 'CABAL',
            'numero_tarjeta': '1234567890123456',
            'nombre_titular': 'Pedro Ramírez',
            'nro_documento': '99887766',
            'mes_expiracion': str(mes_expirado),
            'anio_expiracion': str(anio_expirado),
            'cvv': '789'
        }
        form = TarjetaLocalForm(data=form_data, cliente=cliente)
        
        assert not form.is_valid(), "El formulario no debería ser válido con tarjeta expirada"
        assert '__all__' in form.errors, "Debería haber un error general"
        assert 'La tarjeta está expirada.' in str(form.errors['__all__'])
    
    def test_form_formatea_numero_tarjeta(self, cliente):
        """Prueba que el formulario formatea correctamente el número de tarjeta."""
        anio_actual = datetime.now().year
        form_data = {
            'brand': 'PANAL',
            'numero_tarjeta': '1234567890123456',
            'nombre_titular': 'Pedro Ramírez',
            'nro_documento': '99887766',
            'mes_expiracion': '6',
            'anio_expiracion': str(anio_actual + 1),
            'cvv': '123'
        }
        form = TarjetaLocalForm(data=form_data, cliente=cliente)
        
        assert form.is_valid(), f"El formulario debería ser válido. Errores: {form.errors}"
        assert form.cleaned_data['numero_tarjeta'] == '1234 5678 9012 3456'
