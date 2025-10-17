"""
Pruebas unitarias sencillas para los modelos de la aplicación de clientes.
"""

import pytest
from django.core.exceptions import ValidationError

from clientes.models import Cliente


@pytest.mark.django_db
class TestClienteModel:
    """Pruebas unitarias sencillas para el modelo Cliente"""
    
    def test_crear_cliente_valido(self):
        """
        Prueba 1: Crear un cliente con datos válidos
        """
        cliente = Cliente.objects.create(
            nombre='Juan Pérez',
            tipo='F',
            tipo_documento='CI',
            numero_documento='12345678',
            correo_electronico='juan@test.com',
            telefono='0991234567',
            direccion='Dirección test',
            ocupacion='Empleado',
            segmento='minorista'
        )
        
        assert cliente.nombre == 'Juan Pérez'
        assert cliente.tipo == 'F'
        assert cliente.segmento == 'minorista'


    def test_metodo_str_retorna_nombre(self):
        """
        Prueba 4: El método __str__ debe retornar el nombre del cliente
        """
        cliente = Cliente(nombre='María González')
        assert str(cliente) == 'María González'

    def test_tiene_tarjetas_activas_sin_stripe_id(self):
        """
        Prueba 5: Cliente sin ID de Stripe no tiene tarjetas activas
        """
        cliente = Cliente.objects.create(
            nombre='Cliente Sin Stripe',
            tipo='F',
            tipo_documento='CI',
            numero_documento='55555555',
            correo_electronico='sinstripe@test.com',
            telefono='0995555555',
            direccion='Dirección',
            ocupacion='Empleado',
            segmento='minorista'
        )
        
        assert cliente.tiene_tarjetas_activas() == False