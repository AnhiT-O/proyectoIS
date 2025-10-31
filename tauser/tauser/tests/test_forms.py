"""
Tests para los formularios del sistema TAUser.

Pruebas unitarias para validar el correcto funcionamiento de los formularios
utilizados en las terminales autónomas de usuario (TAUser).
"""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from tauser.forms import TokenForm, IngresoForm, Token2FAForm
from django.forms import ValidationError


class TestTokenForm:
    """Tests para el formulario TokenForm."""
    
    def test_token_valido_con_8_caracteres_alfanumericos(self):
        """Prueba que acepta tokens válidos de 8 caracteres alfanuméricos."""
        form_data = {'codigo': 'ABC12345'}
        form = TokenForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data['codigo'] == 'ABC12345'
    
    def test_token_invalido_menos_8_caracteres(self):
        """Prueba que rechaza tokens con menos de 8 caracteres."""
        form_data = {'codigo': 'ABC123'}
        form = TokenForm(data=form_data)
        assert not form.is_valid()
        assert 'El código debe ser alfanumérico y tener exactamente 8 caracteres.' in form.errors['codigo']
    
    def test_token_invalido_mas_8_caracteres(self):
        """Prueba que rechaza tokens con más de 8 caracteres."""
        form_data = {'codigo': 'ABC123456'}
        form = TokenForm(data=form_data)
        assert not form.is_valid()
        assert 'El código debe ser alfanumérico y tener exactamente 8 caracteres.' in form.errors['codigo']
    
    def test_token_invalido_con_caracteres_especiales(self):
        """Prueba que rechaza tokens con caracteres especiales."""
        form_data = {'codigo': 'ABC123@#'}
        form = TokenForm(data=form_data)
        assert not form.is_valid()
        assert 'El código debe ser alfanumérico y tener exactamente 8 caracteres.' in form.errors['codigo']
    
    def test_token_invalido_con_espacios(self):
        """Prueba que rechaza tokens con espacios."""
        form_data = {'codigo': 'ABC 1234'}
        form = TokenForm(data=form_data)
        assert not form.is_valid()
        assert 'El código debe ser alfanumérico y tener exactamente 8 caracteres.' in form.errors['codigo']
    
    def test_token_vacio_requerido(self):
        """Prueba que el campo código es requerido."""
        form_data = {'codigo': ''}
        form = TokenForm(data=form_data)
        assert not form.is_valid()
        assert 'Debes ingresar el código de transacción.' in form.errors['codigo']


class TestIngresoForm:
    """Tests para el formulario IngresoForm."""
    
    def test_archivo_txt_valido(self):
        """Prueba que acepta archivos .txt válidos."""
        contenido = "Ingreso\nGuaraní\t50000\t10\nDólar\t100\t5"
        archivo = SimpleUploadedFile(
            "billetes.txt",
            contenido.encode('utf-8'),
            content_type="text/plain"
        )
        form = IngresoForm(files={'archivo': archivo})
        assert form.is_valid()
    
    def test_archivo_extension_incorrecta(self):
        """Prueba que rechaza archivos que no son .txt."""
        contenido = "Ingreso\nGuaraní\t50000\t10"
        archivo = SimpleUploadedFile(
            "billetes.csv",
            contenido.encode('utf-8'),
            content_type="text/csv"
        )
        form = IngresoForm(files={'archivo': archivo})
        assert not form.is_valid()
        assert 'El archivo debe tener extensión .txt.' in form.errors['archivo']
    
    def test_archivo_muy_grande(self):
        """Prueba que rechaza archivos mayores a 5MB."""
        contenido = "A" * (6 * 1024 * 1024)  # 6MB
        archivo = SimpleUploadedFile(
            "billetes.txt",
            contenido.encode('utf-8'),
            content_type="text/plain"
        )
        form = IngresoForm(files={'archivo': archivo})
        assert not form.is_valid()
        assert 'El archivo no debe superar los 5MB.' in form.errors['archivo']
    
    def test_archivo_codificacion_invalida(self):
        """Prueba que rechaza archivos con codificación inválida."""
        contenido = b'\xff\xfe\x41\x00'  # Contenido inválido en UTF-8
        archivo = SimpleUploadedFile(
            "billetes.txt",
            contenido,
            content_type="text/plain"
        )
        form = IngresoForm(files={'archivo': archivo})
        assert not form.is_valid()
        assert 'El archivo debe contener texto válido en UTF-8.' in form.errors['archivo']
    
    def test_archivo_requerido(self):
        """Prueba que el archivo es requerido."""
        form = IngresoForm(files={})
        assert not form.is_valid()
        assert 'Debes seleccionar un archivo .txt.' in form.errors['archivo']


class TestToken2FAForm:
    """Tests para el formulario Token2FAForm."""
    
    def test_codigo_2fa_valido(self):
        """Prueba que acepta códigos 2FA válidos de 6 dígitos."""
        form_data = {'codigo_2fa': '123456'}
        form = Token2FAForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data['codigo_2fa'] == '123456'
    
    def test_codigo_2fa_invalido_menos_6_digitos(self):
        """Prueba que rechaza códigos con menos de 6 dígitos."""
        form_data = {'codigo_2fa': '12345'}
        form = Token2FAForm(data=form_data)
        assert not form.is_valid()
        assert 'El código debe contener exactamente 6 dígitos numéricos.' in form.errors['codigo_2fa']
    
    def test_codigo_2fa_invalido_mas_6_digitos(self):
        """Prueba que rechaza códigos con más de 6 dígitos."""
        form_data = {'codigo_2fa': '1234567'}
        form = Token2FAForm(data=form_data)
        assert not form.is_valid()
        assert 'El código debe contener exactamente 6 dígitos numéricos.' in form.errors['codigo_2fa']
    
    def test_codigo_2fa_invalido_con_letras(self):
        """Prueba que rechaza códigos con letras."""
        form_data = {'codigo_2fa': '12345A'}
        form = Token2FAForm(data=form_data)
        assert not form.is_valid()
        assert 'El código debe contener exactamente 6 dígitos numéricos.' in form.errors['codigo_2fa']
    
    def test_codigo_2fa_invalido_con_caracteres_especiales(self):
        """Prueba que rechaza códigos con caracteres especiales."""
        form_data = {'codigo_2fa': '12345@'}
        form = Token2FAForm(data=form_data)
        assert not form.is_valid()
        assert 'El código debe contener exactamente 6 dígitos numéricos.' in form.errors['codigo_2fa']
    
    def test_codigo_2fa_vacio_requerido(self):
        """Prueba que el código 2FA es requerido."""
        form_data = {'codigo_2fa': ''}
        form = Token2FAForm(data=form_data)
        assert not form.is_valid()
        assert 'Debes ingresar el código de verificación 2FA.' in form.errors['codigo_2fa']