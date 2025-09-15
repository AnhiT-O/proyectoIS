import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from medios_pago.forms import TarjetaCreditoForm, CuentaBancariaForm


@pytest.mark.django_db
class TestTarjetaCreditoForm:
    """Pruebas unitarias para el formulario TarjetaCreditoForm"""

    def test_formulario_valido_con_todos_los_campos(self):
        """Test que verifica que el formulario es válido con todos los campos correctos"""
        form_data = {
            'numero_tarjeta': '1234567890123456',
            'cvv': '123',
            'nombre_titular_tarjeta': 'Juan Pérez González',
            'fecha_vencimiento_tc': '12/2025',
            'descripcion_tarjeta': 'Tarjeta personal principal',
            'moneda_tc': 'PYG'
        }
        form = TarjetaCreditoForm(data=form_data)
        
        assert form.is_valid(), f"El formulario debe ser válido. Errores: {form.errors}"

    def test_numero_tarjeta_valido_16_digitos(self):
        """Test que verifica que se acepta un número de tarjeta válido de 16 dígitos"""
        form_data = {
            'numero_tarjeta': '1234567890123456',
            'cvv': '123',
            'nombre_titular_tarjeta': 'Juan Pérez',
            'fecha_vencimiento_tc': '12/2025',
            'descripcion_tarjeta': 'Tarjeta personal',
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        form.is_valid()
        
        cleaned_numero = form.cleaned_data.get('numero_tarjeta')
        assert cleaned_numero == '1234567890123456', f"El número de tarjeta debe ser '1234567890123456' pero se obtuvo '{cleaned_numero}'"

    def test_numero_tarjeta_invalido_mas_16_digitos(self):
        """Test que verifica que se rechaza un número de tarjeta con más de 16 dígitos"""
        form_data = {
            'numero_tarjeta': '123456789012345678',  # 18 dígitos
            'cvv': '123',
            'nombre_titular_tarjeta': 'Juan Pérez',
            'fecha_vencimiento_tc': '12/2025',
            'descripcion_tarjeta': 'Tarjeta personal',
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debe ser válido con número de tarjeta de más de 16 dígitos"
        assert 'numero_tarjeta' in form.errors, "Debe haber error en el campo numero_tarjeta"

    def test_numero_tarjeta_invalido_con_letras(self):
        """Test que verifica que se rechaza un número de tarjeta con letras"""
        form_data = {
            'numero_tarjeta': '1234567890123abc',  # Contiene letras
            'cvv': '123',
            'nombre_titular_tarjeta': 'Juan Pérez',
            'fecha_vencimiento_tc': '12/2025',
            'descripcion_tarjeta': 'Tarjeta personal',
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debe ser válido con número de tarjeta que contiene letras"
        assert 'numero_tarjeta' in form.errors, "Debe haber error en el campo numero_tarjeta"
        assert 'debe contener solo dígitos' in str(form.errors['numero_tarjeta']), "El mensaje debe mencionar que solo acepta dígitos"

    def test_cvv_valido_3_digitos(self):
        """Test que verifica que se acepta un CVV válido de 3 dígitos"""
        form_data = {
            'numero_tarjeta': '1234567890123456',
            'cvv': '456',
            'nombre_titular_tarjeta': 'Juan Pérez',
            'fecha_vencimiento_tc': '12/2025',
            'descripcion_tarjeta': 'Tarjeta personal',
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        form.is_valid()
        
        cleaned_cvv = form.cleaned_data.get('cvv')
        assert cleaned_cvv == '456', f"El CVV debe ser '456' pero se obtuvo '{cleaned_cvv}'"

    def test_cvv_invalido_mas_3_digitos(self):
        """Test que verifica que se rechaza un CVV con más de 3 dígitos"""
        form_data = {
            'numero_tarjeta': '1234567890123456',
            'cvv': '1234',  # 4 dígitos
            'nombre_titular_tarjeta': 'Juan Pérez',
            'fecha_vencimiento_tc': '12/2025',
            'descripcion_tarjeta': 'Tarjeta personal',
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debe ser válido con CVV de más de 3 dígitos"
        assert 'cvv' in form.errors, "Debe haber error en el campo cvv"

    def test_cvv_invalido_con_letras(self):
        """Test que verifica que se rechaza un CVV con letras"""
        form_data = {
            'numero_tarjeta': '1234567890123456',
            'cvv': '12a',  # Contiene letra
            'nombre_titular_tarjeta': 'Juan Pérez',
            'fecha_vencimiento_tc': '12/2025',
            'descripcion_tarjeta': 'Tarjeta personal',
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debe ser válido con CVV que contiene letras"
        assert 'cvv' in form.errors, "Debe haber error en el campo cvv"
        assert 'debe contener solo dígitos' in str(form.errors['cvv']), "El mensaje debe mencionar que solo acepta dígitos"

    def test_nombre_titular_valido_normalizado(self):
        """Test que verifica que el nombre del titular se normaliza a mayúsculas"""
        form_data = {
            'numero_tarjeta': '1234567890123456',
            'cvv': '123',
            'nombre_titular_tarjeta': 'juan pérez gonzález',  # En minúsculas
            'fecha_vencimiento_tc': '12/2025',
            'descripcion_tarjeta': 'Tarjeta personal',
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        form.is_valid()
        
        cleaned_nombre = form.cleaned_data.get('nombre_titular_tarjeta')
        assert cleaned_nombre == 'JUAN PÉREZ GONZÁLEZ', f"El nombre debe normalizarse a mayúsculas. Se esperaba 'JUAN PÉREZ GONZÁLEZ' pero se obtuvo '{cleaned_nombre}'"

    def test_nombre_titular_invalido_muy_corto(self):
        """Test que verifica que se rechaza un nombre muy corto"""
        form_data = {
            'numero_tarjeta': '1234567890123456',
            'cvv': '123',
            'nombre_titular_tarjeta': 'Jo',  # Solo 2 caracteres
            'fecha_vencimiento_tc': '12/2025',
            'descripcion_tarjeta': 'Tarjeta personal',
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debe ser válido con nombre muy corto"
        assert 'nombre_titular_tarjeta' in form.errors, "Debe haber error en el campo nombre_titular_tarjeta"
        assert 'debe tener al menos 3 caracteres' in str(form.errors['nombre_titular_tarjeta']), "El mensaje debe mencionar los 3 caracteres mínimos"

    def test_fecha_vencimiento_valida(self):
        """Test que verifica que se acepta una fecha de vencimiento válida"""
        form_data = {
            'numero_tarjeta': '1234567890123456',
            'cvv': '123',
            'nombre_titular_tarjeta': 'Juan Pérez',
            'fecha_vencimiento_tc': '06/2027',
            'descripcion_tarjeta': 'Tarjeta personal',
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        form.is_valid()
        
        cleaned_fecha = form.cleaned_data.get('fecha_vencimiento_tc')
        assert cleaned_fecha == '06/2027', f"La fecha debe ser '06/2027' pero se obtuvo '{cleaned_fecha}'"

    def test_fecha_vencimiento_invalida_mes_incorrecto(self):
        """Test que verifica que se rechaza una fecha con mes inválido"""
        form_data = {
            'numero_tarjeta': '1234567890123456',
            'cvv': '123',
            'nombre_titular_tarjeta': 'Juan Pérez',
            'fecha_vencimiento_tc': '13/2025',  # Mes 13 no existe
            'descripcion_tarjeta': 'Tarjeta personal',
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debe ser válido con mes inválido"
        assert 'fecha_vencimiento_tc' in form.errors, "Debe haber error en el campo fecha_vencimiento_tc"

    def test_descripcion_tarjeta_valida_normalizada(self):
        """Test que verifica que la descripción se normaliza correctamente"""
        form_data = {
            'numero_tarjeta': '1234567890123456',
            'cvv': '123',
            'nombre_titular_tarjeta': 'Juan Pérez',
            'fecha_vencimiento_tc': '12/2025',
            'descripcion_tarjeta': '  Mi tarjeta personal  ',  # Con espacios
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        form.is_valid()
        
        cleaned_descripcion = form.cleaned_data.get('descripcion_tarjeta')
        assert cleaned_descripcion == 'Mi tarjeta personal', f"La descripción debe normalizarse sin espacios. Se esperaba 'Mi tarjeta personal' pero se obtuvo '{cleaned_descripcion}'"

    def test_descripcion_tarjeta_invalida_muy_corta(self):
        """Test que verifica que se rechaza una descripción muy corta"""
        form_data = {
            'numero_tarjeta': '1234567890123456',
            'cvv': '123',
            'nombre_titular_tarjeta': 'Juan Pérez',
            'fecha_vencimiento_tc': '12/2025',
            'descripcion_tarjeta': 'Mi',  # Solo 2 caracteres
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debe ser válido con descripción muy corta"
        assert 'descripcion_tarjeta' in form.errors, "Debe haber error en el campo descripcion_tarjeta"
        assert 'debe tener al menos 3 caracteres' in str(form.errors['descripcion_tarjeta']), "El mensaje debe mencionar los 3 caracteres mínimos"

    def test_moneda_tc_valida_pyg(self):
        """Test que verifica que se acepta PYG como moneda válida"""
        form_data = {
            'numero_tarjeta': '1234567890123456',
            'cvv': '123',
            'nombre_titular_tarjeta': 'Juan Pérez',
            'fecha_vencimiento_tc': '12/2025',
            'descripcion_tarjeta': 'Tarjeta personal',
            'moneda_tc': 'PYG'
        }
        form = TarjetaCreditoForm(data=form_data)
        
        assert form.is_valid(), f"El formulario debe ser válido con moneda PYG. Errores: {form.errors}"

    def test_moneda_tc_valida_usd(self):
        """Test que verifica que se acepta USD como moneda válida"""
        form_data = {
            'numero_tarjeta': '1234567890123456',
            'cvv': '123',
            'nombre_titular_tarjeta': 'Juan Pérez',
            'fecha_vencimiento_tc': '12/2025',
            'descripcion_tarjeta': 'Tarjeta personal',
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        
        assert form.is_valid(), f"El formulario debe ser válido con moneda USD. Errores: {form.errors}"

    def test_formulario_invalido_campo_requerido_faltante(self):
        """Test que verifica que el formulario es inválido cuando falta un campo requerido"""
        form_data = {
            'numero_tarjeta': '1234567890123456',
            # Falta el CVV
            'nombre_titular_tarjeta': 'Juan Pérez',
            'fecha_vencimiento_tc': '12/2025',
            'descripcion_tarjeta': 'Tarjeta personal',
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debe ser válido cuando falta un campo requerido"
        assert 'cvv' in form.errors, "Debe haber error en el campo cvv faltante"


@pytest.mark.django_db
class TestCuentaBancariaForm:
    """Pruebas unitarias para el formulario CuentaBancariaForm"""

    def test_formulario_valido_con_todos_los_campos(self):
        """Test que verifica que el formulario es válido con todos los campos correctos"""
        form_data = {
            'banco': 'Banco Nacional de Fomento',
            'numero_cuenta': '1234567890',
            'nombre_titular_cuenta': 'Juan Pérez González',
            'tipo_cuenta': 'corriente'
        }
        form = CuentaBancariaForm(data=form_data)
        
        assert form.is_valid(), f"El formulario debe ser válido. Errores: {form.errors}"

    def test_numero_cuenta_valido_largo_suficiente(self):
        """Test que verifica que se acepta un número de cuenta válido"""
        form_data = {
            'banco': 'Banco Nacional',
            'numero_cuenta': '123456789012345',
            'nombre_titular_cuenta': 'Juan Pérez',
            'tipo_cuenta': 'ahorro'
        }
        form = CuentaBancariaForm(data=form_data)
        form.is_valid()
        
        cleaned_numero = form.cleaned_data.get('numero_cuenta')
        assert cleaned_numero == '123456789012345', f"El número de cuenta debe ser '123456789012345' pero se obtuvo '{cleaned_numero}'"

    def test_numero_cuenta_invalido_muy_corto(self):
        """Test que verifica que se rechaza un número de cuenta muy corto"""
        form_data = {
            'banco': 'Banco Nacional',
            'numero_cuenta': '12345',  # Solo 5 caracteres
            'nombre_titular_cuenta': 'Juan Pérez',
            'tipo_cuenta': 'corriente'
        }
        form = CuentaBancariaForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debe ser válido con número de cuenta muy corto"
        assert 'numero_cuenta' in form.errors, "Debe haber error en el campo numero_cuenta"
        assert 'debe tener al menos 6 caracteres' in str(form.errors['numero_cuenta']), "El mensaje debe mencionar los 6 caracteres mínimos"

    def test_numero_cuenta_normalizado_sin_espacios(self):
        """Test que verifica que el número de cuenta se normaliza sin espacios"""
        form_data = {
            'banco': 'Banco Nacional',
            'numero_cuenta': '  1234567890  ',  # Con espacios
            'nombre_titular_cuenta': 'Juan Pérez',
            'tipo_cuenta': 'corriente'
        }
        form = CuentaBancariaForm(data=form_data)
        form.is_valid()
        
        cleaned_numero = form.cleaned_data.get('numero_cuenta')
        assert cleaned_numero == '1234567890', f"El número debe normalizarse sin espacios. Se esperaba '1234567890' pero se obtuvo '{cleaned_numero}'"

    def test_nombre_titular_cuenta_valido_normalizado(self):
        """Test que verifica que el nombre del titular se normaliza a mayúsculas"""
        form_data = {
            'banco': 'Banco Nacional',
            'numero_cuenta': '1234567890',
            'nombre_titular_cuenta': 'juan pérez gonzález',  # En minúsculas
            'tipo_cuenta': 'corriente'
        }
        form = CuentaBancariaForm(data=form_data)
        form.is_valid()
        
        cleaned_nombre = form.cleaned_data.get('nombre_titular_cuenta')
        assert cleaned_nombre == 'JUAN PÉREZ GONZÁLEZ', f"El nombre debe normalizarse a mayúsculas. Se esperaba 'JUAN PÉREZ GONZÁLEZ' pero se obtuvo '{cleaned_nombre}'"

    def test_nombre_titular_cuenta_invalido_muy_corto(self):
        """Test que verifica que se rechaza un nombre muy corto"""
        form_data = {
            'banco': 'Banco Nacional',
            'numero_cuenta': '1234567890',
            'nombre_titular_cuenta': 'Jo',  # Solo 2 caracteres
            'tipo_cuenta': 'corriente'
        }
        form = CuentaBancariaForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debe ser válido con nombre muy corto"
        assert 'nombre_titular_cuenta' in form.errors, "Debe haber error en el campo nombre_titular_cuenta"
        assert 'debe tener al menos 3 caracteres' in str(form.errors['nombre_titular_cuenta']), "El mensaje debe mencionar los 3 caracteres mínimos"

    def test_banco_valido_normalizado(self):
        """Test que verifica que el nombre del banco se normaliza con Title Case"""
        form_data = {
            'banco': 'banco nacional de fomento',  # En minúsculas
            'numero_cuenta': '1234567890',
            'nombre_titular_cuenta': 'Juan Pérez',
            'tipo_cuenta': 'corriente'
        }
        form = CuentaBancariaForm(data=form_data)
        form.is_valid()
        
        cleaned_banco = form.cleaned_data.get('banco')
        assert cleaned_banco == 'Banco Nacional De Fomento', f"El banco debe normalizarse con Title Case. Se esperaba 'Banco Nacional De Fomento' pero se obtuvo '{cleaned_banco}'"

    def test_banco_invalido_muy_corto(self):
        """Test que verifica que se rechaza un nombre de banco muy corto"""
        form_data = {
            'banco': 'BN',  # Solo 2 caracteres
            'numero_cuenta': '1234567890',
            'nombre_titular_cuenta': 'Juan Pérez',
            'tipo_cuenta': 'corriente'
        }
        form = CuentaBancariaForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debe ser válido con nombre de banco muy corto"
        assert 'banco' in form.errors, "Debe haber error en el campo banco"
        assert 'debe tener al menos 3 caracteres' in str(form.errors['banco']), "El mensaje debe mencionar los 3 caracteres mínimos"

    def test_tipo_cuenta_valido_corriente(self):
        """Test que verifica que se acepta 'corriente' como tipo de cuenta válido"""
        form_data = {
            'banco': 'Banco Nacional',
            'numero_cuenta': '1234567890',
            'nombre_titular_cuenta': 'Juan Pérez',
            'tipo_cuenta': 'corriente'
        }
        form = CuentaBancariaForm(data=form_data)
        
        assert form.is_valid(), f"El formulario debe ser válido con tipo_cuenta 'corriente'. Errores: {form.errors}"

    def test_tipo_cuenta_valido_ahorro(self):
        """Test que verifica que se acepta 'ahorro' como tipo de cuenta válido"""
        form_data = {
            'banco': 'Banco Nacional',
            'numero_cuenta': '1234567890',
            'nombre_titular_cuenta': 'Juan Pérez',
            'tipo_cuenta': 'ahorro'
        }
        form = CuentaBancariaForm(data=form_data)
        
        assert form.is_valid(), f"El formulario debe ser válido con tipo_cuenta 'ahorro'. Errores: {form.errors}"

    def test_tipo_cuenta_valido_otro(self):
        """Test que verifica que se acepta 'otro' como tipo de cuenta válido"""
        form_data = {
            'banco': 'Banco Nacional',
            'numero_cuenta': '1234567890',
            'nombre_titular_cuenta': 'Juan Pérez',
            'tipo_cuenta': 'otro'
        }
        form = CuentaBancariaForm(data=form_data)
        
        assert form.is_valid(), f"El formulario debe ser válido con tipo_cuenta 'otro'. Errores: {form.errors}"

    def test_formulario_invalido_campo_requerido_faltante(self):
        """Test que verifica que el formulario es inválido cuando falta un campo requerido"""
        form_data = {
            'banco': 'Banco Nacional',
            # Falta el numero_cuenta
            'nombre_titular_cuenta': 'Juan Pérez',
            'tipo_cuenta': 'corriente'
        }
        form = CuentaBancariaForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debe ser válido cuando falta un campo requerido"
        assert 'numero_cuenta' in form.errors, "Debe haber error en el campo numero_cuenta faltante"

    def test_formulario_vacio_es_invalido(self):
        """Test que verifica que un formulario vacío es inválido"""
        form = CuentaBancariaForm(data={})
        
        assert not form.is_valid(), "El formulario vacío no debe ser válido"
        required_fields = ['banco', 'numero_cuenta', 'nombre_titular_cuenta', 'tipo_cuenta']
        
        for field in required_fields:
            assert field in form.errors, f"Debe haber error en el campo requerido '{field}'"