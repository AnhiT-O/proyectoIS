"""
Pruebas unitarias para la aplicación monedas.

Este módulo contiene las pruebas unitarias para los modelos, formularios y vistas
de la aplicación monedas usando pytest.
"""

import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from monedas.models import (
    Moneda, 
    StockGuaranies, 
    Denominacion, 
    HistorialCotizacion
)
from monedas.forms import MonedaForm
from clientes.models import Cliente


@pytest.mark.django_db
class TestMonedaModel:
    """Pruebas para el modelo Moneda."""
    
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
    
    def test_crear_moneda(self, moneda_eur):
        """Prueba la creación de una moneda."""
        assert moneda_eur.nombre == "Euro"
        assert moneda_eur.simbolo == "EUR"
        assert moneda_eur.tasa_base == 8000
        assert moneda_eur.comision_compra == 150
        assert moneda_eur.comision_venta == 200
        assert moneda_eur.activa == True
    
    def test_moneda_str(self, moneda_eur):
        """Prueba el método __str__ de Moneda."""
        assert str(moneda_eur) == "Euro"
    
    def test_calcular_precio_venta_minorista(self, moneda_eur):
        """Prueba el cálculo del precio de venta para cliente minorista."""
        # minorista: sin beneficio
        # precio_venta = tasa_base + comision_venta = 8000 + 200 = 8200
        precio = moneda_eur.calcular_precio_venta('minorista')
        assert precio == 8200, f"Esperado 8200, obtuvo {precio}"
    
    def test_calcular_precio_venta_corporativo(self, moneda_eur):
        """Prueba el cálculo del precio de venta para cliente corporativo (5% de beneficio)."""
        # corporativo: beneficio del 5%
        # precio_venta = tasa_base + comision_venta - (comision_venta * 0.05)
        # = 8000 + 200 - (200 * 0.05) = 8000 + 200 - 10 = 8190
        precio = moneda_eur.calcular_precio_venta('corporativo')
        assert precio == 8190, f"Esperado 8190, obtuvo {precio}"
    
    def test_calcular_precio_venta_vip(self, moneda_eur):
        """Prueba el cálculo del precio de venta para cliente VIP (10% de beneficio)."""
        # vip: beneficio del 10%
        # precio_venta = tasa_base + comision_venta - (comision_venta * 0.10)
        # = 8000 + 200 - (200 * 0.10) = 8000 + 200 - 20 = 8180
        precio = moneda_eur.calcular_precio_venta('vip')
        assert precio == 8180, f"Esperado 8180, obtuvo {precio}"
    
    def test_calcular_precio_compra_minorista(self, moneda_eur):
        """Prueba el cálculo del precio de compra para cliente minorista."""
        # minorista: sin beneficio
        # precio_compra = tasa_base - comision_compra = 8000 - 150 = 7850
        precio = moneda_eur.calcular_precio_compra('minorista')
        assert precio == 7850, f"Esperado 7850, obtuvo {precio}"
    
    def test_calcular_precio_compra_corporativo(self, moneda_eur):
        """Prueba el cálculo del precio de compra para cliente corporativo (5% de beneficio)."""
        # corporativo: beneficio del 5%
        # precio_compra = tasa_base - comision_compra + (comision_compra * 0.05)
        # = 8000 - 150 + (150 * 0.05) = 8000 - 150 + 7.5 = 7857.5 = 7857
        precio = moneda_eur.calcular_precio_compra('corporativo')
        assert precio == 7857, f"Esperado 7857, obtuvo {precio}"
    
    def test_calcular_precio_compra_vip(self, moneda_eur):
        """Prueba el cálculo del precio de compra para cliente VIP (10% de beneficio)."""
        # vip: beneficio del 10%
        # precio_compra = tasa_base - comision_compra + (comision_compra * 0.10)
        # = 8000 - 150 + (150 * 0.10) = 8000 - 150 + 15 = 7865
        precio = moneda_eur.calcular_precio_compra('vip')
        assert precio == 7865, f"Esperado 7865, obtuvo {precio}"
    
    def test_clean_simbolo_mayuscula(self):
        """Prueba que el método clean valida que el símbolo esté en mayúsculas."""
        moneda = Moneda(
            nombre="Libra esterlina",
            simbolo="gbp",  # En minúsculas
            tasa_base=9000,
            comision_compra=200,
            comision_venta=250
        )
        
        with pytest.raises(ValidationError) as exc_info:
            moneda.clean()
        
        assert 'simbolo' in exc_info.value.message_dict
        assert 'El símbolo debe contener solo letras en mayúsculas.' in str(exc_info.value)


@pytest.mark.django_db
class TestStockGuaraniesModel:
    """Pruebas para el modelo StockGuaranies."""
    
    def test_crear_stock_guaranies(self):
        """Prueba la creación del stock de guaraníes."""
        stock = StockGuaranies.objects.create(cantidad=5000000000)
        
        assert stock.cantidad == 5000000000
    
    def test_stock_guaranies_str(self):
        """Prueba el método __str__ de StockGuaranies."""
        stock = StockGuaranies.objects.create(cantidad=1000000000)
        
        assert "Stock: Gs. 1,000,000,000" in str(stock)


@pytest.mark.django_db
class TestDenominacionModel:
    """Pruebas para el modelo Denominacion."""
    
    @pytest.fixture
    def moneda_usd(self):
        """Fixture que obtiene o crea una moneda USD de prueba."""
        moneda, created = Moneda.objects.get_or_create(
            simbolo="USD",
            defaults={
                'nombre': "Dólar estadounidense",
                'tasa_base': 7000,
                'comision_compra': 100,
                'comision_venta': 150
            }
        )
        return moneda
    
    def test_crear_denominacion(self, moneda_usd):
        """Prueba la creación de una denominación."""
        denominacion = Denominacion.objects.create(
            moneda=moneda_usd,
            valor=100
        )
        
        assert denominacion.moneda == moneda_usd
        assert denominacion.valor == 100
    
    def test_denominacion_str(self, moneda_usd):
        """Prueba el método __str__ de Denominacion."""
        denominacion = Denominacion.objects.create(
            moneda=moneda_usd,
            valor=50
        )
        
        assert str(denominacion) == "50"


@pytest.mark.django_db
class TestHistorialCotizacionModel:
    """Pruebas para el modelo HistorialCotizacion."""
    
    @pytest.fixture
    def moneda_usd(self):
        """Fixture que obtiene o crea una moneda USD de prueba."""
        moneda, created = Moneda.objects.get_or_create(
            simbolo="USD",
            defaults={
                'nombre': "Dólar estadounidense",
                'tasa_base': 7000,
                'comision_compra': 100,
                'comision_venta': 150
            }
        )
        return moneda
    
    def test_crear_historial_cotizacion(self, moneda_usd):
        """Prueba la creación de un historial de cotización."""
        fecha_hoy = timezone.now().date()
        historial = HistorialCotizacion.objects.create(
            moneda=moneda_usd,
            fecha=fecha_hoy,
            tasa_base=7000,
            comision_compra=100,
            comision_venta=150
        )
        
        assert historial.moneda == moneda_usd
        assert historial.fecha == fecha_hoy
        assert historial.tasa_base == 7000
    
    def test_historial_calcula_precios_automaticamente(self, moneda_usd):
        """Prueba que el método save calcula automáticamente los precios."""
        fecha_hoy = timezone.now().date()
        historial = HistorialCotizacion.objects.create(
            moneda=moneda_usd,
            fecha=fecha_hoy,
            tasa_base=7000,
            comision_compra=100,
            comision_venta=150
        )
        
        # precio_compra = tasa_base - comision_compra = 7000 - 100 = 6900
        # precio_venta = tasa_base + comision_venta = 7000 + 150 = 7150
        assert historial.precio_compra == 6900
        assert historial.precio_venta == 7150
    
    def test_historial_guarda_nombre_moneda(self, moneda_usd):
        """Prueba que el método save guarda automáticamente el nombre de la moneda."""
        fecha_hoy = timezone.now().date()
        historial = HistorialCotizacion.objects.create(
            moneda=moneda_usd,
            fecha=fecha_hoy,
            tasa_base=7000,
            comision_compra=100,
            comision_venta=150
        )
        
        assert historial.nombre_moneda == "Dólar estadounidense"
    
    def test_historial_cotizacion_str(self, moneda_usd):
        """Prueba el método __str__ de HistorialCotizacion."""
        fecha_hoy = timezone.now().date()
        historial = HistorialCotizacion.objects.create(
            moneda=moneda_usd,
            fecha=fecha_hoy,
            tasa_base=7000,
            comision_compra=100,
            comision_venta=150
        )
        
        str_esperado = f"Dólar estadounidense - {fecha_hoy}"
        assert str(historial) == str_esperado


@pytest.mark.django_db
class TestMonedaForm:
    """Pruebas para el formulario MonedaForm."""
    
    def test_form_valido_con_datos_correctos(self):
        """Prueba que el formulario es válido con datos correctos."""
        form_data = {
            'nombre': 'Libra esterlina',
            'simbolo': 'GBP',
            'tasa_base': 9000,
            'comision_compra': 200,
            'comision_venta': 250,
            'decimales': 2,
            'denominaciones': '5,10,20,50'
        }
        form = MonedaForm(data=form_data)
        
        assert form.is_valid(), f"El formulario debería ser válido. Errores: {form.errors}"
    
    def test_form_convierte_simbolo_a_mayusculas(self):
        """Prueba que el formulario convierte el símbolo a mayúsculas automáticamente."""
        form_data = {
            'nombre': 'Yen japonés',
            'simbolo': 'jpy',  # En minúsculas
            'tasa_base': 50,
            'comision_compra': 5,
            'comision_venta': 8,
            'decimales': 0,
            'denominaciones': '1000,5000,10000'
        }
        form = MonedaForm(data=form_data)
        
        assert form.is_valid(), f"El formulario debería ser válido. Errores: {form.errors}"
        assert form.cleaned_data['simbolo'] == 'JPY'
    
    def test_form_invalido_simbolo_con_numeros(self):
        """Prueba que el formulario es inválido con símbolo que contiene números."""
        form_data = {
            'nombre': 'Test moneda',
            'simbolo': 'US1',  # Contiene número
            'tasa_base': 7000,
            'comision_compra': 100,
            'comision_venta': 150,
            'decimales': 2,
            'denominaciones': '1,5,10'
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con símbolo que contiene números"
        assert 'simbolo' in form.errors
        assert 'El símbolo debe contener solo letras.' in str(form.errors['simbolo'])
    
    def test_form_invalido_tasa_base_negativa(self):
        """Prueba que el formulario es inválido con tasa base negativa."""
        form_data = {
            'nombre': 'Test moneda',
            'simbolo': 'TST',
            'tasa_base': -100,  # Negativa
            'comision_compra': 50,
            'comision_venta': 75,
            'decimales': 2,
            'denominaciones': '1,5,10'
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con tasa base negativa"
        assert 'tasa_base' in form.errors
        assert 'La tasa base debe ser un número positivo.' in str(form.errors['tasa_base'])
    
    def test_form_invalido_comision_compra_negativa(self):
        """Prueba que el formulario es inválido con comisión de compra negativa."""
        form_data = {
            'nombre': 'Test moneda',
            'simbolo': 'TST',
            'tasa_base': 7000,
            'comision_compra': -50,  # Negativa
            'comision_venta': 75,
            'decimales': 2,
            'denominaciones': '1,5,10'
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con comisión de compra negativa"
        assert 'comision_compra' in form.errors
        assert 'La comisión de compra debe ser un número positivo.' in str(form.errors['comision_compra'])
    
    def test_form_invalido_comision_venta_negativa(self):
        """Prueba que el formulario es inválido con comisión de venta negativa."""
        form_data = {
            'nombre': 'Test moneda',
            'simbolo': 'TST',
            'tasa_base': 7000,
            'comision_compra': 50,
            'comision_venta': -75,  # Negativa
            'decimales': 2,
            'denominaciones': '1,5,10'
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con comisión de venta negativa"
        assert 'comision_venta' in form.errors
        assert 'La comisión de venta debe ser un número positivo.' in str(form.errors['comision_venta'])
    
    def test_form_invalido_decimales_mayor_8(self):
        """Prueba que el formulario es inválido con más de 8 decimales."""
        form_data = {
            'nombre': 'Test moneda',
            'simbolo': 'TST',
            'tasa_base': 7000,
            'comision_compra': 50,
            'comision_venta': 75,
            'decimales': 10,  # Mayor a 8
            'denominaciones': '1,5,10'
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con más de 8 decimales"
        assert 'decimales' in form.errors
        assert 'El número de decimales no puede ser mayor a 8.' in str(form.errors['decimales'])
    
    def test_form_invalido_sin_denominaciones(self):
        """Prueba que el formulario es inválido sin denominaciones."""
        form_data = {
            'nombre': 'Test moneda',
            'simbolo': 'TST',
            'tasa_base': 7000,
            'comision_compra': 50,
            'comision_venta': 75,
            'decimales': 2,
            'denominaciones': ''  # Vacío
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido sin denominaciones"
        assert 'denominaciones' in form.errors
    
    def test_form_convierte_denominaciones_a_lista(self):
        """Prueba que el formulario convierte correctamente las denominaciones a lista."""
        form_data = {
            'nombre': 'Test moneda',
            'simbolo': 'TST',
            'tasa_base': 7000,
            'comision_compra': 50,
            'comision_venta': 75,
            'decimales': 2,
            'denominaciones': '1, 5, 10, 20, 50'  # Con espacios
        }
        form = MonedaForm(data=form_data)
        
        assert form.is_valid(), f"El formulario debería ser válido. Errores: {form.errors}"
        assert form.cleaned_data['denominaciones'] == [1, 5, 10, 20, 50]
    
    def test_form_elimina_denominaciones_duplicadas(self):
        """Prueba que el formulario elimina denominaciones duplicadas y ordena."""
        form_data = {
            'nombre': 'Test moneda',
            'simbolo': 'TST',
            'tasa_base': 7000,
            'comision_compra': 50,
            'comision_venta': 75,
            'decimales': 2,
            'denominaciones': '10, 5, 10, 20, 5'  # Con duplicados
        }
        form = MonedaForm(data=form_data)
        
        assert form.is_valid(), f"El formulario debería ser válido. Errores: {form.errors}"
        assert form.cleaned_data['denominaciones'] == [5, 10, 20]
    
    def test_form_invalido_denominacion_negativa(self):
        """Prueba que el formulario es inválido con denominaciones negativas."""
        form_data = {
            'nombre': 'Test moneda',
            'simbolo': 'TST',
            'tasa_base': 7000,
            'comision_compra': 50,
            'comision_venta': 75,
            'decimales': 2,
            'denominaciones': '1, 5, -10'  # Contiene negativo
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con denominaciones negativas"
        assert 'denominaciones' in form.errors
        assert 'Todas las denominaciones deben ser números positivos.' in str(form.errors['denominaciones'])
