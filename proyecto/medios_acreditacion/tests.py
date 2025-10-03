"""
Pruebas unitarias para la aplicación medios_acreditacion.

Este módulo contiene las pruebas unitarias más importantes para validar
el correcto funcionamiento de los modelos y formularios de medios de 
acreditación (cuentas bancarias y billeteras electrónicas).

Utiliza pytest como framework de testing.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from medios_acreditacion.models import CuentaBancaria, Billetera
from medios_acreditacion.forms import CuentaBancariaForm, BilleteraForm
from clientes.models import Cliente


@pytest.mark.django_db
class TestCuentaBancariaModel:
    """Pruebas para el modelo CuentaBancaria."""

    @pytest.fixture
    def cliente_test(self):
        """Fixture para crear un cliente de prueba."""
        return Cliente.objects.create(
            nombre="Juan Pérez",
            tipo_documento="CI",
            numero_documento="12345678",
            correo_electronico="juan@test.com",
            telefono="0981123456",
            tipo="F",
            direccion="Asunción",
            ocupacion="Empleado",
            segmento="minorista"
        )

    def test_crear_cuenta_bancaria_valida(self, cliente_test):
        """Test 1: Verificar que se puede crear una cuenta bancaria con datos válidos."""
        cuenta = CuentaBancaria.objects.create(
            banco="ITAU",
            numero_cuenta="12345678901",
            nombre_titular="Juan Pérez",
            nro_documento="12345678",
            cliente=cliente_test
        )
        
        assert cuenta.banco == "ITAU"
        assert cuenta.numero_cuenta == "12345678901"
        assert cuenta.nombre_titular == "Juan Pérez"
        assert cuenta.nro_documento == "12345678"
        assert cuenta.cliente == cliente_test
        assert str(cuenta) == "Banco Itaú - 12345678901 (Juan Pérez)"

    def test_cuenta_bancaria_sin_cliente_falla(self):
        """Test para verificar que no se puede crear cuenta bancaria sin cliente."""
        with pytest.raises(IntegrityError):
            CuentaBancaria.objects.create(
                banco="ITAU",
                numero_cuenta="12345678901",
                nombre_titular="Juan Pérez",
                nro_documento="12345678"
                # cliente no proporcionado
            )


@pytest.mark.django_db
class TestBilleteraModel:
    """Pruebas para el modelo Billetera."""

    @pytest.fixture
    def cliente_test(self):
        """Fixture para crear un cliente de prueba."""
        return Cliente.objects.create(
            nombre="María García",
            tipo_documento="CI",
            numero_documento="87654321",
            correo_electronico="maria@test.com",
            telefono="0981654321",
            tipo="F",
            direccion="Luque",
            ocupacion="Profesional",
            segmento="corporativo"
        )

    def test_crear_billetera_valida(self, cliente_test):
        """Test 2: Verificar que se puede crear una billetera con datos válidos."""
        billetera = Billetera.objects.create(
            tipo_billetera="tigo",
            telefono="0981123456",
            nombre_titular="María García",
            nro_documento="87654321",
            cliente=cliente_test
        )
        
        assert billetera.tipo_billetera == "tigo"
        assert billetera.telefono == "0981123456"
        assert billetera.nombre_titular == "María García"
        assert billetera.nro_documento == "87654321"
        assert billetera.cliente == cliente_test
        assert str(billetera) == "Tigo Money - 0981123456 (María García)"

    def test_billetera_sin_cliente_falla(self):
        """Test para verificar que no se puede crear billetera sin cliente."""
        with pytest.raises(IntegrityError):
            Billetera.objects.create(
                tipo_billetera="tigo",
                telefono="0981123456",
                nombre_titular="María García",
                nro_documento="87654321"
                # cliente no proporcionado
            )


class TestCuentaBancariaForm:
    """Pruebas para el formulario CuentaBancariaForm."""

    def test_formulario_cuenta_bancaria_valido(self):
        """Test 3: Verificar que el formulario acepta datos válidos de cuenta bancaria."""
        datos_form = {
            'banco': 'ITAU',
            'numero_cuenta': '12345678901',
            'nombre_titular': 'Juan Pérez',
            'nro_documento': '12345678'
        }
        
        formulario = CuentaBancariaForm(data=datos_form)
        assert formulario.is_valid(), f"El formulario debería ser válido. Errores: {formulario.errors}"

    def test_formulario_cuenta_bancaria_banco_por_defecto_invalido(self):
        """Test para verificar que el formulario rechaza banco por defecto."""
        datos_form = {
            'banco': '-------',  # Opción por defecto
            'numero_cuenta': '12345678901',
            'nombre_titular': 'Juan Pérez',
            'nro_documento': '12345678'
        }
        
        formulario = CuentaBancariaForm(data=datos_form)
        assert not formulario.is_valid()
        assert 'banco' in formulario.errors
        assert 'Debes seleccionar un banco válido.' in formulario.errors['banco']

    def test_formulario_cuenta_bancaria_campos_requeridos(self):
        """Test para verificar mensajes de error en campos requeridos."""
        formulario = CuentaBancariaForm(data={})
        assert not formulario.is_valid()
        
        # Verificar mensajes de error específicos
        assert 'Debes seleccionar un banco.' in formulario.errors['banco']
        assert 'Debes ingresar el número de cuenta.' in formulario.errors['numero_cuenta']
        assert 'Debes ingresar el nombre del titular.' in formulario.errors['nombre_titular']
        assert 'Debes ingresar el número de documento del titular.' in formulario.errors['nro_documento']


class TestBilleteraForm:
    """Pruebas para el formulario BilleteraForm."""

    def test_formulario_billetera_valido(self):
        """Test 4: Verificar que el formulario acepta datos válidos de billetera."""
        datos_form = {
            'tipo_billetera': 'tigo',
            'telefono': '0981123456',
            'nombre_titular': 'María García',
            'nro_documento': '87654321'
        }
        
        formulario = BilleteraForm(data=datos_form)
        assert formulario.is_valid(), f"El formulario debería ser válido. Errores: {formulario.errors}"

    def test_formulario_billetera_tipo_por_defecto_invalido(self):
        """Test para verificar que el formulario rechaza tipo de billetera por defecto."""
        datos_form = {
            'tipo_billetera': '-------',  # Opción por defecto
            'telefono': '0981123456',
            'nombre_titular': 'María García',
            'nro_documento': '87654321'
        }
        
        formulario = BilleteraForm(data=datos_form)
        assert not formulario.is_valid()
        assert 'tipo_billetera' in formulario.errors
        assert 'Debes seleccionar un tipo de billetera válido.' in formulario.errors['tipo_billetera']

    def test_formulario_billetera_campos_requeridos(self):
        """Test para verificar mensajes de error en campos requeridos."""
        formulario = BilleteraForm(data={})
        assert not formulario.is_valid()
        
        # Verificar mensajes de error específicos
        assert 'Debes seleccionar un tipo de billetera.' in formulario.errors['tipo_billetera']
        assert 'Debes ingresar el número de teléfono asociado a la billetera.' in formulario.errors['telefono']
        assert 'Debes ingresar el nombre del titular.' in formulario.errors['nombre_titular']
        assert 'Debes ingresar el número de documento del titular.' in formulario.errors['nro_documento']


@pytest.mark.django_db
class TestMetodosString:
    """Pruebas para los métodos __str__ de los modelos."""

    @pytest.fixture
    def cliente_test(self):
        """Fixture para crear un cliente de prueba."""
        return Cliente.objects.create(
            nombre="Carlos López",
            tipo_documento="CI",
            numero_documento="11223344",
            correo_electronico="carlos@test.com",
            telefono="0981112233",
            tipo="F",
            direccion="San Lorenzo",
            ocupacion="Comerciante",
            segmento="vip"
        )

    def test_cuenta_bancaria_str_representation(self, cliente_test):
        """Test 5: Verificar representación string correcta de CuentaBancaria."""
        cuenta = CuentaBancaria.objects.create(
            banco="FAMILIAR",
            numero_cuenta="999888777",
            nombre_titular="Carlos López",
            nro_documento="11223344",
            cliente=cliente_test
        )
        
        expected_str = "Banco Familiar - 999888777 (Carlos López)"
        assert str(cuenta) == expected_str

    def test_billetera_str_representation(self, cliente_test):
        """Test para verificar representación string correcta de Billetera."""
        billetera = Billetera.objects.create(
            tipo_billetera="personal",
            telefono="0981998877",
            nombre_titular="Carlos López",
            nro_documento="11223344",
            cliente=cliente_test
        )
        
        expected_str = "Billetera Personal - 0981998877 (Carlos López)"
        assert str(billetera) == expected_str

    def test_billetera_get_tipo_display_personalizado(self, cliente_test):
        """Test para verificar el método get_tipo_billetera_display personalizado."""
        billetera = Billetera.objects.create(
            tipo_billetera="zimple",
            telefono="0981556677",
            nombre_titular="Carlos López",
            nro_documento="11223344",
            cliente=cliente_test
        )
        
        assert billetera.get_tipo_billetera_display() == "Zimple"
