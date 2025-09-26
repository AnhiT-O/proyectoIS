import pytest
from django.core.exceptions import ValidationError
from monedas.models import Moneda
from clientes.models import Cliente


@pytest.mark.django_db
class TestMonedaModel:
    """Pruebas unitarias para el modelo Moneda"""

    def setup_method(self):
        """Limpiar la base de datos antes de cada prueba"""
        Moneda.objects.all().delete()

    def test_modelo_moneda_str_retorna_nombre(self):
        """
        Prueba 6: Modelo Moneda: método __str__ retorna el nombre correctamente.
        """
        moneda = Moneda(
            nombre='Euro',
            simbolo='EUR',
            tasa_base=8000,
            comision_compra=150,
            comision_venta=200
        )
        
        assert str(moneda) == 'Euro'

    def test_modelo_moneda_clean_error_simbolo_minusculas(self):
        """
        Prueba 7: Modelo Moneda: método clean lanza error si el símbolo no está en mayúsculas.
        """
        moneda = Moneda(
            nombre='Euro',
            simbolo='eur',  # Minúsculas
            tasa_base=8000,
            comision_compra=150,
            comision_venta=200
        )
        
        with pytest.raises(ValidationError) as exc_info:
            moneda.clean()
        
        assert 'simbolo' in exc_info.value.message_dict
        assert 'El símbolo debe contener solo letras en mayúsculas.' in exc_info.value.message_dict['simbolo']

    def test_modelo_moneda_calcular_precio_venta_sin_beneficio(self):
        """
        Prueba 8: Modelo Moneda: método calcular_precio_venta calcula correctamente el precio sin beneficio.
        """
        moneda = Moneda(
            nombre='Dólar',
            simbolo='USD',
            tasa_base=7400,
            comision_compra=200,
            comision_venta=250
        )
        
        precio_venta = moneda.calcular_precio_venta(0)
        # precio_venta = tasa_base + comision_venta - (comision_venta * 0)
        # precio_venta = 7400 + 250 - 0 = 7650
        assert precio_venta == 7650

    def test_modelo_moneda_calcular_precio_venta_con_beneficio(self):
        """
        Prueba 8: Modelo Moneda: método calcular_precio_venta calcula correctamente el precio con beneficio.
        """
        moneda = Moneda(
            nombre='Dólar',
            simbolo='USD',
            tasa_base=7400,
            comision_compra=200,
            comision_venta=250
        )
        
        precio_venta = moneda.calcular_precio_venta(10)  # 10% de beneficio
        # precio_venta = tasa_base + comision_venta - (comision_venta * 0.10)
        # precio_venta = 7400 + 250 - 25 = 7625
        assert precio_venta == 7625

    def test_modelo_moneda_calcular_precio_compra_sin_beneficio(self):
        """
        Prueba 9: Modelo Moneda: método calcular_precio_compra calcula correctamente el precio sin beneficio.
        """
        moneda = Moneda(
            nombre='Dólar',
            simbolo='USD',
            tasa_base=7400,
            comision_compra=200,
            comision_venta=250
        )
        
        precio_compra = moneda.calcular_precio_compra(0)
        # precio_compra = tasa_base - comision_compra + (comision_compra * 0)
        # precio_compra = 7400 - 200 + 0 = 7200
        assert precio_compra == 7200

    def test_modelo_moneda_calcular_precio_compra_con_beneficio(self):
        """
        Prueba 9: Modelo Moneda: método calcular_precio_compra calcula correctamente el precio con beneficio.
        """
        moneda = Moneda(
            nombre='Dólar',
            simbolo='USD',
            tasa_base=7400,
            comision_compra=200,
            comision_venta=250
        )
        
        precio_compra = moneda.calcular_precio_compra(10)  # 10% de beneficio
        # precio_compra = tasa_base - comision_compra + (comision_compra * 0.10)
        # precio_compra = 7400 - 200 + 20 = 7220
        assert precio_compra == 7220

    def test_modelo_moneda_get_precios_cliente_sin_cliente(self):
        """
        Prueba 10: Modelo Moneda: método get_precios_cliente sin cliente (beneficio 0%).
        """
        moneda = Moneda(
            nombre='Dólar',
            simbolo='USD',
            tasa_base=7400,
            comision_compra=200,
            comision_venta=250
        )
        
        precios = moneda.get_precios_cliente(None)
        
        assert precios['precio_venta'] == 7650  # Sin beneficio
        assert precios['precio_compra'] == 7200  # Sin beneficio

    def test_modelo_moneda_get_precios_cliente_con_cliente_minorista(self):
        """
        Prueba 10: Modelo Moneda: método get_precios_cliente aplica correctamente el beneficio del cliente minorista.
        """
        moneda = Moneda(
            nombre='Dólar',
            simbolo='USD',
            tasa_base=7400,
            comision_compra=200,
            comision_venta=250
        )
        
        cliente = Cliente(
            nombre='Cliente Test',
            tipoDocCliente='CI',
            docCliente='12345678',
            correoElecCliente='test@test.com',
            telefono='123456789',
            tipoCliente='F',
            direccion='Dirección test',
            ocupacion='Empleado',
            segmento='minorista',
            beneficio_segmento=0  # 0% de beneficio
        )
        
        precios = moneda.get_precios_cliente(cliente)
        
        # Con 0% de beneficio debería ser igual a sin cliente
        assert precios['precio_venta'] == 7650
        assert precios['precio_compra'] == 7200

    def test_modelo_moneda_get_precios_cliente_con_cliente_corporativo(self):
        """
        Prueba 10: Modelo Moneda: método get_precios_cliente aplica correctamente el beneficio del cliente corporativo.
        """
        moneda = Moneda(
            nombre='Dólar',
            simbolo='USD',
            tasa_base=7400,
            comision_compra=200,
            comision_venta=250
        )
        
        cliente = Cliente(
            nombre='Cliente Corporativo',
            tipoDocCliente='RUC',
            docCliente='12345678-9',
            correoElecCliente='corp@test.com',
            telefono='123456789',
            tipoCliente='J',
            direccion='Dirección corporativa',
            ocupacion='Empresa',
            segmento='corporativo',
            beneficio_segmento=5  # 5% de beneficio
        )
        
        precios = moneda.get_precios_cliente(cliente)
        
        # Con 5% de beneficio
        # precio_venta = 7400 + 250 - (250 * 0.05) = 7400 + 250 - 12.5 = 7637.5 -> 7637 (int)
        # precio_compra = 7400 - 200 + (200 * 0.05) = 7400 - 200 + 10 = 7210
        assert precios['precio_venta'] == 7637
        assert precios['precio_compra'] == 7210

    def test_modelo_moneda_get_precios_cliente_con_cliente_vip(self):
        """
        Prueba 10: Modelo Moneda: método get_precios_cliente aplica correctamente el beneficio del cliente VIP.
        """
        moneda = Moneda(
            nombre='Dólar',
            simbolo='USD',
            tasa_base=7400,
            comision_compra=200,
            comision_venta=250
        )
        
        cliente = Cliente(
            nombre='Cliente VIP',
            tipoDocCliente='CI',
            docCliente='98765432',
            correoElecCliente='vip@test.com',
            telefono='987654321',
            tipoCliente='F',
            direccion='Dirección VIP',
            ocupacion='Empresario',
            segmento='vip',
            beneficio_segmento=10  # 10% de beneficio
        )
        
        precios = moneda.get_precios_cliente(cliente)
        
        # Con 10% de beneficio
        # precio_venta = 7400 + 250 - (250 * 0.10) = 7400 + 250 - 25 = 7625
        # precio_compra = 7400 - 200 + (200 * 0.10) = 7400 - 200 + 20 = 7220
        assert precios['precio_venta'] == 7625
        assert precios['precio_compra'] == 7220