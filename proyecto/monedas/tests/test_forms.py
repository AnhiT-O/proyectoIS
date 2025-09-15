import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError

from monedas.forms import MonedaForm
from monedas.models import Moneda


class TestMonedaForm(TestCase):
    """
    Test suite para el formulario MonedaForm.
    Cubre validaciones, limpieza de datos, widgets y mensajes de error.
    """

    def setUp(self):
        """Configuración inicial para cada test."""
        self.datos_validos = {
            'nombre': 'Euro',
            'simbolo': 'EUR',
            'tasa_base': 8500,
            'comision_compra': 150,
            'comision_venta': 200,
            'decimales': 2
        }

    def test_form_con_datos_validos(self):
        """Test que verifica que el formulario acepta datos válidos."""
        form = MonedaForm(data=self.datos_validos)
        
        assert form.is_valid(), f"El formulario debería ser válido con datos correctos. Errores: {form.errors}"

    def test_form_save_crea_moneda(self):
        """Test que verifica que el formulario guarda correctamente la moneda."""
        form = MonedaForm(data=self.datos_validos)
        
        assert form.is_valid(), "El formulario debería ser válido antes de guardar"
        
        moneda = form.save()
        
        assert isinstance(moneda, Moneda), "Debería retornar una instancia de Moneda"
        assert moneda.nombre == 'Euro', "El nombre debería guardarse correctamente"
        assert moneda.simbolo == 'EUR', "El símbolo debería guardarse correctamente"
        assert moneda.tasa_base == 8500, "La tasa base debería guardarse correctamente"

    def test_form_campo_nombre_requerido(self):
        """Test que verifica que el campo nombre es requerido."""
        datos_sin_nombre = self.datos_validos.copy()
        del datos_sin_nombre['nombre']
        
        form = MonedaForm(data=datos_sin_nombre)
        
        assert not form.is_valid(), "El formulario no debería ser válido sin nombre"
        assert 'nombre' in form.errors, "Debería haber un error en el campo 'nombre'"
        assert 'Debes ingresar un nombre.' in str(form.errors['nombre']), "Debería mostrar el mensaje de error personalizado"

    def test_form_campo_simbolo_requerido(self):
        """Test que verifica que el campo símbolo es requerido."""
        datos_sin_simbolo = self.datos_validos.copy()
        del datos_sin_simbolo['simbolo']
        
        form = MonedaForm(data=datos_sin_simbolo)
        
        assert not form.is_valid(), "El formulario no debería ser válido sin símbolo"
        assert 'simbolo' in form.errors, "Debería haber un error en el campo 'simbolo'"
        assert 'Debes ingresar un símbolo.' in str(form.errors['simbolo']), "Debería mostrar el mensaje de error personalizado"

    def test_form_simbolo_maximo_3_caracteres(self):
        """Test que verifica que el símbolo no puede exceder 3 caracteres."""
        datos_simbolo_largo = self.datos_validos.copy()
        datos_simbolo_largo['simbolo'] = 'EURO'  # 4 caracteres
        
        form = MonedaForm(data=datos_simbolo_largo)
        
        assert not form.is_valid(), "El formulario no debería ser válido con símbolo de más de 3 caracteres"
        assert 'simbolo' in form.errors, "Debería haber un error en el campo 'simbolo'"

    def test_form_nombre_maximo_30_caracteres(self):
        """Test que verifica que el nombre no puede exceder 30 caracteres."""
        datos_nombre_largo = self.datos_validos.copy()
        datos_nombre_largo['nombre'] = 'A' * 31  # 31 caracteres
        
        form = MonedaForm(data=datos_nombre_largo)
        
        assert not form.is_valid(), "El formulario no debería ser válido con nombre de más de 30 caracteres"
        assert 'nombre' in form.errors, "Debería haber un error en el campo 'nombre'"

    def test_clean_simbolo_convierte_a_mayusculas(self):
        """Test que verifica que el método clean_simbolo convierte a mayúsculas."""
        datos_simbolo_minuscula = self.datos_validos.copy()
        datos_simbolo_minuscula['simbolo'] = 'eur'
        
        form = MonedaForm(data=datos_simbolo_minuscula)
        
        assert form.is_valid(), f"El formulario debería ser válido. Errores: {form.errors}"
        assert form.cleaned_data['simbolo'] == 'EUR', "El símbolo debería convertirse automáticamente a mayúsculas"

    def test_clean_simbolo_mixto_convierte_a_mayusculas(self):
        """Test que verifica la conversión de símbolos con mayúsculas y minúsculas mezcladas."""
        datos_simbolo_mixto = self.datos_validos.copy()
        datos_simbolo_mixto['simbolo'] = 'EuR'
        
        form = MonedaForm(data=datos_simbolo_mixto)
        
        assert form.is_valid(), "El formulario debería ser válido con símbolo mixto"
        assert form.cleaned_data['simbolo'] == 'EUR', "El símbolo debería convertirse completamente a mayúsculas"

    def test_clean_simbolo_solo_letras(self):
        """Test que verifica que el símbolo solo acepta letras."""
        simbolos_invalidos = ['12A', 'A1B', '123', 'A-B', 'A_B', 'A B']
        
        for simbolo_invalido in simbolos_invalidos:
            datos_invalidos = self.datos_validos.copy()
            datos_invalidos['simbolo'] = simbolo_invalido
            
            form = MonedaForm(data=datos_invalidos)
            
            assert not form.is_valid(), f"El formulario no debería ser válido con símbolo '{simbolo_invalido}'"
            assert 'simbolo' in form.errors, f"Debería haber un error para el símbolo '{simbolo_invalido}'"
            assert 'El símbolo debe contener solo letras.' in str(form.errors['simbolo']), f"Debería mostrar mensaje de error específico para '{simbolo_invalido}'"

    def test_clean_tasa_base_valor_none_convierte_a_cero(self):
        """Test que verifica que tasa_base None se convierte a 0."""
        datos_sin_tasa = self.datos_validos.copy()
        datos_sin_tasa['tasa_base'] = None
        
        form = MonedaForm(data=datos_sin_tasa)
        
        assert form.is_valid(), "El formulario debería ser válido sin tasa_base"
        assert form.cleaned_data['tasa_base'] == 0, "tasa_base None debería convertirse a 0"

    def test_clean_tasa_base_valor_vacio_convierte_a_cero(self):
        """Test que verifica que tasa_base vacía se convierte a 0."""
        datos_tasa_vacia = self.datos_validos.copy()
        datos_tasa_vacia['tasa_base'] = ''
        
        form = MonedaForm(data=datos_tasa_vacia)
        
        assert form.is_valid(), "El formulario debería ser válido con tasa_base vacía"
        assert form.cleaned_data['tasa_base'] == 0, "tasa_base vacía debería convertirse a 0"

    def test_clean_decimales_valor_none_convierte_a_tres(self):
        """Test que verifica que decimales None se convierte a 3."""
        datos_sin_decimales = self.datos_validos.copy()
        datos_sin_decimales['decimales'] = None
        
        form = MonedaForm(data=datos_sin_decimales)
        
        assert form.is_valid(), "El formulario debería ser válido sin decimales"
        assert form.cleaned_data['decimales'] == 3, "decimales None debería convertirse a 3"

    def test_clean_decimales_valor_vacio_convierte_a_tres(self):
        """Test que verifica que decimales vacío se convierte a 3."""
        datos_decimales_vacios = self.datos_validos.copy()
        datos_decimales_vacios['decimales'] = ''
        
        form = MonedaForm(data=datos_decimales_vacios)
        
        assert form.is_valid(), "El formulario debería ser válido con decimales vacío"
        assert form.cleaned_data['decimales'] == 3, "decimales vacío debería convertirse a 3"

    def test_campos_opcionales_pueden_ser_vacios(self):
        """Test que verifica que los campos opcionales pueden estar vacíos."""
        datos_minimos = {
            'nombre': 'Bitcoin',
            'simbolo': 'BTC'
        }
        
        form = MonedaForm(data=datos_minimos)
        
        assert form.is_valid(), f"El formulario debería ser válido solo con nombre y símbolo. Errores: {form.errors}"
        assert form.cleaned_data['tasa_base'] == 0, "tasa_base debería ser 0 por defecto"
        assert form.cleaned_data['decimales'] == 3, "decimales debería ser 3 por defecto"

    def test_form_widgets_tienen_clases_css(self):
        """Test que verifica que los widgets tienen las clases CSS correctas."""
        form = MonedaForm()
        
        # Verificar que todos los campos tienen la clase 'form-control'
        campos_con_form_control = ['nombre', 'simbolo', 'tasa_base', 'comision_compra', 'comision_venta', 'decimales']
        
        for campo in campos_con_form_control:
            widget_attrs = form.fields[campo].widget.attrs
            assert 'class' in widget_attrs, f"El campo '{campo}' debería tener atributo 'class'"
            assert 'form-control' in widget_attrs['class'], f"El campo '{campo}' debería tener la clase 'form-control'"

    def test_simbolo_widget_configuracion_especial(self):
        """Test que verifica la configuración especial del widget del símbolo."""
        form = MonedaForm()
        simbolo_widget = form.fields['simbolo'].widget
        
        assert simbolo_widget.attrs.get('maxlength') == '3', "El widget del símbolo debería tener maxlength='3'"
        assert 'text-transform: uppercase;' in simbolo_widget.attrs.get('style', ''), "El widget debería tener estilo para convertir a mayúsculas"

    def test_form_meta_configuration(self):
        """Test que verifica la configuración de Meta del formulario."""
        form = MonedaForm()
        
        assert form._meta.model == Moneda, "El modelo del formulario debería ser Moneda"
        
        campos_esperados = ['nombre', 'simbolo', 'tasa_base', 'decimales', 'comision_compra', 'comision_venta']
        assert form._meta.fields == campos_esperados, f"Los campos del formulario deberían ser {campos_esperados}"

    def test_form_con_instancia_existente(self):
        """Test que verifica que el formulario funciona correctamente con una instancia existente."""
        # Crear una moneda primero
        moneda_existente = Moneda.objects.create(
            nombre='Libra',
            simbolo='GBP',
            tasa_base=9000,
            comision_compra=180,
            comision_venta=230
        )
        
        form = MonedaForm(instance=moneda_existente)
        
        assert form.initial['nombre'] == 'Libra', "El formulario debería prellenar el nombre"
        assert form.initial['simbolo'] == 'GBP', "El formulario debería prellenar el símbolo"
        assert form.initial['tasa_base'] == 9000, "El formulario debería prellenar la tasa base"

    def test_form_edicion_con_datos_actualizados(self):
        """Test que verifica la edición de una moneda existente."""
        # Crear moneda inicial
        moneda = Moneda.objects.create(nombre='Yen', simbolo='JPY', tasa_base=50)
        
        # Datos para actualizar
        datos_actualizados = {
            'nombre': 'Yen Japonés',
            'simbolo': 'JPY',
            'tasa_base': 55,
            'comision_compra': 5,
            'comision_venta': 8,
            'decimales': 0
        }
        
        form = MonedaForm(data=datos_actualizados, instance=moneda)
        
        assert form.is_valid(), f"El formulario de edición debería ser válido. Errores: {form.errors}"
        
        moneda_actualizada = form.save()
        
        assert moneda_actualizada.nombre == 'Yen Japonés', "El nombre debería actualizarse"
        assert moneda_actualizada.tasa_base == 55, "La tasa base debería actualizarse"
        assert moneda_actualizada.pk == moneda.pk, "Debería ser la misma instancia actualizada"

    def test_form_validacion_unicidad_nombre(self):
        """Test que verifica la validación de unicidad del nombre."""
        # Crear moneda existente
        Moneda.objects.create(nombre='Peso', simbolo='PES')
        
        # Intentar crear otra con el mismo nombre
        datos_duplicados = self.datos_validos.copy()
        datos_duplicados['nombre'] = 'Peso'
        datos_duplicados['simbolo'] = 'PE2'
        
        form = MonedaForm(data=datos_duplicados)
        
        # El formulario puede ser válido en nivel de form, pero fallará en la base de datos
        # Esta validación se maneja en el modelo, no en el formulario
        if form.is_valid():
            with pytest.raises(Exception):  # IntegrityError esperado
                form.save()

    def test_form_validacion_unicidad_simbolo(self):
        """Test que verifica la validación de unicidad del símbolo."""
        # Crear moneda existente
        Moneda.objects.create(nombre='Real', simbolo='BRL')
        
        # Intentar crear otra con el mismo símbolo
        datos_duplicados = self.datos_validos.copy()
        datos_duplicados['nombre'] = 'Real Brasileño'
        datos_duplicados['simbolo'] = 'BRL'
        
        form = MonedaForm(data=datos_duplicados)
        
        # Similar al test anterior, la unicidad se valida en el modelo
        if form.is_valid():
            with pytest.raises(Exception):  # IntegrityError esperado
                form.save()