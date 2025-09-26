"""
Pruebas unitarias muy sencillas para las vistas de la aplicación de clientes.
"""

import pytest
from unittest.mock import Mock

from clientes.models import Cliente
from clientes.views import verificar_acceso_cliente


@pytest.mark.django_db
class TestClienteViews:
    """Pruebas unitarias muy sencillas para las vistas de clientes"""
    
    def test_verificar_acceso_cliente_sin_permisos(self):
        """
        Prueba 1: Usuario sin permisos no tiene acceso
        """
        # Crear mock de usuario sin permisos
        usuario_mock = Mock()
        usuario_mock.has_perm.return_value = False
        usuario_mock.clientes_operados.all.return_value = []
        
        # Crear cliente real
        cliente = Cliente.objects.create(
            nombre='Cliente Test',
            tipoDocCliente='CI',
            docCliente='11111111',
            correoElecCliente='cliente@test.com',
            telefono='0991111111',
            tipoCliente='F',
            direccion='Dirección test',
            ocupacion='Empleado',
            segmento='minorista'
        )
        
        # Usuario sin permisos no debe tener acceso
        resultado = verificar_acceso_cliente(usuario_mock, cliente)
        assert resultado == False

    def test_verificar_acceso_cliente_con_permisos_admin(self):
        """
        Prueba 2: Usuario con permisos admin tiene acceso
        """
        # Crear mock de usuario con permisos admin
        usuario_admin_mock = Mock()
        usuario_admin_mock.has_perm.return_value = True
        
        # Crear cliente real
        cliente = Cliente.objects.create(
            nombre='Cliente Admin',
            tipoDocCliente='CI',
            docCliente='22222222',
            correoElecCliente='clienteadmin@test.com',
            telefono='0992222222',
            tipoCliente='F',
            direccion='Dirección admin',
            ocupacion='Empleado',
            segmento='corporativo'
        )
        
        # Usuario admin debe tener acceso
        resultado = verificar_acceso_cliente(usuario_admin_mock, cliente)
        assert resultado == True

    def test_verificar_acceso_cliente_asociado(self):
        """
        Prueba 3: Usuario asociado tiene acceso aunque no sea admin
        """
        # Crear cliente real
        cliente = Cliente.objects.create(
            nombre='Cliente Asociado',
            tipoDocCliente='CI',
            docCliente='33333333',
            correoElecCliente='clienteasociado@test.com',
            telefono='0993333333',
            tipoCliente='F',
            direccion='Dirección asociado',
            ocupacion='Empleado',
            segmento='vip'
        )
        
        # Crear mock de usuario asociado (sin permisos admin pero con cliente asociado)
        usuario_asociado_mock = Mock()
        usuario_asociado_mock.has_perm.return_value = False
        usuario_asociado_mock.clientes_operados.all.return_value = [cliente]
        
        # Usuario asociado debe tener acceso
        resultado = verificar_acceso_cliente(usuario_asociado_mock, cliente)
        assert resultado == True

    def test_crear_cliente_basico(self):
        """
        Prueba 4: Crear cliente básico para verificar funcionalidad
        """
        cliente = Cliente.objects.create(
            nombre='Cliente Básico',
            tipoDocCliente='CI',
            docCliente='44444444',
            correoElecCliente='basico@test.com',
            telefono='0994444444',
            tipoCliente='F',
            direccion='Dirección básica',
            ocupacion='Empleado',
            segmento='corporativo'
        )
        
        assert cliente.nombre == 'Cliente Básico'
        assert cliente.segmento == 'corporativo'
        assert cliente.beneficio_segmento == 5  # Corporativo = 5

    def test_cliente_str_method(self):
        """
        Prueba 5: Método __str__ del cliente funciona correctamente
        """
        cliente = Cliente.objects.create(
            nombre='Cliente String Test',
            tipoDocCliente='CI',
            docCliente='55555555',
            correoElecCliente='string@test.com',
            telefono='0995555555',
            tipoCliente='F',
            direccion='Dirección string',
            ocupacion='Empleado',
            segmento='minorista'
        )
        
        assert str(cliente) == 'Cliente String Test'