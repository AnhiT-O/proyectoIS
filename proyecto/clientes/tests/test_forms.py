"""
Pruebas unitarias sencillas para los formularios de la aplicación de clientes.
"""

import pytest
from clientes.forms import ClienteForm, AgregarTarjetaForm
from clientes.models import Cliente


@pytest.mark.django_db
class TestClienteForm:
    """Pruebas unitarias sencillas para el formulario ClienteForm"""
    
    def test_formulario_valido_con_datos_correctos(self):
        """
        Prueba 1: Formulario válido con todos los datos correctos
        """
        form_data = {
            'nombre': 'Juan Pérez',
            'tipo_documento': 'CI',
            'numero_documento': '12345678',
            'correo_electronico': 'juan@test.com',
            'telefono': '0991234567',
            'tipo': 'F',
            'direccion': 'Dirección test',
            'ocupacion': 'Empleado',
            'segmento': 'minorista'
        }
        
        form = ClienteForm(data=form_data)
        assert form.is_valid(), f"Formulario debería ser válido, errores: {form.errors}"

    def test_formulario_invalido_telefono_no_numerico(self):
        """
        Prueba 2: Formulario inválido con teléfono no numérico
        """
        form_data = {
            'nombre': 'Juan Pérez',
            'tipo_documento': 'CI',
            'numero_documento': '12345678',
            'correo_electronico': 'juan@test.com',
            'telefono': '099-123-4567',  # Contiene guiones
            'tipo': 'F',
            'direccion': 'Dirección test',
            'ocupacion': 'Empleado',
            'segmento': 'minorista'
        }
        
        form = ClienteForm(data=form_data)
        assert not form.is_valid()
        assert 'telefono' in form.errors

    def test_formulario_invalido_documento_no_numerico(self):
        """
        Prueba 3: Formulario inválido con documento no numérico
        """
        form_data = {
            'nombre': 'María González',
            'tipo_documento': 'CI',
            'numero_documento': '1234-5678',  # Contiene guión
            'correo_electronico': 'maria@test.com',
            'telefono': '0981234567',
            'tipo': 'F',
            'direccion': 'Dirección test',
            'ocupacion': 'Empleada',
            'segmento': 'minorista'
        }
        
        form = ClienteForm(data=form_data)
        assert not form.is_valid()
        assert 'numero_documento' in form.errors

    def test_formulario_invalido_campos_requeridos_vacios(self):
        """
        Prueba 4: Formulario inválido con campos requeridos vacíos
        """
        form_data = {
            'nombre': '',  # Campo requerido vacío
            'tipo_documento': '',  # Campo requerido vacío
            'numero_documento': '',  # Campo requerido vacío
            'correo_electronico': '',  # Campo requerido vacío
            'telefono': '',  # Campo requerido vacío
            'tipo': '',  # Campo requerido vacío
            'direccion': '',  # Campo requerido vacío
            'ocupacion': '',  # Campo requerido vacío
            'segmento': 'minorista'
        }
        
        form = ClienteForm(data=form_data)
        assert not form.is_valid()
        
        # Verificar que hay errores en los campos principales
        assert 'nombre' in form.errors
        assert 'numero_documento' in form.errors
        assert 'correo_electronico' in form.errors

    def test_crear_cliente_desde_formulario_valido(self):
        """
        Prueba 5: Crear cliente desde formulario válido
        """
        form_data = {
            'nombre': 'Cliente Test',
            'tipo_documento': 'CI',
            'numero_documento': '87654321',
            'correo_electronico': 'cliente@test.com',
            'telefono': '0987654321',
            'tipo': 'F',
            'direccion': 'Dirección test',
            'ocupacion': 'Empleado',
            'segmento': 'vip',
            'declaracion_jurada': True
        }
        
        form = ClienteForm(data=form_data)
        assert form.is_valid()
        
        cliente = form.save()
        assert cliente.nombre == 'Cliente Test'
        assert cliente.segmento == 'vip'


@pytest.mark.django_db
class TestAgregarTarjetaForm:
    """Pruebas unitarias sencillas para el formulario AgregarTarjetaForm"""
    
    def setup_method(self):
        """Configurar datos de prueba"""
        self.cliente = Cliente.objects.create(
            nombre='Cliente Tarjeta',
            tipo_documento='CI',
            numero_documento='66666666',
            correo_electronico='tarjeta@test.com',
            telefono='0996666666',
            tipo='F',
            direccion='Dirección tarjeta',
            ocupacion='Empleado',
            segmento='minorista'
        )
    
    def test_formulario_invalido_sin_token(self):
        """
        Prueba 1: Formulario inválido sin token de Stripe
        """
        form_data = {}
        form = AgregarTarjetaForm(data=form_data, cliente=self.cliente)
        
        assert not form.is_valid()
        assert 'stripe_token' in form.errors

    def test_formulario_valido_con_token(self):
        """
        Prueba 2: Formulario válido con token de Stripe
        """
        form_data = {'stripe_token': 'tok_test_1234567890'}
        form = AgregarTarjetaForm(data=form_data, cliente=self.cliente)
        
        assert form.is_valid(), f"Formulario debería ser válido, errores: {form.errors}"