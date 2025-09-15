import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta
from unittest.mock import Mock

from monedas.models import Moneda


class TestMonedaModel(TestCase):
    """
    Test suite para el modelo Moneda.
    Cubre creación, validaciones, métodos de cálculo y comportamientos especiales.
    """

    def setUp(self):
        """Configuración inicial para cada test."""
        self.datos_moneda_validos = {
            'nombre': 'Euro',
            'simbolo': 'EUR',
            'activa': True,
            'tasa_base': 8500,
            'comision_compra': 150,
            'comision_venta': 200,
            'decimales': 2
        }

    def test_crear_moneda_exitosa(self):
        """Test que verifica la creación exitosa de una moneda con datos válidos."""
        moneda = Moneda.objects.create(**self.datos_moneda_validos)
        
        assert moneda.nombre == 'Euro', "El nombre de la moneda debería ser 'Euro'"
        assert moneda.simbolo == 'EUR', "El símbolo de la moneda debería ser 'EUR'"
        assert moneda.activa is True, "La moneda debería estar activa por defecto"
        assert moneda.tasa_base == 8500, "La tasa base debería ser 8500"
        assert moneda.comision_compra == 150, "La comisión de compra debería ser 150"
        assert moneda.comision_venta == 200, "La comisión de venta debería ser 200"
        assert moneda.decimales == 2, "Los decimales deberían ser 2"
        assert moneda.fecha_cotizacion is not None, "La fecha de cotización debería establecerse automáticamente"

    def test_valores_por_defecto(self):
        """Test que verifica los valores por defecto del modelo."""
        moneda = Moneda.objects.create(nombre='Test', simbolo='TST')
        
        assert moneda.activa is True, "El campo 'activa' debería ser True por defecto"
        assert moneda.tasa_base == 0, "La tasa base debería ser 0 por defecto"
        assert moneda.comision_compra == 0, "La comisión de compra debería ser 0 por defecto"
        assert moneda.comision_venta == 0, "La comisión de venta debería ser 0 por defecto"
        assert moneda.decimales == 3, "Los decimales deberían ser 3 por defecto"

    def test_validacion_simbolo_mayusculas(self):
        """Test que verifica que el símbolo debe estar en mayúsculas."""
        moneda = Moneda(nombre='Test', simbolo='eur')
        
        with pytest.raises(ValidationError) as exc_info:
            moneda.full_clean()
        
        assert 'simbolo' in exc_info.value.message_dict, "Debería haber un error de validación para el campo 'simbolo'"
        assert 'El símbolo debe contener solo letras en mayúsculas.' in str(exc_info.value), "El mensaje de error debería indicar que el símbolo debe estar en mayúsculas"

    def test_simbolo_mayusculas_valido(self):
        """Test que verifica que un símbolo en mayúsculas es válido."""
        moneda = Moneda(nombre='Test', simbolo='EUR')
        
        try:
            moneda.full_clean()
        except ValidationError:
            pytest.fail("No debería haber errores de validación con un símbolo en mayúsculas")

    def test_str_representation(self):
        """Test que verifica la representación string del modelo."""
        moneda = Moneda.objects.create(nombre='Peso Argentino', simbolo='ARS')
        
        assert str(moneda) == 'Peso Argentino', "La representación string debería ser el nombre de la moneda"

    def test_calcular_precios_con_valores_cero(self):
        """Test que verifica el cálculo con comisiones en cero."""
        moneda = Moneda.objects.create(
            nombre='Bitcoin',
            simbolo='BTC',
            tasa_base=50000,
            comision_compra=0,
            comision_venta=0
        )
        
        precio_venta = moneda.calcular_precio_venta(10)
        precio_compra = moneda.calcular_precio_compra(10)
        
        assert precio_venta == 50000, f"El precio de venta con comisión 0 debería ser 50000, pero fue {precio_venta}"
        assert precio_compra == 50000, f"El precio de compra con comisión 0 debería ser 50000, pero fue {precio_compra}"

    def test_get_precios_cliente_con_cliente_vip(self):
        """Test que verifica el cálculo de precios para cliente VIP (10% beneficio)."""
        moneda = Moneda.objects.create(
            nombre='Euro',
            simbolo='EUR',
            tasa_base=8500,
            comision_compra=150,
            comision_venta=200
        )
        
        # Mock de cliente VIP
        cliente_mock = Mock()
        cliente_mock.beneficio_segmento = 10
        
        precios = moneda.get_precios_cliente(cliente_mock)
        
        # precio_venta = 8500 + 200 - (200 * 0.10) = 8680
        precio_venta_esperado = 8500 + 200 - int(200 * 0.10)
        # precio_compra = 8500 - 150 + (150 * 0.10) = 8365
        precio_compra_esperado = 8500 - 150 + int(150 * 0.10)
        
        assert precios['precio_venta'] == precio_venta_esperado, f"El precio de venta para cliente VIP debería ser {precio_venta_esperado}, pero fue {precios['precio_venta']}"
        assert precios['precio_compra'] == precio_compra_esperado, f"El precio de compra para cliente VIP debería ser {precio_compra_esperado}, pero fue {precios['precio_compra']}"

    def test_get_precios_cliente_estructura_respuesta(self):
        """Test que verifica la estructura de la respuesta del método get_precios_cliente."""
        moneda = Moneda.objects.create(nombre='Test', simbolo='TST')
        precios = moneda.get_precios_cliente(None)
        
        assert isinstance(precios, dict), "La respuesta debería ser un diccionario"
        assert 'precio_venta' in precios, "La respuesta debería contener 'precio_venta'"
        assert 'precio_compra' in precios, "La respuesta debería contener 'precio_compra'"
        assert len(precios) == 2, "La respuesta debería contener exactamente 2 claves"

    def test_fecha_cotizacion_se_actualiza_al_cambiar_comision_compra(self):
        """Test que verifica que fecha_cotizacion se actualiza al cambiar comision_compra."""
        moneda = Moneda.objects.create(
            nombre='Euro',
            simbolo='EUR',
            comision_compra=150
        )
        fecha_original = moneda.fecha_cotizacion
        
        # Esperar un momento para asegurar diferencia de tiempo
        import time
        time.sleep(0.1)
        
        # Cambiar comision_compra
        moneda.comision_compra = 200
        moneda.save()
        
        assert moneda.fecha_cotizacion > fecha_original, "La fecha de cotización debería actualizarse al cambiar comision_compra"

    def test_fecha_cotizacion_se_actualiza_al_cambiar_comision_venta(self):
        """Test que verifica que fecha_cotizacion se actualiza al cambiar comision_venta."""
        moneda = Moneda.objects.create(
            nombre='Libra',
            simbolo='GBP',
            comision_venta=180
        )
        fecha_original = moneda.fecha_cotizacion
        
        # Esperar un momento para asegurar diferencia de tiempo
        import time
        time.sleep(0.1)
        
        # Cambiar comision_venta
        moneda.comision_venta = 220
        moneda.save()
        
        assert moneda.fecha_cotizacion > fecha_original, "La fecha de cotización debería actualizarse al cambiar comision_venta"

    def test_fecha_cotizacion_no_se_actualiza_en_creacion(self):
        """Test que verifica que la lógica de actualización no aplica en la creación inicial."""
        # Este test verifica que el método save() maneja correctamente cuando pk es None
        moneda = Moneda(
            nombre='Bitcoin',
            simbolo='BTC',
            tasa_base=50000
        )
        
        # No debería haber errores al guardar por primera vez
        try:
            moneda.save()
            assert moneda.fecha_cotizacion is not None, "La fecha de cotización debería establecerse en la creación"
        except Exception as e:
            pytest.fail(f"No debería haber errores al crear una nueva moneda: {e}")

    def test_meta_verbose_names(self):
        """Test que verifica los nombres verbose del modelo."""
        meta = Moneda._meta
        
        assert meta.verbose_name == 'Moneda', "El verbose_name debería ser 'Moneda'"
        assert meta.verbose_name_plural == 'Monedas', "El verbose_name_plural debería ser 'Monedas'"

    def test_meta_db_table(self):
        """Test que verifica el nombre de la tabla en la base de datos."""
        meta = Moneda._meta
        
        assert meta.db_table == 'monedas', "El nombre de la tabla debería ser 'monedas'"

    def test_meta_permisos_personalizados(self):
        """Test que verifica los permisos personalizados del modelo."""
        meta = Moneda._meta
        permisos_esperados = [
            ("gestion", "Puede gestionar monedas (crear y editar)"),
            ("activacion", "Puede activar/desactivar monedas"),
            ("cotizacion", "Puede actualizar cotización de monedas")
        ]
        
        assert meta.permissions == permisos_esperados, f"Los permisos deberían ser {permisos_esperados}, pero son {meta.permissions}"

    def test_meta_default_permissions_disabled(self):
        """Test que verifica que los permisos por defecto están deshabilitados."""
        meta = Moneda._meta
        
        assert meta.default_permissions == [], "Los permisos por defecto deberían estar deshabilitados (lista vacía)"

    def test_longitud_maxima_campos(self):
        """Test que verifica las longitudes máximas de los campos."""
        # Nombre muy largo (más de 30 caracteres)
        nombre_largo = 'a' * 31
        moneda = Moneda(nombre=nombre_largo, simbolo='TST')
        
        with pytest.raises(ValidationError) as exc_info:
            moneda.full_clean()
        
        assert 'nombre' in exc_info.value.message_dict, "Debería haber un error de validación para el campo 'nombre' cuando excede la longitud máxima"
        
        # Símbolo muy largo (más de 3 caracteres)
        simbolo_largo = 'ABCD'
        moneda = Moneda(nombre='Test', simbolo=simbolo_largo)
        
        with pytest.raises(ValidationError) as exc_info:
            moneda.full_clean()
        
        assert 'simbolo' in exc_info.value.message_dict, "Debería haber un error de validación para el campo 'simbolo' cuando excede la longitud máxima"