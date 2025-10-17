import pytest
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.http import JsonResponse
from django.contrib.auth.models import Permission
from decimal import Decimal
from unittest.mock import Mock, patch
import json

from proyecto.views import (
    login_usuario, logout_usuario, inicio, simular, 
    custom_permission_denied_view
)
from monedas.models import Moneda
from clientes.models import Cliente

User = get_user_model()


@pytest.mark.django_db
class TestLoginUsuarioView:
    """Pruebas para la vista login_usuario"""
    
    def setup_method(self):
        self.client = Client()
        self.factory = RequestFactory()
    
    def test_redirige_a_perfil_si_usuario_autenticado(self):
        """
        Prueba 5: Redirigir a perfil si el usuario ya está autenticado
        """
        # Crear usuario y autenticarlo
        user = User(
            username='authuser',
            first_name='Auth',
            last_name='User',
            email='auth@example.com',
            numero_documento='11111111',
            bloqueado=False,
            is_active=True
        )
        user.set_password('testpass')
        user.save()
        
        self.client.login(username='authuser', password='testpass')
        
        # Acceder a la vista de login
        response = self.client.get(reverse('login'))
        
        # Verificar redirección a perfil
        assert response.status_code == 302
        assert response.url == reverse('usuarios:perfil')

    def test_permite_login_y_redirige_correctamente(self):
        """
        Prueba 6: Permitir login y redirigir correctamente tras autenticación
        """
        # Crear usuario
        user = User(
            username='loginuser',
            first_name='Login',
            last_name='User',
            email='login@example.com',
            numero_documento='22222222',
            bloqueado=False,
            is_active=True
        )
        user.set_password('loginpass')
        user.save()
        
        # Realizar POST con credenciales válidas
        response = self.client.post(reverse('login'), {
            'username': 'loginuser',
            'password': 'loginpass'
        })
        
        # Verificar redirección tras login exitoso
        assert response.status_code == 302
        assert response.url == reverse('inicio')
        
        # Verificar mensaje de bienvenida
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert 'Bienvenido a Global Exchange, Login' in str(messages[0])

    def test_no_permite_login_credenciales_invalidas(self):
        """
        Prueba 7: No permitir login con credenciales inválidas
        """
        # Crear usuario
        user = User(
            username='validuser',
            first_name='Valid',
            last_name='User',
            email='valid@example.com',
            numero_documento='33333333',
            bloqueado=False,
            is_active=True
        )
        user.set_password('correctpass')
        user.save()
        
        # Intentar login con credenciales incorrectas
        response = self.client.post(reverse('login'), {
            'username': 'validuser',
            'password': 'wrongpass'
        })
        
        # Verificar que no redirige (status 200 = renderiza form con errores)
        assert response.status_code == 200
        assert 'form' in response.context
        assert not response.context['form'].is_valid()


@pytest.mark.django_db 
class TestLogoutUsuarioView:
    """Pruebas para la vista logout_usuario"""
    
    def setup_method(self):
        self.client = Client()
    
    def test_cierra_sesion_y_redirige_con_mensaje(self):
        """
        Prueba 8: Cerrar sesión y redirigir a inicio mostrando mensaje de éxito
        """
        # Crear y autenticar usuario
        user = User(
            username='logoutuser',
            first_name='Logout',
            last_name='User',
            email='logout@example.com',
            numero_documento='44444444',
            bloqueado=False,
            is_active=True
        )
        user.set_password('testpass')
        user.save()
        
        self.client.login(username='logoutuser', password='testpass')
        
        # Realizar logout
        response = self.client.get(reverse('logout'))
        
        # Verificar redirección a inicio
        assert response.status_code == 302
        assert response.url == reverse('inicio')
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert 'Has cerrado sesión exitosamente.' in str(messages[0])


@pytest.mark.django_db
class TestInicioView:
    """Pruebas para la vista inicio"""
    
    def setup_method(self):
        self.client = Client()
        
        # Crear moneda de prueba
        self.moneda = Moneda.objects.create(
            nombre='Test Coin',
            simbolo='TST',
            activa=True,
            tasa_base=1000,
            comision_compra=50,
            comision_venta=60,
            decimales=2
        )
    
    def test_renderiza_correctamente_usuario_autenticado(self):
        """
        Prueba 9: Renderizar correctamente para usuario autenticado mostrando cotizaciones
        """
        # Crear y autenticar usuario
        user = User(
            username='authuser',
            first_name='Auth',
            last_name='User',
            numero_documento='55555555',
            bloqueado=False,
            is_active=True
        )
        user.set_password('testpass')
        user.save()
        
        self.client.login(username='authuser', password='testpass')
        
        # Acceder a la vista inicio
        response = self.client.get(reverse('inicio'))
        
        # Verificar respuesta exitosa
        assert response.status_code == 200
        assert 'cotizaciones' in response.context
        assert len(response.context['cotizaciones']) > 0
        
        # Verificar que contiene datos de la moneda
        cotizacion = response.context['cotizaciones'][0]
        assert cotizacion['moneda'] == self.moneda
        assert 'precio_compra' in cotizacion
        assert 'precio_venta' in cotizacion

    def test_renderiza_correctamente_usuario_no_autenticado(self):
        """
        Prueba 10: Renderiza correctamente cotizaciones para usuario no autenticado.
        """
        # Acceder sin autenticar
        response = self.client.get(reverse('inicio'))
        
        # Verificar respuesta exitosa
        assert response.status_code == 200

        # Verificar que hay cotizaciones para usuario no autenticado
        assert 'cotizaciones' in response.context

@pytest.mark.django_db
class TestSimularView:
    """Pruebas para la vista simular"""
    
    def setup_method(self):
        self.client = Client()
        
        # Crear usuario autenticado
        self.user = User(
            username='simuser',
            first_name='Sim',
            last_name='User',
            email='sim@example.com',
            tipo_documento='CI',
            numero_documento='77777777',
            bloqueado=False,
            is_active=True
        )
        self.user.set_password('testpass')
        self.user.save()
        
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
