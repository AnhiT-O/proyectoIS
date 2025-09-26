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
            tipoCliente='F',
            tipoDocCliente='CI',
            docCliente='12345678',
            correoElecCliente='juan@test.com',
            telefono='0991234567',
            direccion='Dirección test',
            ocupacion='Empleado',
            segmento='minorista'
        )
        
        assert cliente.nombre == 'Juan Pérez'
        assert cliente.tipoCliente == 'F'
        assert cliente.segmento == 'minorista'
        assert cliente.beneficio_segmento == 0

    def test_beneficios_por_segmento(self):
        """
        Prueba 2: Verificar que los beneficios se asignan correctamente por segmento
        """
        # Cliente minorista
        cliente_minorista = Cliente.objects.create(
            nombre='Cliente Minorista',
            tipoCliente='F',
            tipoDocCliente='CI',
            docCliente='11111111',
            correoElecCliente='minorista@test.com',
            telefono='0991111111',
            direccion='Dirección',
            ocupacion='Empleado',
            segmento='minorista'
        )
        assert cliente_minorista.beneficio_segmento == 0
        
        # Cliente corporativo
        cliente_corporativo = Cliente.objects.create(
            nombre='Cliente Corporativo',
            tipoCliente='F',
            tipoDocCliente='CI',
            docCliente='22222222',
            correoElecCliente='corporativo@test.com',
            telefono='0992222222',
            direccion='Dirección',
            ocupacion='Gerente',
            segmento='corporativo'
        )
        assert cliente_corporativo.beneficio_segmento == 5
        
        # Cliente VIP
        cliente_vip = Cliente.objects.create(
            nombre='Cliente VIP',
            tipoCliente='F',
            tipoDocCliente='CI',
            docCliente='33333333',
            correoElecCliente='vip@test.com',
            telefono='0993333333',
            direccion='Dirección',
            ocupacion='Empresario',
            segmento='vip'
        )
        assert cliente_vip.beneficio_segmento == 10

    def test_validacion_persona_juridica_debe_usar_ruc(self):
        """
        Prueba 3: Las personas jurídicas deben usar RUC
        """
        # Caso inválido: Persona jurídica con CI
        cliente_invalido = Cliente(
            nombre='Empresa S.A.',
            tipoCliente='J',  # Jurídica
            tipoDocCliente='CI',  # CI es incorrecto para jurídica
            docCliente='12345678',
            correoElecCliente='empresa@test.com',
            telefono='0991234567',
            direccion='Dirección',
            ocupacion='Comercio',
            segmento='corporativo'
        )
        
        # Debe lanzar ValidationError
        with pytest.raises(ValidationError):
            cliente_invalido.clean()

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
            tipoCliente='F',
            tipoDocCliente='CI',
            docCliente='55555555',
            correoElecCliente='sinstripe@test.com',
            telefono='0995555555',
            direccion='Dirección',
            ocupacion='Empleado',
            segmento='minorista'
        )
        
        assert cliente.tiene_tarjetas_activas() == False