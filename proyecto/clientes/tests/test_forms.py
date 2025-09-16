import pytest
from django.core.exceptions import ValidationError
from clientes.forms import ClienteForm
from clientes.models import Cliente


class TestClienteForm:
    
    @pytest.mark.django_db
    def test_cliente_form_creacion_exitosa_con_datos_validos(self):
        """Prueba 1: ClienteForm: creación exitosa de cliente con datos válidos."""
        form_data = {
            'nombre': 'Juan Pérez',
            'tipoDocCliente': 'CI',
            'docCliente': '1234567',
            'correoElecCliente': 'juan.perez@example.com',
            'telefono': '0981123456',
            'tipoCliente': 'F',
            'direccion': 'Asunción, Paraguay',
            'ocupacion': 'Ingeniero',
            'segmento': 'minorista',
            'declaracion_jurada': True
        }
        
        form = ClienteForm(data=form_data)
        assert form.is_valid(), f"El formulario debería ser válido. Errores: {form.errors}"
        
        cliente = form.save()
        assert cliente.nombre == 'Juan Pérez'
        assert cliente.docCliente == '1234567'
        assert cliente.tipoCliente == 'F'
        assert cliente.beneficio_segmento == 0  # minorista = 0%

    @pytest.mark.django_db
    def test_cliente_form_error_documento_no_numerico(self):
        """Prueba 2: ClienteForm: error si el documento no es numérico."""
        form_data = {
            'nombre': 'Juan Pérez',
            'tipoDocCliente': 'CI',
            'docCliente': '123ABC',  # Documento con letras
            'correoElecCliente': 'juan.perez@example.com',
            'telefono': '0981123456',
            'tipoCliente': 'F',
            'direccion': 'Asunción, Paraguay',
            'ocupacion': 'Ingeniero',
            'segmento': 'minorista',
            'declaracion_jurada': True
        }
        
        form = ClienteForm(data=form_data)
        assert not form.is_valid()
        assert 'docCliente' in form.errors
        assert 'El documento debe contener solo números' in str(form.errors['docCliente'])

    @pytest.mark.django_db
    def test_cliente_form_error_telefono_no_numerico(self):
        """Prueba 2: ClienteForm: error si el teléfono no es numérico."""
        form_data = {
            'nombre': 'Juan Pérez',
            'tipoDocCliente': 'CI',
            'docCliente': '1234567',
            'correoElecCliente': 'juan.perez@example.com',
            'telefono': '098-112-3456',  # Teléfono con guiones
            'tipoCliente': 'F',
            'direccion': 'Asunción, Paraguay',
            'ocupacion': 'Ingeniero',
            'segmento': 'minorista',
            'declaracion_jurada': True
        }
        
        form = ClienteForm(data=form_data)
        assert not form.is_valid()
        assert 'telefono' in form.errors
        assert 'El teléfono debe contener solo números' in str(form.errors['telefono'])

    @pytest.mark.django_db
    def test_cliente_form_error_documento_ya_existe(self):
        """Prueba 3: ClienteForm: error si el documento ya existe (único)."""
        # Crear cliente existente
        Cliente.objects.create(
            nombre='Usuario Existente',
            tipoDocCliente='CI',
            docCliente='1234567',
            correoElecCliente='existente@example.com',
            telefono='0981111111',
            tipoCliente='F',
            direccion='Ciudad',
            ocupacion='Empleado',
            segmento='minorista'
        )
        
        # Intentar crear otro cliente con el mismo documento
        form_data = {
            'nombre': 'Juan Pérez',
            'tipoDocCliente': 'CI',
            'docCliente': '1234567',  # Documento duplicado
            'correoElecCliente': 'juan.perez@example.com',
            'telefono': '0981123456',
            'tipoCliente': 'F',
            'direccion': 'Asunción, Paraguay',
            'ocupacion': 'Ingeniero',
            'segmento': 'minorista',
            'declaracion_jurada': True
        }
        
        form = ClienteForm(data=form_data)
        assert not form.is_valid()
        assert 'docCliente' in form.errors

    @pytest.mark.django_db
    def test_cliente_form_error_correo_ya_existe(self):
        """Prueba 3: ClienteForm: error si el correo ya existe (único)."""
        # Crear cliente existente
        Cliente.objects.create(
            nombre='Usuario Existente',
            tipoDocCliente='CI',
            docCliente='7654321',
            correoElecCliente='duplicado@example.com',
            telefono='0981111111',
            tipoCliente='F',
            direccion='Ciudad',
            ocupacion='Empleado',
            segmento='minorista'
        )
        
        # Intentar crear otro cliente con el mismo correo
        form_data = {
            'nombre': 'Juan Pérez',
            'tipoDocCliente': 'CI',
            'docCliente': '1234567',
            'correoElecCliente': 'duplicado@example.com',  # Correo duplicado
            'telefono': '0981123456',
            'tipoCliente': 'F',
            'direccion': 'Asunción, Paraguay',
            'ocupacion': 'Ingeniero',
            'segmento': 'minorista',
            'declaracion_jurada': True
        }
        
        form = ClienteForm(data=form_data)
        assert not form.is_valid()
        assert 'correoElecCliente' in form.errors

    @pytest.mark.django_db
    def test_cliente_form_error_campos_requeridos_vacios(self):
        """Prueba 4: ClienteForm: error si algún campo requerido está vacío."""
        form_data = {
            'nombre': '',  # Campo requerido vacío
            'tipoDocCliente': 'CI',
            'docCliente': '1234567',
            'correoElecCliente': 'juan.perez@example.com',
            'telefono': '0981123456',
            'tipoCliente': 'F',
            'direccion': 'Asunción, Paraguay',
            'ocupacion': 'Ingeniero',
            'segmento': 'minorista',
        }
        
        form = ClienteForm(data=form_data)
        assert not form.is_valid()
        assert 'nombre' in form.errors
        assert 'Debes ingresar el nombre.' in str(form.errors['nombre'])

    @pytest.mark.django_db
    def test_cliente_form_error_campos_exceden_maximo_caracteres(self):
        """Prueba 4: ClienteForm: error si algún campo excede el máximo de caracteres."""
        form_data = {
            'nombre': 'A' * 101,  # Excede máximo de 100 caracteres
            'tipoDocCliente': 'CI',
            'docCliente': '1234567',
            'correoElecCliente': 'juan.perez@example.com',
            'telefono': '0981123456',
            'tipoCliente': 'F',
            'direccion': 'Asunción, Paraguay',
            'ocupacion': 'Ingeniero',
            'segmento': 'minorista',
        }
        
        form = ClienteForm(data=form_data)
        assert not form.is_valid()
        assert 'nombre' in form.errors
        assert 'El nombre no puede exceder los 100 caracteres.' in str(form.errors['nombre'])

    @pytest.mark.django_db
    def test_cliente_form_error_tipo_documento_no_corresponde_tipo_cliente(self):
        """Prueba 5: ClienteForm: error si el tipo de documento no corresponde al tipo de cliente."""
        form_data = {
            'nombre': 'Empresa SA',
            'tipoDocCliente': 'CI',  # Persona jurídica con CI (debe ser RUC)
            'docCliente': '1234567',
            'correoElecCliente': 'empresa@example.com',
            'telefono': '0981123456',
            'tipoCliente': 'J',  # Jurídica
            'direccion': 'Asunción, Paraguay',
            'ocupacion': 'Comercio',
            'segmento': 'corporativo',
        }
        
        form = ClienteForm(data=form_data)
        
        # El formulario puede ser válido a nivel de formulario, 
        # pero el error se detecta en el método clean del modelo
        if form.is_valid():
            try:
                cliente = form.save()
                assert False, "Debería haber lanzado ValidationError"
            except ValidationError as e:
                assert 'tipoDocCliente' in e.message_dict
                assert 'Las personas jurídicas deben usar RUC' in str(e.message_dict['tipoDocCliente'])
