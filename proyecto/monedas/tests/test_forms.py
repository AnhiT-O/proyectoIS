import pytest
from django.forms import ValidationError
from django.db import transaction
from monedas.forms import MonedaForm
from monedas.models import Moneda


@pytest.mark.django_db
class TestMonedaForm:
    """Pruebas unitarias para MonedaForm"""
    
    def setup_method(self):
        """Limpiar la base de datos antes de cada prueba"""
        Moneda.objects.all().delete()
    
    def test_moneda_form_creacion_exitosa(self):
        """
        Prueba 1: MonedaForm: creación exitosa de moneda con datos válidos.
        """
        form_data = {
            'nombre': 'Euro',
            'simbolo': 'EUR',
            'tasa_base': 8000,
            'comision_compra': 150,
            'comision_venta': 200,
            'decimales': 2
        }
        form = MonedaForm(data=form_data)
        
        assert form.is_valid()
        moneda = form.save()
        assert moneda.nombre == 'Euro'
        assert moneda.simbolo == 'EUR'
        assert moneda.tasa_base == 8000
        assert moneda.comision_compra == 150
        assert moneda.comision_venta == 200
        assert moneda.decimales == 2

    def test_moneda_form_error_nombre_duplicado(self):
        """
        Prueba 2: MonedaForm: error si el nombre ya existe.
        """
        # Crear una moneda existente
        Moneda.objects.create(
            nombre='Dólar',
            simbolo='USD',
            tasa_base=7400,
            comision_compra=200,
            comision_venta=250
        )
        
        # Intentar crear otra con el mismo nombre
        form_data = {
            'nombre': 'Dólar',
            'simbolo': 'DLR',
            'tasa_base': 7500,
            'comision_compra': 200,
            'comision_venta': 250
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid()
        assert 'nombre' in form.errors
        # Verificar que el error contiene el mensaje de duplicado
        assert any('ya existe' in str(error).lower() for error in form.errors['nombre'])

    def test_moneda_form_error_nombre_vacio(self):
        """
        Prueba 2: MonedaForm: error si el nombre está vacío.
        """
        form_data = {
            'nombre': '',
            'simbolo': 'EUR',
            'tasa_base': 8000,
            'comision_compra': 150,
            'comision_venta': 200
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid()
        assert 'nombre' in form.errors
        assert 'Debes ingresar un nombre.' in form.errors['nombre']

    def test_moneda_form_error_simbolo_duplicado(self):
        """
        Prueba 3: MonedaForm: error si el símbolo ya existe.
        """
        # Crear una moneda existente
        Moneda.objects.create(
            nombre='Dólar',
            simbolo='USD',
            tasa_base=7400,
            comision_compra=200,
            comision_venta=250
        )
        
        # Intentar crear otra con el mismo símbolo
        form_data = {
            'nombre': 'Dólar Estadounidense',
            'simbolo': 'USD',
            'tasa_base': 7500,
            'comision_compra': 200,
            'comision_venta': 250
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid()
        assert 'simbolo' in form.errors

    def test_moneda_form_error_simbolo_no_letras(self):
        """
        Prueba 3: MonedaForm: error si el símbolo no es solo letras.
        """
        form_data = {
            'nombre': 'Bitcoin',
            'simbolo': 'BT1',  # Contiene número
            'tasa_base': 50000,
            'comision_compra': 1000,
            'comision_venta': 1200
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid()
        assert 'simbolo' in form.errors
        assert 'El símbolo debe contener solo letras.' in form.errors['simbolo']

    def test_moneda_form_simbolo_convierte_a_mayusculas(self):
        """
        Prueba 3: MonedaForm: el símbolo se convierte automáticamente a mayúsculas.
        """
        form_data = {
            'nombre': 'Euro',
            'simbolo': 'eur',  # Minúsculas
            'tasa_base': 8000,
            'comision_compra': 150,
            'comision_venta': 200
        }
        form = MonedaForm(data=form_data)
        
        assert form.is_valid()
        moneda = form.save()
        assert moneda.simbolo == 'EUR'  # Se convirtió a mayúsculas

    def test_moneda_form_error_tasa_base_negativa(self):
        """
        Prueba 4: MonedaForm: error si la tasa base es negativa.
        """
        form_data = {
            'nombre': 'Moneda Test',
            'simbolo': 'TST',
            'tasa_base': -100,  # Valor negativo
            'comision_compra': 50,
            'comision_venta': 60
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid()
        assert 'tasa_base' in form.errors

    def test_moneda_form_error_tasa_base_vacia(self):
        """
        Prueba 4: MonedaForm: error si la tasa base está vacía.
        """
        form_data = {
            'nombre': 'Moneda Test',
            'simbolo': 'TST',
            'tasa_base': '',  # Vacío
            'comision_compra': 50,
            'comision_venta': 60
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid()
        assert 'tasa_base' in form.errors
        assert 'Debes ingresar una tasa base.' in form.errors['tasa_base']

    def test_moneda_form_error_comision_compra_negativa(self):
        """
        Prueba 4: MonedaForm: error si la comisión de compra es negativa.
        """
        form_data = {
            'nombre': 'Moneda Test',
            'simbolo': 'TST',
            'tasa_base': 1000,
            'comision_compra': -50,  # Valor negativo
            'comision_venta': 60
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid()
        assert 'comision_compra' in form.errors

    def test_moneda_form_error_comision_compra_vacia(self):
        """
        Prueba 4: MonedaForm: error si la comisión de compra está vacía.
        """
        form_data = {
            'nombre': 'Moneda Test',
            'simbolo': 'TST',
            'tasa_base': 1000,
            'comision_compra': '',  # Vacío
            'comision_venta': 60
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid()
        assert 'comision_compra' in form.errors
        assert 'Debes ingresar una comisión de compra.' in form.errors['comision_compra']

    def test_moneda_form_error_comision_venta_negativa(self):
        """
        Prueba 4: MonedaForm: error si la comisión de venta es negativa.
        """
        form_data = {
            'nombre': 'Moneda Test',
            'simbolo': 'TST',
            'tasa_base': 1000,
            'comision_compra': 50,
            'comision_venta': -60  # Valor negativo
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid()
        assert 'comision_venta' in form.errors

    def test_moneda_form_error_comision_venta_vacia(self):
        """
        Prueba 4: MonedaForm: error si la comisión de venta está vacía.
        """
        form_data = {
            'nombre': 'Moneda Test',
            'simbolo': 'TST',
            'tasa_base': 1000,
            'comision_compra': 50,
            'comision_venta': ''  # Vacío
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid()
        assert 'comision_venta' in form.errors
        assert 'Debes ingresar una comisión de venta.' in form.errors['comision_venta']

    def test_moneda_form_decimales_default_es_3(self):
        """
        Prueba 5: MonedaForm: el campo decimales por defecto es 3 si no se especifica.
        """
        form_data = {
            'nombre': 'Moneda Test',
            'simbolo': 'TST',
            'tasa_base': 1000,
            'comision_compra': 50,
            'comision_venta': 60
            # No incluimos 'decimales'
        }
        form = MonedaForm(data=form_data)
        
        assert form.is_valid()
        moneda = form.save()
        assert moneda.decimales == 3  # Valor por defecto