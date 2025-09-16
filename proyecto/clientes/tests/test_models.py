import pytest
from django.core.exceptions import ValidationError
from clientes.models import Cliente


class TestClienteModelo:
    
    @pytest.mark.django_db
    def test_cliente_save_actualiza_beneficio_segun_segmento(self):
        """Prueba 6: Modelo Cliente: método save actualiza correctamente el beneficio según el segmento."""
        
        # Crear cliente con segmento minorista
        cliente_minorista = Cliente(
            nombre='Cliente Minorista',
            tipoDocCliente='CI',
            docCliente='1234567',
            correoElecCliente='minorista@example.com',
            telefono='0981123456',
            tipoCliente='F',
            direccion='Asunción',
            ocupacion='Empleado',
            segmento='minorista'
        )
        cliente_minorista.save()
        assert cliente_minorista.beneficio_segmento == 0
        
        # Crear cliente con segmento corporativo
        cliente_corporativo = Cliente(
            nombre='Cliente Corporativo',
            tipoDocCliente='RUC',
            docCliente='80012345-1',
            correoElecCliente='corporativo@example.com',
            telefono='0981123457',
            tipoCliente='J',
            direccion='Asunción',
            ocupacion='Empresa',
            segmento='corporativo'
        )
        cliente_corporativo.save()
        assert cliente_corporativo.beneficio_segmento == 5
        
        # Crear cliente con segmento VIP
        cliente_vip = Cliente(
            nombre='Cliente VIP',
            tipoDocCliente='CI',
            docCliente='7654321',
            correoElecCliente='vip@example.com',
            telefono='0981123458',
            tipoCliente='F',
            direccion='Asunción',
            ocupacion='Ejecutivo',
            segmento='vip'
        )
        cliente_vip.save()
        assert cliente_vip.beneficio_segmento == 10
        
        # Actualizar segmento y verificar que se actualiza el beneficio
        cliente_minorista.segmento = 'vip'
        cliente_minorista.save()
        assert cliente_minorista.beneficio_segmento == 10

    @pytest.mark.django_db
    def test_cliente_clean_valida_coherencia_tipo_cliente_tipo_documento(self):
        """Prueba 7: Modelo Cliente: método clean valida coherencia entre tipoCliente y tipoDocCliente."""
        
        # Crear cliente jurídico con CI (debe fallar)
        cliente_invalido = Cliente(
            nombre='Empresa SA',
            tipoDocCliente='CI',  # Incorrecto: jurídica debe usar RUC
            docCliente='1234567',
            correoElecCliente='empresa@example.com',
            telefono='0981123456',
            tipoCliente='J',  # Jurídica
            direccion='Asunción',
            ocupacion='Comercio',
            segmento='corporativo'
        )
        
        with pytest.raises(ValidationError) as exc_info:
            cliente_invalido.save()
        
        assert 'tipoDocCliente' in exc_info.value.message_dict
        assert 'Las personas jurídicas deben usar RUC' in str(exc_info.value.message_dict['tipoDocCliente'])
        
        # Crear cliente jurídico con RUC (debe funcionar)
        cliente_valido = Cliente(
            nombre='Empresa SA',
            tipoDocCliente='RUC',  # Correcto
            docCliente='80012345-1',
            correoElecCliente='empresa2@example.com',
            telefono='0981123457',
            tipoCliente='J',  # Jurídica
            direccion='Asunción',
            ocupacion='Comercio',
            segmento='corporativo'
        )
        
        # No debe lanzar excepción
        cliente_valido.save()
        assert cliente_valido.pk is not None
        
        # Crear cliente físico con CI (debe funcionar)
        cliente_fisico = Cliente(
            nombre='Juan Pérez',
            tipoDocCliente='CI',  # Correcto para persona física
            docCliente='7654321',
            correoElecCliente='juan@example.com',
            telefono='0981123458',
            tipoCliente='F',  # Física
            direccion='Asunción',
            ocupacion='Empleado',
            segmento='minorista'
        )
        
        # No debe lanzar excepción
        cliente_fisico.save()
        assert cliente_fisico.pk is not None

    @pytest.mark.django_db
    def test_cliente_str_retorna_nombre_correctamente(self):
        """Prueba 8: Modelo Cliente: método __str__ retorna el nombre correctamente."""
        
        cliente = Cliente(
            nombre='María González',
            tipoDocCliente='CI',
            docCliente='9876543',
            correoElecCliente='maria@example.com',
            telefono='0981123456',
            tipoCliente='F',
            direccion='Asunción',
            ocupacion='Profesora',
            segmento='minorista'
        )
        cliente.save()
        
        assert str(cliente) == 'María González'
        
        # Verificar con otro cliente
        cliente2 = Cliente(
            nombre='Empresa ABC SA',
            tipoDocCliente='RUC',
            docCliente='80054321-7',
            correoElecCliente='abc@example.com',
            telefono='0981654321',
            tipoCliente='J',
            direccion='Ciudad del Este',
            ocupacion='Comercio',
            segmento='corporativo'
        )
        cliente2.save()
        
        assert str(cliente2) == 'Empresa ABC SA'
