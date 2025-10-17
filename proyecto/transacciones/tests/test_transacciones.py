"""
Pruebas unitarias para la aplicación transacciones.

Este módulo contiene las pruebas unitarias para los modelos, formularios y funciones
de la aplicación transacciones usando pytest.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from transacciones.models import (
    Recargos,
    LimiteGlobal,
    TransactionToken,
    Tauser,
    BilletesTauser,
    Transaccion,
    calcular_conversion,
    redondear_efectivo
)
from transacciones.forms import SeleccionMonedaMontoForm, VariablesForm
from monedas.models import Moneda, Denominacion, StockGuaranies
from clientes.models import Cliente
from usuarios.models import Usuario


@pytest.mark.django_db
class TestRecargosModel:
    """Pruebas para el modelo Recargos."""
    
    def test_crear_recargo(self):
        """Prueba la creación de un recargo."""
        recargo = Recargos.objects.create(
            medio="Tarjeta de Crédito",
            marca="TEST_CARD",
            recargo=Decimal("2.5")
        )
        
        assert recargo.medio == "Tarjeta de Crédito"
        assert recargo.marca == "TEST_CARD"
        assert recargo.recargo == Decimal("2.5")
    
    def test_recargo_str(self):
        """Prueba el método __str__ de Recargos."""
        recargo = Recargos.objects.create(
            medio="Billetera Electrónica",
            marca="Test Wallet",
            recargo=Decimal("1.5")
        )
        
        assert str(recargo) == "Test Wallet"


@pytest.mark.django_db
class TestLimiteGlobalModel:
    """Pruebas para el modelo LimiteGlobal."""
    
    def test_crear_limite_global(self):
        """Prueba la creación de un límite global."""
        limite = LimiteGlobal.objects.create(
            limite_diario=90000000,
            limite_mensual=450000000
        )
        
        assert limite.limite_diario == 90000000
        assert limite.limite_mensual == 450000000
    
    def test_limite_global_str(self):
        """Prueba el método __str__ de LimiteGlobal."""
        limite = LimiteGlobal.objects.create(
            limite_diario=100000000,
            limite_mensual=500000000
        )
        
        assert "100,000,000" in str(limite)
        assert "500,000,000" in str(limite)


@pytest.mark.django_db
class TestTransactionTokenModel:
    """Pruebas para el modelo TransactionToken."""
    
    @pytest.fixture
    def usuario(self):
        """Fixture que crea un usuario de prueba."""
        return Usuario.objects.create(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            numero_documento="12345678",
            telefono="0981234567"
        )
    
    def test_crear_transaction_token(self, usuario):
        """Prueba la creación de un token de transacción."""
        expires_at = timezone.now() + timedelta(minutes=10)
        token = TransactionToken.objects.create(
            usuario=usuario,
            token="123456",
            transaccion_data={"tipo": "compra", "monto": 100},
            expires_at=expires_at
        )
        
        assert token.usuario == usuario
        assert token.token == "123456"
        assert token.used == False
    
    def test_token_is_valid(self, usuario):
        """Prueba el método is_valid del token."""
        expires_at = timezone.now() + timedelta(minutes=10)
        token = TransactionToken.objects.create(
            usuario=usuario,
            token="123456",
            transaccion_data={"tipo": "compra"},
            expires_at=expires_at
        )
        
        assert token.is_valid() == True
    
    def test_token_not_valid_when_expired(self, usuario):
        """Prueba que el token no sea válido cuando está expirado."""
        expires_at = timezone.now() - timedelta(minutes=1)
        token = TransactionToken.objects.create(
            usuario=usuario,
            token="123456",
            transaccion_data={"tipo": "compra"},
            expires_at=expires_at
        )
        
        assert token.is_valid() == False
    
    def test_token_not_valid_when_used(self, usuario):
        """Prueba que el token no sea válido cuando ya fue usado."""
        expires_at = timezone.now() + timedelta(minutes=10)
        token = TransactionToken.objects.create(
            usuario=usuario,
            token="123456",
            transaccion_data={"tipo": "compra"},
            expires_at=expires_at,
            used=True
        )
        
        assert token.is_valid() == False
    
    def test_mark_as_used(self, usuario):
        """Prueba el método mark_as_used del token."""
        expires_at = timezone.now() + timedelta(minutes=10)
        token = TransactionToken.objects.create(
            usuario=usuario,
            token="123456",
            transaccion_data={"tipo": "compra"},
            expires_at=expires_at
        )
        
        token.mark_as_used()
        token.refresh_from_db()
        
        assert token.used == True


@pytest.mark.django_db
class TestTauserModel:
    """Pruebas para el modelo Tauser."""
    
    def test_crear_tauser(self):
        """Prueba la creación de un Tauser."""
        tauser = Tauser.objects.create(
            puerto=8001,
            sucursal="Sucursal Test"
        )
        
        assert tauser.puerto == 8001
        assert tauser.sucursal == "Sucursal Test"
    
    def test_tauser_str(self):
        """Prueba el método __str__ de Tauser."""
        tauser = Tauser.objects.create(
            puerto=8002,
            sucursal="Sucursal Centro"
        )
        
        assert str(tauser) == "TAUser Puerto 8002"


@pytest.mark.django_db
class TestBilletesTauserModel:
    """Pruebas para el modelo BilletesTauser."""
    
    @pytest.fixture
    def tauser(self):
        """Fixture que crea un Tauser de prueba."""
        return Tauser.objects.create(
            puerto=8003,
            sucursal="Sucursal Test Billetes"
        )
    
    @pytest.fixture
    def denominacion(self):
        """Fixture que crea una denominación de prueba."""
        moneda, created = Moneda.objects.get_or_create(
            simbolo="USD",
            defaults={
                'nombre': "Dólar estadounidense",
                'tasa_base': 7000,
                'comision_compra': 100,
                'comision_venta': 150
            }
        )
        return Denominacion.objects.create(
            moneda=moneda,
            valor=100
        )
    
    def test_crear_billetes_tauser(self, tauser, denominacion):
        """Prueba la creación de billetes en un Tauser."""
        billetes = BilletesTauser.objects.create(
            tauser=tauser,
            denominacion=denominacion,
            cantidad=50
        )
        
        assert billetes.tauser == tauser
        assert billetes.denominacion == denominacion
        assert billetes.cantidad == 50


@pytest.mark.django_db
class TestTransaccionModel:
    """Pruebas para el modelo Transaccion."""
    
    @pytest.fixture
    def cliente(self):
        """Fixture que crea un cliente de prueba."""
        return Cliente.objects.create(
            nombre="Cliente Test",
            tipo_documento="CI",
            numero_documento="87654321",
            correo_electronico="cliente@test.com",
            telefono="0987654321",
            segmento="minorista"
        )
    
    @pytest.fixture
    def moneda_eur(self):
        """Fixture que crea una moneda EUR de prueba."""
        return Moneda.objects.create(
            nombre="Euro",
            simbolo="EUR",
            tasa_base=8000,
            comision_compra=150,
            comision_venta=200,
            decimales=2,
            activa=True
        )
    
    @pytest.fixture
    def usuario(self):
        """Fixture que crea un usuario de prueba."""
        return Usuario.objects.create(
            username="operador",
            email="operador@test.com",
            first_name="Operador",
            last_name="Test",
            numero_documento="11223344",
            telefono="0981122334"
        )
    
    def test_crear_transaccion(self, cliente, moneda_eur, usuario):
        """Prueba la creación de una transacción."""
        transaccion = Transaccion.objects.create(
            cliente=cliente,
            tipo="compra",
            moneda=moneda_eur,
            monto=Decimal("100"),
            cotizacion=8200,
            precio_base=820000,
            monto_original=Decimal("100"),
            beneficio_segmento=0,
            porc_beneficio_segmento="0%",
            recargo_pago=0,
            porc_recargo_pago="0%",
            recargo_cobro=0,
            porc_recargo_cobro="0%",
            redondeo_efectivo_monto=Decimal("0"),
            redondeo_efectivo_precio_final=0,
            precio_final=820000,
            medio_pago="Efectivo",
            medio_cobro="Efectivo",
            usuario=usuario
        )
        
        assert transaccion.cliente == cliente
        assert transaccion.tipo == "compra"
        assert transaccion.moneda == moneda_eur
        assert transaccion.monto == Decimal("100")
        assert transaccion.estado == "Pendiente"
    
    def test_transaccion_str(self, cliente, moneda_eur, usuario):
        """Prueba el método __str__ de Transaccion."""
        transaccion = Transaccion.objects.create(
            cliente=cliente,
            tipo="venta",
            moneda=moneda_eur,
            monto=Decimal("50"),
            cotizacion=7850,
            precio_base=392500,
            monto_original=Decimal("50"),
            beneficio_segmento=0,
            porc_beneficio_segmento="0%",
            recargo_pago=0,
            porc_recargo_pago="0%",
            recargo_cobro=0,
            porc_recargo_cobro="0%",
            redondeo_efectivo_monto=Decimal("0"),
            redondeo_efectivo_precio_final=0,
            precio_final=392500,
            medio_pago="Efectivo",
            medio_cobro="Efectivo",
            usuario=usuario
        )
        
        str_transaccion = str(transaccion)
        assert "Venta" in str_transaccion
        assert "50" in str_transaccion
        assert "EUR" in str_transaccion


@pytest.mark.django_db
class TestCalcularConversion:
    """Pruebas para la función calcular_conversion."""
    
    @pytest.fixture
    def moneda_usd(self):
        """Fixture que crea una moneda USD de prueba."""
        moneda, created = Moneda.objects.get_or_create(
            simbolo="USD",
            defaults={
                'nombre': "Dólar estadounidense",
                'tasa_base': 7000,
                'comision_compra': 100,
                'comision_venta': 150,
                'decimales': 2
            }
        )
        # Crear denominaciones para USD
        for valor in [1, 5, 10, 20, 50, 100]:
            Denominacion.objects.get_or_create(moneda=moneda, valor=valor)
        
        # Crear denominaciones para guaraníes
        for valor in [2000, 5000, 10000, 20000, 50000, 100000]:
            Denominacion.objects.get_or_create(moneda=None, valor=valor)
        
        return moneda
    
    def test_calcular_conversion_compra_minorista(self, moneda_usd):
        """Prueba el cálculo de conversión para compra de cliente minorista."""
        resultado = calcular_conversion(
            monto=Decimal("100"),
            moneda=moneda_usd,
            operacion="compra",
            pago="Efectivo",
            cobro="Efectivo",
            segmentacion="minorista"
        )
        
        # Verificar que retorna los campos esperados
        assert 'cotizacion' in resultado
        assert 'precio_base' in resultado
        assert 'beneficio_segmento' in resultado
        assert 'precio_final' in resultado
        assert resultado['porc_beneficio_segmento'] == '0%'
    
    def test_calcular_conversion_compra_corporativo(self, moneda_usd):
        """Prueba el cálculo de conversión para compra de cliente corporativo (5% beneficio)."""
        resultado = calcular_conversion(
            monto=Decimal("100"),
            moneda=moneda_usd,
            operacion="compra",
            pago="Efectivo",
            cobro="Efectivo",
            segmentacion="corporativo"
        )
        
        assert resultado['porc_beneficio_segmento'] == '5%'
        assert resultado['beneficio_segmento'] > 0
    
    def test_calcular_conversion_compra_vip(self, moneda_usd):
        """Prueba el cálculo de conversión para compra de cliente VIP (10% beneficio)."""
        resultado = calcular_conversion(
            monto=Decimal("100"),
            moneda=moneda_usd,
            operacion="compra",
            pago="Efectivo",
            cobro="Efectivo",
            segmentacion="vip"
        )
        
        assert resultado['porc_beneficio_segmento'] == '10%'
        assert resultado['beneficio_segmento'] > 0
    
    def test_calcular_conversion_venta_minorista(self, moneda_usd):
        """Prueba el cálculo de conversión para venta de cliente minorista."""
        resultado = calcular_conversion(
            monto=Decimal("100"),
            moneda=moneda_usd,
            operacion="venta",
            pago="Efectivo",
            cobro="Efectivo",
            segmentacion="minorista"
        )
        
        assert 'cotizacion' in resultado
        assert 'precio_final' in resultado
        assert resultado['porc_beneficio_segmento'] == '0%'


@pytest.mark.django_db
class TestRedondearEfectivo:
    """Pruebas para la función redondear_efectivo."""
    
    def test_redondear_sin_redondeo_necesario(self):
        """Prueba redondeo cuando el monto es múltiplo exacto de una denominación."""
        denominaciones = [2000, 5000, 10000, 20000, 50000, 100000]
        monto = Decimal("10000")
        
        redondeo = redondear_efectivo(monto, denominaciones)
        
        assert redondeo == 0
    
    def test_redondear_con_redondeo(self):
        """Prueba redondeo cuando el monto no es múltiplo de ninguna denominación."""
        denominaciones = [2000, 5000, 10000, 20000, 50000, 100000]
        monto = Decimal("7500")
        
        redondeo = redondear_efectivo(monto, denominaciones)
        
        # Debería retornar 500 (cantidad necesaria para llegar a 8000 que es múltiplo de 2000)
        assert redondeo == Decimal("500"), f"Esperado 500, obtenido {redondeo}"
    
    def test_redondear_con_denominacion_menor(self):
        """Prueba redondeo con denominación menor."""
        denominaciones = [2000, 5000, 10000]
        monto = Decimal("3000")
        
        redondeo = redondear_efectivo(monto, denominaciones)
        
        # Debería retornar 1000 (cantidad mínima necesaria para llegar a 4000, múltiplo de 2000)
        assert redondeo == Decimal("1000"), f"Esperado 1000, obtenido {redondeo}"


@pytest.mark.django_db
class TestSeleccionMonedaMontoForm:
    """Pruebas para el formulario SeleccionMonedaMontoForm."""
    
    @pytest.fixture
    def moneda_gbp(self):
        """Fixture que crea una moneda GBP de prueba."""
        return Moneda.objects.create(
            nombre="Libra esterlina",
            simbolo="GBP",
            tasa_base=9000,
            comision_compra=200,
            comision_venta=250,
            decimales=2,
            activa=True
        )
    
    def test_form_valido_con_datos_correctos(self, moneda_gbp):
        """Prueba que el formulario es válido con datos correctos."""
        form_data = {
            'moneda': moneda_gbp.id,
            'monto': '100.50'
        }
        form = SeleccionMonedaMontoForm(data=form_data)
        
        assert form.is_valid(), f"El formulario debería ser válido. Errores: {form.errors}"
    
    def test_form_invalido_monto_negativo(self, moneda_gbp):
        """Prueba que el formulario es inválido con monto negativo."""
        form_data = {
            'moneda': moneda_gbp.id,
            'monto': '-50'
        }
        form = SeleccionMonedaMontoForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con monto negativo"
        assert 'monto' in form.errors
        assert 'El monto debe ser mayor a 0.' in str(form.errors['monto'])
    
    def test_form_invalido_monto_cero(self, moneda_gbp):
        """Prueba que el formulario es inválido con monto cero."""
        form_data = {
            'moneda': moneda_gbp.id,
            'monto': '0'
        }
        form = SeleccionMonedaMontoForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con monto cero"
        assert 'monto' in form.errors
    
    def test_form_invalido_sin_moneda(self):
        """Prueba que el formulario es inválido sin moneda."""
        form_data = {
            'monto': '100'
        }
        form = SeleccionMonedaMontoForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido sin moneda"
        assert 'moneda' in form.errors
        assert 'Debes seleccionar una moneda.' in str(form.errors['moneda'])
    
    def test_form_invalido_sin_monto(self, moneda_gbp):
        """Prueba que el formulario es inválido sin monto."""
        form_data = {
            'moneda': moneda_gbp.id
        }
        form = SeleccionMonedaMontoForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido sin monto"
        assert 'monto' in form.errors


@pytest.mark.django_db
class TestVariablesForm:
    """Pruebas para el formulario VariablesForm."""
    
    def test_form_inicializa_con_valores_existentes(self):
        """Prueba que el formulario se inicializa con valores de la base de datos."""
        # Crear recargos de prueba
        Recargos.objects.update_or_create(
            marca='VISA',
            defaults={'medio': 'Tarjeta de Crédito', 'recargo': Decimal('1.5')}
        )
        
        form = VariablesForm()
        
        # Verificar que el campo tiene un valor inicial
        assert form.fields['recargo_visa'].initial is not None
    
    def test_form_valido_con_datos_correctos(self):
        """Prueba que el formulario es válido con datos correctos."""
        form_data = {
            'recargo_visa': '1.5',
            'recargo_mastercard': '2.0',
            'recargo_tigo_money': '2.5',
            'recargo_billetera_personal': '2.5',
            'recargo_zimple': '3.0',
            'recargo_panal': '2.0',
            'recargo_cabal': '1.0',
            'limite_diario': '90000000',
            'limite_mensual': '450000000'
        }
        form = VariablesForm(data=form_data)
        
        assert form.is_valid(), f"El formulario debería ser válido. Errores: {form.errors}"
    
    def test_form_invalido_recargo_negativo(self):
        """Prueba que el formulario es inválido con recargo negativo."""
        form_data = {
            'recargo_visa': '-1.0',
            'recargo_mastercard': '2.0',
            'recargo_tigo_money': '2.5',
            'recargo_billetera_personal': '2.5',
            'recargo_zimple': '3.0',
            'recargo_panal': '2.0',
            'recargo_cabal': '1.0',
            'limite_diario': '90000000',
            'limite_mensual': '450000000'
        }
        form = VariablesForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con recargo negativo"
        assert 'recargo_visa' in form.errors
        assert 'El recargo no puede ser negativo.' in str(form.errors['recargo_visa'])
    
    def test_form_invalido_recargo_mayor_100(self):
        """Prueba que el formulario es inválido con recargo mayor a 100%."""
        form_data = {
            'recargo_visa': '150.0',
            'recargo_mastercard': '2.0',
            'recargo_tigo_money': '2.5',
            'recargo_billetera_personal': '2.5',
            'recargo_zimple': '3.0',
            'recargo_panal': '2.0',
            'recargo_cabal': '1.0',
            'limite_diario': '90000000',
            'limite_mensual': '450000000'
        }
        form = VariablesForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con recargo mayor a 100%"
        assert 'recargo_visa' in form.errors, "Debe haber error en el campo recargo_visa"
    
    def test_form_invalido_limite_diario_cero(self):
        """Prueba que el formulario es inválido con límite diario en cero."""
        form_data = {
            'recargo_visa': '1.5',
            'recargo_mastercard': '2.0',
            'recargo_tigo_money': '2.5',
            'recargo_billetera_personal': '2.5',
            'recargo_zimple': '3.0',
            'recargo_panal': '2.0',
            'recargo_cabal': '1.0',
            'limite_diario': '0',
            'limite_mensual': '450000000'
        }
        form = VariablesForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con límite diario en cero"
        assert 'limite_diario' in form.errors
    
    def test_form_save_actualiza_valores(self):
        """Prueba que el método save actualiza los valores correctamente."""
        # Crear recargos iniciales
        Recargos.objects.update_or_create(
            marca='VISA',
            defaults={'medio': 'Tarjeta de Crédito', 'recargo': Decimal('1.0')}
        )
        
        form_data = {
            'recargo_visa': '2.5',
            'recargo_mastercard': '2.0',
            'recargo_tigo_money': '2.5',
            'recargo_billetera_personal': '2.5',
            'recargo_zimple': '3.0',
            'recargo_panal': '2.0',
            'recargo_cabal': '1.0',
            'limite_diario': '100000000',
            'limite_mensual': '500000000'
        }
        form = VariablesForm(data=form_data)
        
        assert form.is_valid()
        result = form.save()
        
        assert result == True
        
        # Verificar que se actualizó
        visa_recargo = Recargos.objects.get(marca='VISA')
        assert visa_recargo.recargo == Decimal('2.5')
