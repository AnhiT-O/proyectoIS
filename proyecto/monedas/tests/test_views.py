import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from monedas.models import Moneda
from usuarios.models import Usuario
from roles.models import Roles


@pytest.mark.django_db
class TestMonedaViews:
    """Pruebas unitarias para las vistas de Moneda"""

    def setup_method(self):
        """Limpiar la base de datos antes de cada prueba"""
        Moneda.objects.all().delete()
        from usuarios.models import Usuario
        Usuario.objects.all().delete()

    @pytest.fixture
    def client(self):
        """Cliente de pruebas Django"""
        return Client()

    @pytest.fixture
    def usuario_con_permisos(self):
        """Usuario con permisos para gestionar monedas"""
        usuario = Usuario(
            username='testuser',
            email='test@test.com',
            first_name='Usuario Test',
            last_name='Test',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            is_active=True
        )
        usuario.set_password('testpass123')
        usuario.save()
        
        # Crear un rol con permisos
        rol, created = Roles.objects.get_or_create(name='Administrador', defaults={'descripcion': 'Admin test'})
        content_type = ContentType.objects.get_for_model(Moneda)
        
        # Agregar permisos de monedas
        perm_gestion = Permission.objects.get_or_create(
            codename='gestion',
            name='Puede gestionar monedas (crear y editar)',
            content_type=content_type,
        )[0]
        perm_activacion = Permission.objects.get_or_create(
            codename='activacion',
            name='Puede activar/desactivar monedas',
            content_type=content_type,
        )[0]
        
        rol.permissions.add(perm_gestion, perm_activacion)
        usuario.groups.add(rol)
        
        return usuario

    @pytest.fixture
    def usuario_sin_permisos(self):
        """Usuario sin permisos para gestionar monedas"""
        usuario = Usuario(
            username='noAdmin',
            email='noAdmin@test.com',
            first_name='Usuario Sin Permisos',
            last_name='Test',
            tipo_cedula='CI',
            cedula_identidad='87654321',
            is_active=True
        )
        usuario.set_password('testpass123')
        usuario.save()
        return usuario

    def test_vista_moneda_crear_usuario_autenticado_con_permiso(self, client, usuario_con_permisos):
        """
        Prueba 11: Vista moneda_crear: solo usuarios autenticados y con permiso pueden crear monedas.
        """
        client.force_login(usuario_con_permisos)
        
        response = client.get(reverse('monedas:crear_monedas'))
        assert response.status_code == 200

        # Probar POST con datos válidos
        form_data = {
            'nombre': 'Euro',
            'simbolo': 'EUR',
            'tasa_base': 8000,
            'comision_compra': 150,
            'comision_venta': 200,
            'decimales': 2
        }
        response = client.post(reverse('monedas:crear_monedas'), data=form_data)
        assert response.status_code == 302  # Redirection after success

        # Verificar que se creó la moneda
        moneda = Moneda.objects.get(nombre='Euro')
        assert moneda.simbolo == 'EUR'

    def test_vista_moneda_crear_usuario_no_autenticado(self, client):
        """
        Prueba 11: Vista moneda_crear: usuarios no autenticados son redirigidos al login.
        """
        response = client.get(reverse('monedas:crear_monedas'))
        assert response.status_code == 302  # Redirection to login
        assert '/ingresar/' in response.url

    def test_vista_moneda_crear_usuario_sin_permiso(self, client, usuario_sin_permisos):
        """
        Prueba 11: Vista moneda_crear: usuarios sin permiso reciben error 403.
        """
        client.force_login(usuario_sin_permisos)
        
        response = client.get(reverse('monedas:crear_monedas'))
        assert response.status_code == 403  # Permission denied

    def test_vista_moneda_crear_muestra_errores_formulario_invalido(self, client, usuario_con_permisos):
        """
        Prueba 12: Vista moneda_crear: muestra errores si los datos del formulario son inválidos.
        """
        client.force_login(usuario_con_permisos)
        
        # Datos inválidos - nombre vacío
        form_data = {
            'nombre': '',
            'simbolo': 'EUR',
            'tasa_base': 8000,
            'comision_compra': 150,
            'comision_venta': 200
        }
        
        response = client.post(reverse('monedas:crear_monedas'), data=form_data)
        assert response.status_code == 200  # Regresa al formulario
        assert 'form' in response.context
        assert not response.context['form'].is_valid()
        assert 'nombre' in response.context['form'].errors

    def test_vista_moneda_lista_muestra_todas_las_monedas(self, client, usuario_con_permisos):
        """
        Prueba 13: Vista moneda_lista: muestra todas las monedas.
        """
        # Crear monedas de prueba
        Moneda.objects.create(
            nombre='Dólar',
            simbolo='USD',
            tasa_base=7400,
            comision_compra=200,
            comision_venta=250
        )
        Moneda.objects.create(
            nombre='Euro',
            simbolo='EUR',
            tasa_base=8000,
            comision_compra=150,
            comision_venta=200
        )
        
        client.force_login(usuario_con_permisos)
        
        response = client.get(reverse('monedas:lista_monedas'))
        assert response.status_code == 200
        assert 'monedas' in response.context
        assert len(response.context['monedas']) == 2

    def test_vista_moneda_lista_busqueda_por_nombre(self, client, usuario_con_permisos):
        """
        Prueba 13: Vista moneda_lista: permite búsqueda por nombre.
        """
        Moneda.objects.create(
            nombre='Dólar',
            simbolo='USD',
            tasa_base=7400,
            comision_compra=200,
            comision_venta=250
        )
        Moneda.objects.create(
            nombre='Euro',
            simbolo='EUR',
            tasa_base=8000,
            comision_compra=150,
            comision_venta=200
        )
        
        client.force_login(usuario_con_permisos)
        
        response = client.get(reverse('monedas:lista_monedas'), {'busqueda': 'Dólar'})
        assert response.status_code == 200
        assert len(response.context['monedas']) == 1
        assert response.context['monedas'][0].nombre == 'Dólar'

    def test_vista_moneda_lista_busqueda_por_simbolo(self, client, usuario_con_permisos):
        """
        Prueba 13: Vista moneda_lista: permite búsqueda por símbolo.
        """
        Moneda.objects.create(
            nombre='Dólar',
            simbolo='USD',
            tasa_base=7400,
            comision_compra=200,
            comision_venta=250
        )
        Moneda.objects.create(
            nombre='Euro',
            simbolo='EUR',
            tasa_base=8000,
            comision_compra=150,
            comision_venta=200
        )
        
        client.force_login(usuario_con_permisos)
        
        response = client.get(reverse('monedas:lista_monedas'), {'busqueda': 'EUR'})
        assert response.status_code == 200
        assert len(response.context['monedas']) == 1
        assert response.context['monedas'][0].simbolo == 'EUR'

    def test_vista_moneda_lista_activar_desactivar_con_permiso(self, client, usuario_con_permisos):
        """
        Prueba 14: Vista moneda_lista: permite activar/desactivar monedas solo a usuarios con permiso.
        """
        moneda = Moneda.objects.create(
            nombre='Dólar',
            simbolo='USD',
            tasa_base=7400,
            comision_compra=200,
            comision_venta=250,
            activa=True
        )
        
        client.force_login(usuario_con_permisos)
        
        # Desactivar la moneda
        response = client.post(reverse('monedas:lista_monedas'), {
            'cambiar_estado': 'true',
            'moneda_id': moneda.id
        })
        assert response.status_code == 200
        
        # Verificar que se desactivó
        moneda.refresh_from_db()
        assert not moneda.activa

    def test_vista_moneda_editar_usuario_con_permiso_gestion(self, client, usuario_con_permisos):
        """
        Prueba 15: Vista moneda_editar: solo usuarios con permiso pueden editar.
        """
        moneda = Moneda.objects.create(
            nombre='Dólar',
            simbolo='USD',
            tasa_base=7400,
            comision_compra=200,
            comision_venta=250
        )
        
        client.force_login(usuario_con_permisos)
        
        response = client.get(reverse('monedas:editar_monedas', args=[moneda.pk]))
        assert response.status_code == 200
        assert 'form' in response.context

        # Probar edición
        form_data = {
            'nombre': 'Dólar Actualizado',
            'simbolo': 'USD',
            'tasa_base': 7500,
            'comision_compra': 180,
            'comision_venta': 220,
            'decimales': 2
        }
        
        response = client.post(reverse('monedas:editar_monedas', args=[moneda.pk]), data=form_data)
        assert response.status_code == 302  # Redirection after success
        
        moneda.refresh_from_db()
        assert moneda.nombre == 'Dólar Actualizado'

    def test_vista_moneda_editar_usuario_sin_permiso(self, client, usuario_sin_permisos):
        """
        Prueba 15: Vista moneda_editar: usuarios sin permiso reciben error 403.
        """
        moneda = Moneda.objects.create(
            nombre='Dólar',
            simbolo='USD',
            tasa_base=7400,
            comision_compra=200,
            comision_venta=250
        )
        
        client.force_login(usuario_sin_permisos)
        
        response = client.get(reverse('monedas:editar_monedas', args=[moneda.pk]))
        assert response.status_code == 403  # Permission denied

    def test_vista_moneda_editar_oculta_campos_segun_permisos(self, client):
        """
        Prueba 15: Vista moneda_editar: se ocultan campos según permisos.
        """
        # Crear usuario solo con permiso de cotización
        usuario = Usuario(
            username='cotizador',
            email='cotizador@test.com',
            first_name='Cotizador',
            last_name='Test',
            tipo_cedula='CI',
            cedula_identidad='11223344',
            is_active=True
        )
        usuario.set_password('testpass123')
        usuario.save()
        
        rol, created = Roles.objects.get_or_create(name='Cotizador', defaults={'descripcion': 'Solo cotización'})
        content_type = ContentType.objects.get_for_model(Moneda)
        
        perm_cotizacion = Permission.objects.get_or_create(
            codename='cotizacion',
            name='Puede actualizar cotización de monedas',
            content_type=content_type,
        )[0]
        
        rol.permissions.add(perm_cotizacion)
        usuario.groups.add(rol)
        
        moneda = Moneda.objects.create(
            nombre='Dólar',
            simbolo='USD',
            tasa_base=7400,
            comision_compra=200,
            comision_venta=250
        )
        
        client.force_login(usuario)
        
        response = client.get(reverse('monedas:editar_monedas', args=[moneda.pk]))
        assert response.status_code == 200
        
        # Verificar que ciertos campos no están en el formulario
        form = response.context['form']
        assert 'nombre' not in form.fields
        assert 'simbolo' not in form.fields
        assert 'decimales' not in form.fields
        # Pero sí debería tener los campos de cotización
        assert 'tasa_base' in form.fields
        assert 'comision_compra' in form.fields
        assert 'comision_venta' in form.fields