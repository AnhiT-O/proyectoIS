"""
Pruebas simples para las vistas de `proyecto.reportes.views`.

Estas pruebas verifican permisos y la API JSON de ganancias en forma básica.
"""

import pytest
from decimal import Decimal
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import Group

from monedas.models import Moneda
from clientes.models import Cliente
from usuarios.models import Usuario
from transacciones.models import Transaccion


@pytest.mark.django_db
class TestReportesViews:
    """Pruebas básicas de autorización y cálculo en reportes/views.py"""

    def test_transacciones_reportes_denegado_para_no_admin(self):
        """Verifica que un usuario sin el grupo 'Administrador' reciba 403 al acceder a la vista.

        Escenario:
        - Crear un usuario normal sin pertenecer al grupo Administrador.
        - Hacer login y solicitar la vista `reportes:transacciones`.
        Resultado esperado: HTTP 403 (acceso denegado).
        """
        client = Client()
        # crear usuario normal
        user = Usuario.objects.create(
            username='normal_user',
            email='normal@example.com',
            first_name='Normal',
            last_name='User',
            numero_documento='90000001',
            telefono='0990000001',
            is_active=True,
        )
        user.set_password('password')
        user.save()

        client.force_login(user)
        url = reverse('reportes:transacciones')
        resp = client.get(url)
        assert resp.status_code == 403

    def test_transacciones_reportes_ok_para_admin(self):
        """Comprueba que un usuario del grupo 'Administrador' puede acceder a la vista.

        Escenario:
        - Crear/obtener el grupo 'Administrador' y un usuario que pertenezca a ese grupo.
        - Iniciar sesión y solicitar la vista `reportes:transacciones`.
        Resultado esperado: HTTP 200 y claves esperadas en el contexto del template.
        """
        client = Client()
        # crear grupo y usuario admin
        admin_grp, _ = Group.objects.get_or_create(name='Administrador')
        admin = Usuario.objects.create(
            username='admin_user',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            numero_documento='90000002',
            telefono='0990000002',
            is_active=True,
        )
        admin.set_password('password')
        admin.save()
        admin.groups.add(admin_grp)

        client.force_login(admin)
        url = reverse('reportes:transacciones')
        resp = client.get(url)
        assert resp.status_code == 200
        # la vista coloca 'filas' y 'resumen_por_moneda' en el contexto
        assert 'filas' in resp.context
        assert 'resumen_por_moneda' in resp.context

    def test_obtener_datos_ganancias_calculo_basico(self):
        """Valida la API JSON de ganancias para una transacción de venta simple.

        Escenario:
        - Crear usuario administrador y moneda con `comision_venta=10`.
        - Crear una transacción de tipo 'venta' con monto 100 y estado 'completa'.
        - Llamar a `reportes:api_ganancias` con rango 'hoy'.
        Resultado esperado: la ganancia total reportada coincide con 100 * comision_venta.
        """
        client = Client()
        admin_grp, _ = Group.objects.get_or_create(name='Administrador')
        admin = Usuario.objects.create(
            username='admin_api',
            email='admin_api@example.com',
            first_name='Api',
            last_name='Admin',
            numero_documento='90000003',
            telefono='0990000003',
            is_active=True,
        )
        admin.set_password('password')
        admin.save()
        admin.groups.add(admin_grp)

        # crear moneda con comision_venta = 10
        moneda = Moneda.objects.create(
            nombre='TestCoin',
            simbolo='TST',
            tasa_base=1000,
            comision_compra=5,
            comision_venta=10,
        )

        # crear cliente y usuario operador requerido por Transaccion
        cliente = Cliente.objects.create(
            nombre='Cliente Test',
            tipo_documento='CI',
            numero_documento='70000001',
            correo_electronico='c@test.com',
            telefono='0997000001',
            tipo='F',
            direccion='Dirección',
            ocupacion='Ninguna',
            segmento='minorista',
        )

        operador = Usuario.objects.create(
            username='oper',
            email='oper@example.com',
            first_name='Oper',
            last_name='User',
            numero_documento='90000004',
            telefono='0990000004',
            is_active=True,
        )
        operador.set_password('password')
        operador.save()

        # crear transaccion venta completa: ganancia = monto * comision_venta
        t = Transaccion.objects.create(
            cliente=cliente,
            tipo='venta',
            moneda=moneda,
            monto=Decimal('100'),
            cotizacion=0,
            precio_base=0,
            beneficio_segmento=0,
            porc_beneficio_segmento='0',
            recargo_pago=0,
            porc_recargo_pago='0',
            recargo_cobro=0,
            porc_recargo_cobro='0',
            precio_final=0,
            pagado=0,
            medio_pago='Efectivo',
            medio_cobro='Efectivo',
            estado='completa',
            usuario=operador,
        )

        client.force_login(admin)
        url = reverse('reportes:api_ganancias')
        resp = client.get(url, {'rango': 'hoy'})
        assert resp.status_code == 200
        data = resp.json()
        # ganancia esperada = 100 * 10 = 1000
        assert float(data['ganancia_total']) == pytest.approx(100 * 10, rel=1e-6)

    def test_obtener_datos_ganancias_filtro_por_moneda(self):
        """Verifica que el parámetro `moneda_id` filtra correctamente las ganancias.

        Escenario:
        - Crear dos monedas y una transacción en cada una (ambas completadas).
        - Consultar la API especificando `moneda_id` de la primera moneda.
        Resultado esperado: `ganancia_total` corresponde solo a las transacciones de la moneda indicada.
        """
        client = Client()
        admin_grp, _ = Group.objects.get_or_create(name='Administrador')
        admin = Usuario.objects.create(
            username='admin_filter',
            email='admin_filter@example.com',
            first_name='Admin',
            last_name='Filter',
            numero_documento='90000005',
            telefono='0990000005',
            is_active=True,
        )
        admin.set_password('password')
        admin.save()
        admin.groups.add(admin_grp)

        moneda1 = Moneda.objects.create(nombre='M1', simbolo='M1', tasa_base=100, comision_compra=1, comision_venta=2)
        moneda2 = Moneda.objects.create(nombre='M2', simbolo='M2', tasa_base=200, comision_compra=2, comision_venta=4)

        cliente = Cliente.objects.create(
            nombre='Cliente Filter',
            tipo_documento='CI',
            numero_documento='70000002',
            correo_electronico='cf@test.com',
            telefono='0997000002',
            tipo='F',
            direccion='Dirección',
            ocupacion='Ninguna',
            segmento='minorista',
        )

        operador = Usuario.objects.create(
            username='oper2',
            email='oper2@example.com',
            first_name='Oper2',
            last_name='User2',
            numero_documento='90000006',
            telefono='0990000006',
            is_active=True,
        )
        operador.set_password('password')
        operador.save()

        # una transaccion en cada moneda
        Transaccion.objects.create(
            cliente=cliente, tipo='venta', moneda=moneda1, monto=Decimal('10'), cotizacion=0,
            precio_base=0, beneficio_segmento=0, porc_beneficio_segmento='0', recargo_pago=0,
            porc_recargo_pago='0', recargo_cobro=0, porc_recargo_cobro='0', precio_final=0,
            pagado=0, medio_pago='Efectivo', medio_cobro='Efectivo', estado='completa', usuario=operador
        )
        Transaccion.objects.create(
            cliente=cliente, tipo='venta', moneda=moneda2, monto=Decimal('20'), cotizacion=0,
            precio_base=0, beneficio_segmento=0, porc_beneficio_segmento='0', recargo_pago=0,
            porc_recargo_pago='0', recargo_cobro=0, porc_recargo_cobro='0', precio_final=0,
            pagado=0, medio_pago='Efectivo', medio_cobro='Efectivo', estado='completa', usuario=operador
        )

        client.force_login(admin)
        url = reverse('reportes:api_ganancias')
        resp = client.get(url, {'rango': 'hoy', 'moneda_id': str(moneda1.id)})
        assert resp.status_code == 200
        data = resp.json()
        # solo debe contar la transaccion con moneda1: ganancia = 10 * comision_venta(2) = 20
        assert float(data['ganancia_total']) == pytest.approx(10 * 2, rel=1e-6)

    def test_obtener_datos_ganancias_ignora_transacciones_incompletas(self):
        """Asegura que transacciones no completas (estado distinto a 'completa'/'confirmada') no se acumulen.

        Escenario:
        - Crear una transacción con estado 'Pendiente'.
        - Llamar a la API de ganancias.
        Resultado esperado: `ganancia_total` es 0.0.
        """
        client = Client()
        admin_grp, _ = Group.objects.get_or_create(name='Administrador')
        admin = Usuario.objects.create(
            username='admin_ignore',
            email='admin_ignore@example.com',
            first_name='Admin',
            last_name='Ignore',
            numero_documento='90000007',
            telefono='0990000007',
            is_active=True,
        )
        admin.set_password('password')
        admin.save()
        admin.groups.add(admin_grp)

        moneda = Moneda.objects.create(nombre='MIgn', simbolo='MIG', tasa_base=100, comision_compra=1, comision_venta=2)
        cliente = Cliente.objects.create(
            nombre='Cliente Ignore',
            tipo_documento='CI',
            numero_documento='70000003',
            correo_electronico='ci@test.com',
            telefono='0997000003',
            tipo='F', direccion='Dirección', ocupacion='Ninguna', segmento='minorista'
        )
        operador = Usuario.objects.create(
            username='oper3', email='oper3@example.com', first_name='Oper3', last_name='User3',
            numero_documento='90000008', telefono='0990000008', is_active=True
        )
        operador.set_password('password')
        operador.save()

        # crear transaccion pendiente (no debe contarse)
        Transaccion.objects.create(
            cliente=cliente, tipo='venta', moneda=moneda, monto=Decimal('50'), cotizacion=0,
            precio_base=0, beneficio_segmento=0, porc_beneficio_segmento='0', recargo_pago=0,
            porc_recargo_pago='0', recargo_cobro=0, porc_recargo_cobro='0', precio_final=0,
            pagado=0, medio_pago='Efectivo', medio_cobro='Efectivo', estado='Pendiente', usuario=operador
        )

        client.force_login(admin)
        url = reverse('reportes:api_ganancias')
        resp = client.get(url, {'rango': 'hoy'})
        data = resp.json()
        assert float(data['ganancia_total']) == pytest.approx(0.0, abs=1e-6)
