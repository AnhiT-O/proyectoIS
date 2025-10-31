"""
Tests para las vistas 2FA del sistema TAUser.

Este módulo contiene tests unitarios para las vistas AJAX de autenticación
de dos factores (2FA) utilizadas en las terminales autónomas de usuario.

Author: Equipo de desarrollo Global Exchange  
Date: 2025
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, Client, RequestFactory
from django.http import JsonResponse
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta

from ..forms import Token2FAForm


class TestSend2FATokenView:
    """
    Tests para la vista AJAX send_2fa_token.
    
    Verifica el envío de tokens 2FA por email a usuarios.
    """
    
    def test_send_2fa_disabled_returns_error(self):
        """
        Test 1: Verificar respuesta cuando 2FA está deshabilitado.
        
        - Debe retornar error cuando 2FA no está habilitado
        - Debe incluir mensaje apropiado y código de error
        - Debe devolver JsonResponse con success=False
        """
        from django.test import RequestFactory
        import json
        
        # Crear request factory
        factory = RequestFactory()
        request = factory.post('/2fa/send-token/', content_type='application/json')
        
        # Mock para simular 2FA deshabilitado
        with patch('tauser.views_2fa.is_2fa_enabled') as mock_2fa_enabled:
            mock_2fa_enabled.return_value = False
            
            # Importar y llamar la vista
            from tauser.views_2fa import send_2fa_token
            response = send_2fa_token(request)
            
            # Verificar que es JsonResponse
            assert isinstance(response, JsonResponse)
            
            # Verificar contenido de la respuesta
            response_data = json.loads(response.content)
            assert response_data['success'] == False
            assert '2FA no está habilitado' in response_data['message']
            assert response_data['error'] == '2FA_DISABLED'
    
    def test_send_2fa_no_transaction_in_session(self):
        """
        Test 2: Verificar respuesta cuando no hay transacción en sesión.
        
        - Debe retornar error cuando no existe transacción en sesión
        - Debe incluir mensaje y código de error apropiados
        - Debe manejar sesiones vacías correctamente
        """
        from django.test import RequestFactory
        import json
        
        # Crear request mockeado con sesión vacía
        factory = RequestFactory()
        request = factory.post('/2fa/send-token/', content_type='application/json')
        
        # Mock de sesión vacía
        request.session = {'other_key': 'value'}  # Sin 'transaccion'
        
        # Mock para 2FA habilitado pero sin transacción en sesión
        with patch('tauser.views_2fa.is_2fa_enabled') as mock_2fa_enabled:
            mock_2fa_enabled.return_value = True
            
            # Importar y llamar la vista
            from tauser.views_2fa import send_2fa_token
            response = send_2fa_token(request)
            
            # Verificar respuesta
            response_data = json.loads(response.content)
            assert response_data['success'] == False
            assert 'No se encontró información de transacción' in response_data['message']
            assert response_data['error'] == 'NO_TRANSACTION_DATA'
    
    def test_send_2fa_user_without_email(self):
        """
        Test 3: Verificar respuesta cuando el usuario no tiene email.
        
        - Debe manejar casos donde el usuario asociado no tiene email
        - Debe retornar error apropiado
        - Debe validar la existencia de email antes de enviar token
        """
        from django.test import RequestFactory
        import json
        
        # Crear request con sesión válida
        factory = RequestFactory()
        request = factory.post('/2fa/send-token/', content_type='application/json')
        
        # Mock de sesión con ID de transacción válido
        request.session = {'transaccion': 1}
        
        # Mock de las dependencias
        with patch('tauser.views_2fa.is_2fa_enabled') as mock_2fa_enabled, \
             patch('tauser.views_2fa.Transaccion.objects.get') as mock_get_transaccion:
            
            mock_2fa_enabled.return_value = True
            
            # Mock de transacción con usuario sin email
            mock_transaccion = Mock()
            mock_transaccion.id = 1
            mock_transaccion.usuario.email = None  # Usuario sin email
            mock_get_transaccion.return_value = mock_transaccion
            
            # Importar y llamar la vista
            from tauser.views_2fa import send_2fa_token
            response = send_2fa_token(request)
            
            # Verificar respuesta
            response_data = json.loads(response.content)
            assert response_data['success'] == False
            assert 'no tiene email registrado' in response_data['message']
            assert response_data['error'] == 'NO_EMAIL'


class TestVerify2FATokenView:
    """
    Tests para la vista AJAX verify_2fa_token.
    
    Verifica la validación de tokens 2FA ingresados por usuarios.
    """
    
    def test_verify_2fa_invalid_token_format(self):
        """
        Test 4: Verificar validación de formato de token 2FA.
        
        - Debe rechazar tokens que no sean exactamente 6 dígitos
        - Debe rechazar tokens con letras o caracteres especiales
        - Debe retornar error de formato inválido
        """
        from django.test import RequestFactory
        import json
        
        # Crear request con token inválido
        factory = RequestFactory()
        request_data = json.dumps({'token': 'ABC123'})  # Token con letras
        request = factory.post(
            '/2fa/verify-token/', 
            data=request_data,
            content_type='application/json'
        )
        
        # Mock de sesión
        request.session = {'transaccion': 1}
        
        # Mock de las dependencias
        with patch('tauser.views_2fa.is_2fa_enabled') as mock_2fa_enabled, \
             patch('tauser.views_2fa.Transaccion.objects.get') as mock_get_transaccion:
            
            mock_2fa_enabled.return_value = True
            
            # Mock de transacción válida
            mock_transaccion = Mock()
            mock_transaccion.id = 1
            mock_transaccion.usuario.email = 'test@example.com'
            mock_get_transaccion.return_value = mock_transaccion
            
            # Importar y llamar la vista
            from tauser.views_2fa import verify_2fa_token
            response = verify_2fa_token(request)
            
            # Verificar respuesta
            response_data = json.loads(response.content)
            assert response_data['success'] == False
            assert 'exactamente 6 dígitos' in response_data['message']
            assert response_data['error'] == 'INVALID_FORMAT'
    
    def test_verify_2fa_successful_validation(self):
        """
        Test 5: Verificar validación exitosa de token 2FA.
        
        - Debe aceptar tokens válidos de 6 dígitos
        - Debe llamar a la función de validación de token
        - Debe retornar success=True y URL de redirección
        - Debe manejar transacciones pendientes correctamente
        """
        from django.test import RequestFactory
        import json
        
        # Crear request con token válido
        factory = RequestFactory()
        request_data = json.dumps({'token': '123456'})  # Token válido
        request = factory.post(
            '/2fa/verify-token/', 
            data=request_data,
            content_type='application/json'
        )
        
        # Mock de sesión
        request.session = {'transaccion': 1}
        
        # Mock de las dependencias
        with patch('tauser.views_2fa.is_2fa_enabled') as mock_2fa_enabled, \
             patch('tauser.views_2fa.Transaccion.objects.get') as mock_get_transaccion, \
             patch('tauser.views_2fa.validate_2fa_token') as mock_validate_token:
            
            mock_2fa_enabled.return_value = True
            
            # Mock de transacción pendiente
            mock_transaccion = Mock()
            mock_transaccion.id = 1
            mock_transaccion.token = 'ABC12345'
            mock_transaccion.estado = 'Pendiente'
            mock_transaccion.usuario.email = 'test@example.com'
            mock_get_transaccion.return_value = mock_transaccion
            
            # Mock de validación exitosa
            mock_validate_token.return_value = {
                'success': True,
                'message': 'Token válido'
            }
            
            # Importar y llamar la vista
            from tauser.views_2fa import verify_2fa_token
            response = verify_2fa_token(request)
            
            # Verificar respuesta
            response_data = json.loads(response.content)
            assert response_data['success'] == True
            assert 'Token verificado correctamente' in response_data['message']
            assert 'redirect_url' in response_data
            assert '/ingreso-billetes/ABC12345/' in response_data['redirect_url']
            
            # Verificar que se llamó la validación
            mock_validate_token.assert_called_once_with(mock_transaccion.usuario, '123456')


class TestViews2FAStructure:
    """
    Tests para verificar la estructura y existencia de las vistas 2FA.
    
    Verifica que las funciones estén correctamente definidas y documentadas.
    """
    
    def test_views_2fa_file_structure(self):
        """
        Test para verificar la estructura del archivo views_2fa.py.
        
        - Debe contener las funciones send_2fa_token y verify_2fa_token
        - Debe tener decoradores @require_http_methods apropiados
        - Debe importar las dependencias necesarias
        """
        import os
        import re
        
        # Leer el archivo views_2fa.py
        views_2fa_path = os.path.join(os.path.dirname(__file__), '..', 'views_2fa.py')
        with open(views_2fa_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar que las funciones principales existen
        assert 'def send_2fa_token(request):' in content
        assert 'def verify_2fa_token(request):' in content
        
        # Verificar decoradores
        assert '@require_http_methods(["POST"])' in content
        
        # Verificar importaciones necesarias
        assert 'from django.http import JsonResponse' in content
        assert 'from transacciones.utils_2fa import' in content
        
        # Verificar que tienen docstrings
        send_token_match = re.search(r'def send_2fa_token\(request\):\s*"""(.*?)"""', content, re.DOTALL)
        assert send_token_match is not None
        
        verify_token_match = re.search(r'def verify_2fa_token\(request\):\s*"""(.*?)"""', content, re.DOTALL)
        assert verify_token_match is not None
    
    def test_token_2fa_form_integration(self):
        """
        Test para verificar integración con Token2FAForm.
        
        - El formulario Token2FAForm debe existir y funcionar
        - Debe validar códigos de 6 dígitos correctamente
        - Debe rechazar formatos inválidos
        """
        # Verificar que el formulario existe y funciona
        form_valido = Token2FAForm(data={'codigo_2fa': '123456'})
        assert form_valido.is_valid()
        assert form_valido.cleaned_data['codigo_2fa'] == '123456'
        
        # Verificar que rechaza formatos inválidos
        form_invalido1 = Token2FAForm(data={'codigo_2fa': '12345'})  # Muy corto
        assert not form_invalido1.is_valid()
        
        form_invalido2 = Token2FAForm(data={'codigo_2fa': '12345A'})  # Con letras
        assert not form_invalido2.is_valid()
        
        form_invalido3 = Token2FAForm(data={'codigo_2fa': ''})  # Vacío
        assert not form_invalido3.is_valid()