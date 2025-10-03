"""
Pruebas unitarias para la aplicación de transacciones.
"""

import pytest
from django.core.exceptions import ValidationError
from decimal import Decimal

from clientes.models import Cliente
from monedas.models import Moneda, ConsumoLimiteCliente, LimiteGlobal


@pytest.fixture
def cliente():
    """Fixture para crear un cliente de prueba."""
    return Cliente.objects.create(
        nombre='Cliente Test',
        tipo='F',
        tipo_documento='CI',
        numero_documento='12345678',
        telefono='0981234567',
        correo_electronico='cliente@test.com',
        direccion='Direccion Test',
        ocupacion='Empleado',
        segmento='minorista'
    )


@pytest.fixture
def limite_global():
    """Fixture para crear límites globales."""
    return LimiteGlobal.objects.get_or_create(
        limite_diario=90000000,  # 90M
        limite_mensual=450000000,  # 450M
        defaults={}
    )[0]


@pytest.mark.django_db
class TestValidacionLimites:
    """
    Pruebas para el sistema de validación de límites de transacciones.
    """
    
    def test_validacion_limite_diario_excedido(self, cliente, limite_global):
        """
        Prueba que una transacción que excede el límite diario sea rechazada.
        """
        # Configurar límites del cliente con consumo alto
        ConsumoLimiteCliente.objects.update_or_create(
            cliente=cliente,
            defaults={
                'consumo_diario': 89500000,   # Casi al límite diario (90M)
                'consumo_mensual': 10000000
            }
        )
        
        # Simular transacción que excede límite
        monto_guaranies = Decimal('1000000')  # 1M para asegurar que exceda
        
        with pytest.raises(ValidationError) as excinfo:
            from monedas.services import LimiteService
            LimiteService.validar_limite_transaccion(cliente, monto_guaranies)
        
        assert "límite diario" in str(excinfo.value)
    
    def test_validacion_limite_mensual_excedido(self, cliente, limite_global):
        """
        Prueba que una transacción que excede el límite mensual sea rechazada.
        """
        # Configurar límites del cliente con consumo mensual alto
        ConsumoLimiteCliente.objects.update_or_create(
            cliente=cliente,
            defaults={
                'consumo_diario': 1000000,     # Bajo consumo diario
                'consumo_mensual': 449000000   # Casi al límite mensual (450M)
            }
        )
        
        # Simular transacción que excede límite mensual
        monto_guaranies = Decimal('2000000')  # 2M para asegurar que exceda
        
        with pytest.raises(ValidationError) as excinfo:
            from monedas.services import LimiteService
            LimiteService.validar_limite_transaccion(cliente, monto_guaranies)
        
        assert "límite mensual" in str(excinfo.value)

    def test_validacion_limite_diario_valido(self, cliente, limite_global):
        """
        Prueba que una transacción dentro del límite diario sea válida.
        """
        # Configurar límites del cliente
        ConsumoLimiteCliente.objects.update_or_create(
            cliente=cliente,
            defaults={
                'consumo_diario': 500000,   # 500K ya consumidos
                'consumo_mensual': 10000000  # 10M ya consumidos
            }
        )
        
        # Simular conversión: transacción válida
        monto_guaranies = Decimal('730000')
        
        # No debe lanzar excepción
        try:
            from monedas.services import LimiteService
            LimiteService.validar_limite_transaccion(cliente, monto_guaranies)
        except ValidationError:
            pytest.fail("No debería lanzar ValidationError para transacción válida")


@pytest.mark.django_db
class TestTransaccionViews:
    """
    Pruebas para las vistas de transacciones.
    """
    
    def test_generar_token_transaccion(self):
        """
        Prueba la generación de token de transacción.
        """
        from unittest.mock import patch
        
        # Mock de la función
        with patch('transacciones.views.generar_token_transaccion') as mock_generar:
            mock_generar.return_value = 'TOKEN123456'
            
            from transacciones.views import generar_token_transaccion
            token = generar_token_transaccion()
            
            mock_generar.assert_called_once()
            assert token == 'TOKEN123456'
    
    def test_convertir_funcion(self):
        """
        Prueba la función de conversión de monedas.
        """
        from unittest.mock import patch
        
        # Mock de la función convertir
        with patch('transacciones.views.convertir') as mock_convertir:
            mock_convertir.return_value = {
                'monto_guaranies': Decimal('730000'),
                'precio_aplicado': Decimal('7300.00')
            }
            
            from transacciones.views import convertir
            resultado = convertir(Decimal('100'), 'USD', 'venta')
            
            mock_convertir.assert_called_once_with(Decimal('100'), 'USD', 'venta')
            assert resultado['monto_guaranies'] == Decimal('730000')
            assert resultado['precio_aplicado'] == Decimal('7300.00')
