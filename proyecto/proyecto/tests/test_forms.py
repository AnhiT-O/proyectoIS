import pytest
from django.test import TestCase
from django.forms import ValidationError
from django.contrib.auth import get_user_model
from decimal import Decimal

from proyecto.forms import LoginForm, SimuladorForm
from monedas.models import Moneda
from clientes.models import Cliente

User = get_user_model()


@pytest.mark.django_db
class TestLoginForm:
    """Pruebas unitarias para el formulario LoginForm"""
    
    def test_login_exitoso_con_credenciales_correctas(self):
        """
        Prueba 1: Validar login exitoso con usuario y contraseña correctos
        """
        # Crear usuario de prueba
        user = User(
            username='testuser',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            bloqueado=False,
            is_active=True
        )
        user.set_password('testpassword')
        user.save()
        
        # Crear formulario con credenciales correctas
        form_data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        form = LoginForm(data=form_data)
        
        # Verificar que el formulario es válido
        assert form.is_valid(), f"Formulario debería ser válido, errores: {form.errors}"
        
        # Verificar que el usuario autenticado es el correcto
        user_authenticated = form.get_user()
        assert user_authenticated == user
        assert user_authenticated.username == 'testuser'

    def test_login_rechaza_usuario_bloqueado(self):
        """
        Prueba 2: Rechazar login si el usuario está bloqueado (campo bloqueado=True)
        """
        # Crear usuario bloqueado
        user = User(
            username='blockeduser',
            first_name='Blocked',
            last_name='User',
            email='blocked@example.com',
            tipo_cedula='CI',
            cedula_identidad='87654321',
            bloqueado=True,  # Usuario bloqueado
            is_active=True
        )
        user.set_password('testpassword')
        user.save()
        
        # Intentar login con usuario bloqueado
        form_data = {
            'username': 'blockeduser',
            'password': 'testpassword'
        }
        form = LoginForm(data=form_data)
        
        # Verificar que el formulario no es válido
        assert not form.is_valid()
        
        # Verificar que hay errores no relacionados con campos específicos
        assert form.non_field_errors()

    def test_mensaje_error_personalizado_usuario_bloqueado(self):
        """
        Prueba 3: Mostrar mensaje de error personalizado si el usuario está bloqueado
        """
        # Crear usuario bloqueado
        user = User(
            username='blockeduser2',
            first_name='Blocked',
            last_name='User2',
            email='blocked2@example.com',
            tipo_cedula='CI',
            cedula_identidad='11223344',
            bloqueado=True,
            is_active=True
        )
        user.set_password('testpassword')
        user.save()
        
        # Intentar login
        form_data = {
            'username': 'blockeduser2',
            'password': 'testpassword'
        }
        form = LoginForm(data=form_data)
        
        # Verificar que el formulario no es válido
        assert not form.is_valid()
        
        # Verificar mensaje de error específico para usuario bloqueado
        error_message = "Esta cuenta está bloqueada. Por favor contacta con el administrador."
        assert error_message in str(form.non_field_errors())

    def test_mensaje_error_personalizado_credenciales_incorrectas(self):
        """
        Prueba 4: Mostrar mensaje de error personalizado si usuario/contraseña no coinciden
        """
        # Crear usuario válido
        user = User(
            username='validuser',
            first_name='Valid',
            last_name='User',
            email='valid@example.com',
            tipo_cedula='CI',
            cedula_identidad='55667788',
            bloqueado=False,
            is_active=True
        )
        user.set_password('correctpassword')
        user.save()
        
        # Intentar login con contraseña incorrecta
        form_data = {
            'username': 'validuser',
            'password': 'wrongpassword'
        }
        form = LoginForm(data=form_data)
        
        # Verificar que el formulario no es válido
        assert not form.is_valid()
        
        # Verificar mensaje de error personalizado para credenciales incorrectas
        error_message = "El nombre de usuario y contraseña no coinciden. Inténtelo de nuevo."
        assert error_message in str(form.non_field_errors())


@pytest.mark.django_db
class TestSimuladorForm:
    """Pruebas unitarias para el formulario SimuladorForm"""
    
    def setup_method(self):
        """Configurar datos de prueba"""
        # Crear moneda de prueba
        self.moneda = Moneda.objects.create(
            nombre='Test Dollar',
            simbolo='TSD',
            activa=True,
            tasa_base=7000,
            comision_compra=200,
            comision_venta=250,
            decimales=2
        )
        
        # Crear cliente de prueba
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test',
            tipoDocCliente='CI',
            docCliente='12345678',
            correoElecCliente='cliente@test.com',
            telefono='099123456',
            tipoCliente='F',
            direccion='Dirección Test',
            ocupacion='Empleado',
            segmento='minorista'
        )
    
    def test_formulario_valido_operacion_compra(self):
        """
        Prueba: Validar formulario correcto para operación de compra
        """
        form_data = {
            'moneda': self.moneda.id,
            'monto': '10.50',  # Moneda extranjera
            'operacion': 'compra'
        }
        form = SimuladorForm(data=form_data)
        
        assert form.is_valid(), f"Formulario debería ser válido, errores: {form.errors}"
        assert form.cleaned_data['moneda'] == self.moneda
        assert form.cleaned_data['monto'] == Decimal('10.50')
        assert form.cleaned_data['operacion'] == 'compra'
    
    def test_formulario_valido_operacion_venta(self):
        """
        Prueba: Validar formulario correcto para operación de venta
        """
        form_data = {
            'moneda': self.moneda.id,
            'monto': '15.75',  # Moneda extranjera
            'operacion': 'venta'
        }
        form = SimuladorForm(data=form_data)
        
        assert form.is_valid(), f"Formulario debería ser válido, errores: {form.errors}"
        assert form.cleaned_data['moneda'] == self.moneda
        assert form.cleaned_data['monto'] == Decimal('15.75')
        assert form.cleaned_data['operacion'] == 'venta'
    
    def test_validacion_moneda_requerida(self):
        """
        Prueba: Validar que la moneda es requerida
        """
        form_data = {
            'monto': '100',
            'operacion': 'compra'
        }
        form = SimuladorForm(data=form_data)
        
        assert not form.is_valid()
        assert 'moneda' in form.errors
        assert 'Debes seleccionar una moneda.' in form.errors['moneda']
    
    def test_validacion_monto_requerido(self):
        """
        Prueba: Validar que el monto es requerido
        """
        form_data = {
            'moneda': self.moneda.id,
            'operacion': 'compra'
        }
        form = SimuladorForm(data=form_data)
        
        assert not form.is_valid()
        assert 'monto' in form.errors
        assert 'Debes ingresar un monto numérico.' in form.errors['monto']
    
    def test_validacion_monto_mayor_cero(self):
        """
        Prueba: Validar que el monto debe ser mayor a 0
        """
        form_data = {
            'moneda': self.moneda.id,
            'monto': '0',
            'operacion': 'compra'
        }
        form = SimuladorForm(data=form_data)
        
        assert not form.is_valid()
        assert 'monto' in form.errors
        assert 'El monto debe ser mayor a 0.' in form.errors['monto']
    
    def test_validacion_monto_minimo_compra(self):
        """
        Prueba: Validar monto mínimo para operación de compra según decimales de moneda
        """
        # Crear moneda con 4 decimales
        moneda_4dec = Moneda.objects.create(
            nombre='High Precision Coin',
            simbolo='HPC',
            activa=True,
            tasa_base=1000,
            comision_compra=10,
            comision_venta=15,
            decimales=4
        )
        
        # Monto menor al mínimo permitido (0.0001)
        form_data = {
            'moneda': moneda_4dec.id,
            'monto': '0.00005',
            'operacion': 'compra'
        }
        form = SimuladorForm(data=form_data)
        
        assert not form.is_valid()
        assert 'monto' in form.errors
        assert 'El monto mínimo para compra es 0.0001 HPC.' in form.errors['monto']
    
    def test_validacion_venta_monto_minimo(self):
        """
        Prueba: Validar monto mínimo para venta según decimales de moneda
        """
        # Crear moneda con 4 decimales
        moneda_4dec = Moneda.objects.create(
            nombre='High Precision Coin',
            simbolo='HPC',
            activa=True,
            tasa_base=1000,
            comision_compra=10,
            comision_venta=15,
            decimales=4
        )
        
        # Monto menor al mínimo permitido (0.0001)
        form_data = {
            'moneda': moneda_4dec.id,
            'monto': '0.00005',
            'operacion': 'venta'
        }
        form = SimuladorForm(data=form_data)
        
        assert not form.is_valid()
        assert 'monto' in form.errors
        assert 'El monto mínimo para venta es 0.0001 HPC.' in form.errors['monto']
    
    def test_conversion_compra_sin_cliente(self):
        """
        Prueba: Realizar conversión de compra sin cliente (precios base)
        """
        form_data = {
            'moneda': self.moneda.id,
            'monto': '2.00',
            'operacion': 'compra'
        }
        form = SimuladorForm(data=form_data)
        
        assert form.is_valid()
        
        resultado = form.realizar_conversion()
        
        assert resultado['success']
        assert resultado['tipo_resultado'] == 'guaranies'
        
        # Verificar cálculo: 2.00 * precio_venta
        precio_venta = self.moneda.calcular_precio_venta(0)
        resultado_esperado = int(Decimal('2.00') * precio_venta)
        assert resultado['resultado_numerico'] == resultado_esperado
    
    def test_conversion_venta_sin_cliente(self):
        """
        Prueba: Realizar conversión de venta sin cliente (precios base)
        """
        form_data = {
            'moneda': self.moneda.id,
            'monto': '2.50',  # Moneda extranjera
            'operacion': 'venta'
        }
        form = SimuladorForm(data=form_data)
        
        assert form.is_valid()
        
        resultado = form.realizar_conversion()
        
        assert resultado['success']
        assert resultado['tipo_resultado'] == 'guaranies'
        
        # Verificar cálculo: 2.50 * precio_compra
        precio_compra = self.moneda.calcular_precio_compra(0)
        resultado_esperado = int(Decimal('2.50') * precio_compra)
        assert resultado['resultado_numerico'] == resultado_esperado
    
    def test_conversion_con_cliente(self):
        """
        Prueba: Realizar conversión con cliente (precios segmentados)
        """
        form_data = {
            'moneda': self.moneda.id,
            'monto': '1.00',
            'operacion': 'compra'
        }
        form = SimuladorForm(data=form_data, cliente=self.cliente)
        
        assert form.is_valid()
        
        resultado = form.realizar_conversion()
        
        assert resultado['success']
        assert resultado['tipo_resultado'] == 'guaranies'
        
        # Verificar que se usan precios del cliente
        # (esto depende de la implementación de get_precios_cliente)
    
    def test_error_realizar_conversion_formulario_invalido(self):
        """
        Prueba: Error al realizar conversión con formulario inválido
        """
        form_data = {
            'moneda': self.moneda.id,
            'monto': '-100',  # Monto inválido
            'operacion': 'compra'
        }
        form = SimuladorForm(data=form_data)
        
        assert not form.is_valid()
        
        with pytest.raises(ValueError, match="El formulario no es válido"):
            form.realizar_conversion()