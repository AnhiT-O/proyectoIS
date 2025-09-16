import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase
from medios_pago.models import MedioPago, MedioPagoCliente
from clientes.models import Cliente
import uuid


@pytest.mark.django_db
class TestMedioPagoClienteModel:
    """
    Pruebas unitarias para el modelo MedioPagoCliente
    """

    def setup_method(self):
        """Configuración inicial para cada prueba"""
        # Crear un cliente con documento único
        doc_unico = str(uuid.uuid4())[:10]  # Documento único para evitar conflictos
        self.cliente = Cliente.objects.create(
            nombre='Juan Perez',
            tipoDocCliente='CI',
            docCliente=doc_unico,
            telefono='0981234567',
            correoElecCliente=f'juan{doc_unico}@example.com',
            tipoCliente='F',
            direccion='Asunción',
            ocupacion='Empleado'
        )
        
        # Obtener medio de pago tarjeta de crédito existente
        self.medio_tarjeta, created = MedioPago.objects.get_or_create(
            tipo='tarjeta_credito',
            defaults={'activo': True}
        )

    def test_limite_tarjetas_credito_por_cliente(self):
        """
        12. Modelo MedioPagoCliente: no permite más de 3 tarjetas de crédito activas por cliente.
        """
        # Crear 3 tarjetas de crédito válidas
        for i in range(3):
            MedioPagoCliente.objects.create(
                medio_pago=self.medio_tarjeta,
                cliente=self.cliente,
                numero_tarjeta=f'123456789012345{i}',
                cvv_tarjeta='123',
                nombre_titular_tarjeta='Juan Perez',
                fecha_vencimiento_tc='12/2027',
                descripcion_tarjeta=f'Tarjeta {i+1}',
                moneda_tc='USD'
            )

        # Intentar crear una cuarta tarjeta debe fallar
        with pytest.raises(ValidationError) as excinfo:
            medio_pago_cliente = MedioPagoCliente(
                medio_pago=self.medio_tarjeta,
                cliente=self.cliente,
                numero_tarjeta='1234567890123456',
                cvv_tarjeta='123',
                nombre_titular_tarjeta='Juan Perez',
                fecha_vencimiento_tc='12/2027',
                descripcion_tarjeta='Tarjeta 4',
                moneda_tc='USD'
            )
            medio_pago_cliente.full_clean()

        assert 'numero_tarjeta' in excinfo.value.error_dict
        assert 'Un cliente no puede tener más de 3 tarjetas de crédito configuradas' in str(excinfo.value.error_dict['numero_tarjeta'])

    def test_validacion_numero_tarjeta_longitud_formato(self):
        """
        13. Modelo MedioPagoCliente: error si el número de tarjeta o CVV no cumplen requisitos de longitud o formato.
        """
        # Caso: número de tarjeta con menos de 16 dígitos
        with pytest.raises(ValidationError) as excinfo:
            medio_pago_cliente = MedioPagoCliente(
                medio_pago=self.medio_tarjeta,
                cliente=self.cliente,
                numero_tarjeta='12345678901234',  # 14 dígitos
                cvv_tarjeta='123'
            )
            medio_pago_cliente.full_clean()

        assert 'numero_tarjeta' in excinfo.value.error_dict
        assert 'El número de tarjeta debe tener exactamente 16 dígitos' in str(excinfo.value.error_dict['numero_tarjeta'])

        # Caso: número de tarjeta no numérico
        with pytest.raises(ValidationError) as excinfo:
            medio_pago_cliente = MedioPagoCliente(
                medio_pago=self.medio_tarjeta,
                cliente=self.cliente,
                numero_tarjeta='123456789012345a',  # contiene letra
                cvv_tarjeta='123'
            )
            medio_pago_cliente.full_clean()

        assert 'numero_tarjeta' in excinfo.value.error_dict
        assert 'El número de tarjeta debe contener solo números' in str(excinfo.value.error_dict['numero_tarjeta'])

        # Caso: CVV con menos de 3 dígitos
        with pytest.raises(ValidationError) as excinfo:
            medio_pago_cliente = MedioPagoCliente(
                medio_pago=self.medio_tarjeta,
                cliente=self.cliente,
                numero_tarjeta='1234567890123456',
                cvv_tarjeta='12'  # 2 dígitos
            )
            medio_pago_cliente.full_clean()

        assert 'cvv_tarjeta' in excinfo.value.error_dict
        assert 'El CVV debe tener exactamente 3 dígitos' in str(excinfo.value.error_dict['cvv_tarjeta'])

        # Caso: CVV no numérico
        with pytest.raises(ValidationError) as excinfo:
            medio_pago_cliente = MedioPagoCliente(
                medio_pago=self.medio_tarjeta,
                cliente=self.cliente,
                numero_tarjeta='1234567890123456',
                cvv_tarjeta='12a'  # contiene letra
            )
            medio_pago_cliente.full_clean()

        assert 'cvv_tarjeta' in excinfo.value.error_dict
        assert 'El CVV debe contener solo números' in str(excinfo.value.error_dict['cvv_tarjeta'])

    def test_puede_procesar_transacciones_tarjeta_credito(self):
        """
        14. Modelo MedioPagoCliente: propiedad puede_procesar_transacciones retorna True solo si los datos requeridos están completos según el tipo.
        """
        # Caso: tarjeta de crédito incompleta (sin datos)
        medio_pago_cliente = MedioPagoCliente.objects.create(
            medio_pago=self.medio_tarjeta,
            cliente=self.cliente
        )
        assert not medio_pago_cliente.puede_procesar_transacciones

        # Caso: tarjeta de crédito completa
        medio_pago_cliente.numero_tarjeta = '1234567890123456'
        medio_pago_cliente.cvv_tarjeta = '123'
        medio_pago_cliente.nombre_titular_tarjeta = 'Juan Perez'
        medio_pago_cliente.fecha_vencimiento_tc = '12/2027'
        medio_pago_cliente.descripcion_tarjeta = 'Tarjeta personal'
        medio_pago_cliente.save()
        
        assert medio_pago_cliente.puede_procesar_transacciones

    def test_puede_procesar_transacciones_transferencia(self):
        """
        14. Modelo MedioPagoCliente: propiedad puede_procesar_transacciones retorna True solo si los datos requeridos están completos según el tipo.
        """
        # Obtener medio de pago transferencia existente
        medio_transferencia, created = MedioPago.objects.get_or_create(
            tipo='transferencia',
            defaults={'activo': True}
        )
        
        # Caso: transferencia incompleta (sin datos)
        medio_pago_cliente = MedioPagoCliente.objects.create(
            medio_pago=medio_transferencia,
            cliente=self.cliente
        )
        assert not medio_pago_cliente.puede_procesar_transacciones

        # Caso: transferencia completa
        medio_pago_cliente.numero_cuenta = '123456789012'
        medio_pago_cliente.banco = 'Banco Nacional'
        medio_pago_cliente.nombre_titular_cuenta = 'Juan Perez'
        medio_pago_cliente.tipo_cuenta = 'corriente'
        medio_pago_cliente.save()
        
        assert medio_pago_cliente.puede_procesar_transacciones

    def test_puede_procesar_transacciones_medios_basicos(self):
        """
        14. Modelo MedioPagoCliente: propiedad puede_procesar_transacciones retorna True solo si los datos requeridos están completos según el tipo.
        """
        # Medios de pago que siempre pueden procesar transacciones
        tipos_basicos = ['efectivo', 'cheque', 'billetera_electronica']
        
        for tipo in tipos_basicos:
            medio_pago, created = MedioPago.objects.get_or_create(
                tipo=tipo,
                defaults={'activo': True}
            )
            medio_pago_cliente = MedioPagoCliente.objects.create(
                medio_pago=medio_pago,
                cliente=self.cliente
            )
            assert medio_pago_cliente.puede_procesar_transacciones

    def test_get_descripcion_completa_tarjeta(self):
        """
        15. Modelo MedioPagoCliente: método get_descripcion_completa retorna la descripción adecuada según el tipo de medio.
        """
        # Caso: tarjeta de crédito con descripción personalizada
        medio_pago_cliente = MedioPagoCliente.objects.create(
            medio_pago=self.medio_tarjeta,
            cliente=self.cliente,
            numero_tarjeta='1234567890123456',
            descripcion_tarjeta='Mi tarjeta personal'
        )
        assert medio_pago_cliente.get_descripcion_completa() == 'Mi tarjeta personal'

        # Caso: tarjeta de crédito sin descripción personalizada
        medio_pago_cliente.descripcion_tarjeta = None
        medio_pago_cliente.save()
        assert medio_pago_cliente.get_descripcion_completa() == 'Tarjeta terminada en ****3456'

    def test_get_descripcion_completa_transferencia(self):
        """
        15. Modelo MedioPagoCliente: método get_descripcion_completa retorna la descripción adecuada según el tipo de medio.
        """
        medio_transferencia, created = MedioPago.objects.get_or_create(
            tipo='transferencia',
            defaults={'activo': True}
        )
        
        # Caso: transferencia con banco
        medio_pago_cliente = MedioPagoCliente.objects.create(
            medio_pago=medio_transferencia,
            cliente=self.cliente,
            numero_cuenta='123456789012',
            banco='Banco Nacional'
        )
        assert medio_pago_cliente.get_descripcion_completa() == 'Cuenta 123456789012 - Banco Nacional'

        # Caso: transferencia sin banco
        medio_pago_cliente.banco = None
        medio_pago_cliente.save()
        assert medio_pago_cliente.get_descripcion_completa() == 'Cuenta 123456789012'

    def test_get_descripcion_completa_billetera(self):
        """
        15. Modelo MedioPagoCliente: método get_descripcion_completa retorna la descripción adecuada según el tipo de medio.
        """
        medio_billetera, created = MedioPago.objects.get_or_create(
            tipo='billetera_electronica',
            defaults={'activo': True}
        )
        medio_pago_cliente = MedioPagoCliente.objects.create(
            medio_pago=medio_billetera,
            cliente=self.cliente
        )
        assert medio_pago_cliente.get_descripcion_completa() == 'Billetera'

    def test_get_descripcion_completa_otros_medios(self):
        """
        15. Modelo MedioPagoCliente: método get_descripcion_completa retorna la descripción adecuada según el tipo de medio.
        """
        medios_otros = ['efectivo', 'cheque']
        
        for tipo in medios_otros:
            medio_pago, created = MedioPago.objects.get_or_create(
                tipo=tipo,
                defaults={'activo': True}
            )
            medio_pago_cliente = MedioPagoCliente.objects.create(
                medio_pago=medio_pago,
                cliente=self.cliente
            )
            assert medio_pago_cliente.get_descripcion_completa() == medio_pago.get_tipo_display()
