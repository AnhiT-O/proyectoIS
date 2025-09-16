import pytest
from django.core.exceptions import ValidationError
from medios_pago.forms import TarjetaCreditoForm, CuentaBancariaForm


class TestTarjetaCreditoForm:
    """
    Pruebas unitarias para el formulario TarjetaCreditoForm
    """

    def test_tarjeta_credito_form_datos_validos(self):
        """
        1. TarjetaCreditoForm: valida correctamente una tarjeta con datos válidos.
        """
        form_data = {
            'numero_tarjeta': '1234567890123456',
            'cvv': '123',
            'nombre_titular_tarjeta': 'Juan Perez',
            'fecha_vencimiento_tc': '12/2027',
            'descripcion_tarjeta': 'Tarjeta personal',
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        assert form.is_valid()

    def test_tarjeta_credito_form_numero_tarjeta_no_16_digitos(self):
        """
        2. TarjetaCreditoForm: error si el número de tarjeta no tiene 16 dígitos o no es numérico.
        """
        # Caso: menos de 16 dígitos (Django mostrará mensaje de longitud mínima)
        form_data = {
            'numero_tarjeta': '123456789012345',  # 15 dígitos
            'cvv': '123',
            'nombre_titular_tarjeta': 'Juan Perez',
            'fecha_vencimiento_tc': '12/2027',
            'descripcion_tarjeta': 'Tarjeta personal',
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        assert not form.is_valid()
        assert 'numero_tarjeta' in form.errors
        # El mensaje puede ser de validación de longitud de Django o el personalizado
        error_msg = str(form.errors['numero_tarjeta'])
        assert ('mínimo 16 caracteres' in error_msg) or ('El número de tarjeta debe tener exactamente 16 dígitos' in error_msg)

        # Caso: más de 16 dígitos (Django mostrará mensaje de longitud máxima)
        form_data['numero_tarjeta'] = '12345678901234567'  # 17 dígitos
        form = TarjetaCreditoForm(data=form_data)
        assert not form.is_valid()
        assert 'numero_tarjeta' in form.errors

        # Caso: no numérico
        form_data['numero_tarjeta'] = '123456789012345a'  # contiene letra
        form = TarjetaCreditoForm(data=form_data)
        assert not form.is_valid()
        assert 'numero_tarjeta' in form.errors
        assert 'El número de tarjeta debe contener solo dígitos' in form.errors['numero_tarjeta']

    def test_tarjeta_credito_form_cvv_invalido(self):
        """
        3. TarjetaCreditoForm: error si el CVV no tiene 3 dígitos o no es numérico.
        """
        # Caso: menos de 3 dígitos (Django mostrará mensaje de longitud mínima)
        form_data = {
            'numero_tarjeta': '1234567890123456',
            'cvv': '12',  # 2 dígitos
            'nombre_titular_tarjeta': 'Juan Perez',
            'fecha_vencimiento_tc': '12/2027',
            'descripcion_tarjeta': 'Tarjeta personal',
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        assert not form.is_valid()
        assert 'cvv' in form.errors
        # El mensaje puede ser de validación de longitud de Django o el personalizado
        error_msg = str(form.errors['cvv'])
        assert ('mínimo 3 caracteres' in error_msg) or ('El CVV debe tener exactamente 3 dígitos' in error_msg)

        # Caso: más de 3 dígitos (Django mostrará mensaje de longitud máxima)
        form_data['cvv'] = '1234'  # 4 dígitos
        form = TarjetaCreditoForm(data=form_data)
        assert not form.is_valid()
        assert 'cvv' in form.errors

        # Caso: no numérico
        form_data['cvv'] = '12a'  # contiene letra
        form = TarjetaCreditoForm(data=form_data)
        assert not form.is_valid()
        assert 'cvv' in form.errors
        assert 'El CVV debe contener solo dígitos' in form.errors['cvv']

    def test_tarjeta_credito_form_nombre_titular_corto(self):
        """
        4. TarjetaCreditoForm: error si el nombre del titular tiene menos de 3 caracteres.
        """
        form_data = {
            'numero_tarjeta': '1234567890123456',
            'cvv': '123',
            'nombre_titular_tarjeta': 'AB',  # 2 caracteres
            'fecha_vencimiento_tc': '12/2027',
            'descripcion_tarjeta': 'Tarjeta personal',
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        assert not form.is_valid()
        assert 'nombre_titular_tarjeta' in form.errors
        assert 'El nombre debe tener al menos 3 caracteres' in form.errors['nombre_titular_tarjeta']

    def test_tarjeta_credito_form_fecha_vencimiento_formato_invalido(self):
        """
        5. TarjetaCreditoForm: error si la fecha de vencimiento no tiene formato MM/AAAA.
        """
        form_data = {
            'numero_tarjeta': '1234567890123456',
            'cvv': '123',
            'nombre_titular_tarjeta': 'Juan Perez',
            'fecha_vencimiento_tc': '12/27',  # formato MM/AA incorrecto
            'descripcion_tarjeta': 'Tarjeta personal',
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        assert not form.is_valid()
        assert 'fecha_vencimiento_tc' in form.errors
        # El mensaje puede ser de validación de longitud de Django o el personalizado
        error_msg = str(form.errors['fecha_vencimiento_tc'])
        assert ('mínimo 7 caracteres' in error_msg) or ('Ingrese la fecha en formato MM/AAAA' in error_msg)

        # Caso: mes inválido
        form_data['fecha_vencimiento_tc'] = '13/2027'  # mes 13 no existe
        form = TarjetaCreditoForm(data=form_data)
        assert not form.is_valid()
        assert 'fecha_vencimiento_tc' in form.errors

        # Caso: formato completamente incorrecto
        form_data['fecha_vencimiento_tc'] = '2027/12'  # formato incorrecto
        form = TarjetaCreditoForm(data=form_data)
        assert not form.is_valid()
        assert 'fecha_vencimiento_tc' in form.errors

    def test_tarjeta_credito_form_descripcion_corta(self):
        """
        6. TarjetaCreditoForm: error si la descripción tiene menos de 3 caracteres.
        """
        form_data = {
            'numero_tarjeta': '1234567890123456',
            'cvv': '123',
            'nombre_titular_tarjeta': 'Juan Perez',
            'fecha_vencimiento_tc': '12/2027',
            'descripcion_tarjeta': 'AB',  # 2 caracteres
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        assert not form.is_valid()
        assert 'descripcion_tarjeta' in form.errors
        assert 'La descripción debe tener al menos 3 caracteres' in form.errors['descripcion_tarjeta']

    def test_tarjeta_credito_form_moneda_valida(self):
        """
        7. TarjetaCreditoForm: valida correctamente la moneda de la tarjeta.
        """
        # Caso: moneda USD válida
        form_data = {
            'numero_tarjeta': '1234567890123456',
            'cvv': '123',
            'nombre_titular_tarjeta': 'Juan Perez',
            'fecha_vencimiento_tc': '12/2027',
            'descripcion_tarjeta': 'Tarjeta personal',
            'moneda_tc': 'USD'
        }
        form = TarjetaCreditoForm(data=form_data)
        assert form.is_valid()

        # Caso: moneda PYG válida
        form_data['moneda_tc'] = 'PYG'
        form = TarjetaCreditoForm(data=form_data)
        assert form.is_valid()


class TestCuentaBancariaForm:
    """
    Pruebas unitarias para el formulario CuentaBancariaForm
    """

    def test_cuenta_bancaria_form_datos_validos(self):
        """
        8. CuentaBancariaForm: valida correctamente una cuenta con datos válidos.
        """
        form_data = {
            'banco': 'Banco Nacional',
            'numero_cuenta': '123456789012',
            'nombre_titular_cuenta': 'Juan Perez',
            'tipo_cuenta': 'corriente'
        }
        form = CuentaBancariaForm(data=form_data)
        assert form.is_valid()

    def test_cuenta_bancaria_form_numero_cuenta_corto(self):
        """
        9. CuentaBancariaForm: error si el número de cuenta tiene menos de 6 caracteres.
        """
        form_data = {
            'banco': 'Banco Nacional',
            'numero_cuenta': '12345',  # 5 caracteres
            'nombre_titular_cuenta': 'Juan Perez',
            'tipo_cuenta': 'corriente'
        }
        form = CuentaBancariaForm(data=form_data)
        assert not form.is_valid()
        assert 'numero_cuenta' in form.errors
        assert 'El número de cuenta debe tener al menos 6 caracteres' in form.errors['numero_cuenta']

    def test_cuenta_bancaria_form_nombre_titular_corto(self):
        """
        10. CuentaBancariaForm: error si el nombre del titular tiene menos de 3 caracteres.
        """
        form_data = {
            'banco': 'Banco Nacional',
            'numero_cuenta': '123456789012',
            'nombre_titular_cuenta': 'AB',  # 2 caracteres
            'tipo_cuenta': 'corriente'
        }
        form = CuentaBancariaForm(data=form_data)
        assert not form.is_valid()
        assert 'nombre_titular_cuenta' in form.errors
        assert 'El nombre debe tener al menos 3 caracteres' in form.errors['nombre_titular_cuenta']

    def test_cuenta_bancaria_form_nombre_banco_corto(self):
        """
        11. CuentaBancariaForm: error si el nombre del banco tiene menos de 3 caracteres.
        """
        form_data = {
            'banco': 'AB',  # 2 caracteres
            'numero_cuenta': '123456789012',
            'nombre_titular_cuenta': 'Juan Perez',
            'tipo_cuenta': 'corriente'
        }
        form = CuentaBancariaForm(data=form_data)
        assert not form.is_valid()
        assert 'banco' in form.errors
        assert 'El nombre del banco debe tener al menos 3 caracteres' in form.errors['banco']
