"""
Vistas AJAX para autenticación de dos factores (2FA) en Tauser.

Este módulo contiene las vistas para manejar el flujo 2FA mediante AJAX,
permitiendo la integración con un modal en el frontend.
"""

import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from transacciones.utils_2fa import (
    is_2fa_enabled, create_transaction_token, validate_2fa_token
)
from transacciones.models import Transaccion
import logging

logger = logging.getLogger(__name__)

@require_http_methods(["POST"])
def send_2fa_token(request):
    """
    Vista AJAX para enviar token 2FA al email del usuario asociado a la transacción.
    """
    try:
        # Verificar si 2FA está habilitado
        if not is_2fa_enabled():
            return JsonResponse({
                'success': False,
                'message': 'El sistema de verificación 2FA no está habilitado',
                'error': '2FA_DISABLED'
            })
        
        # Obtener datos de la transacción desde la sesión
        transaccion_id = request.session.get('transaccion')
        if not transaccion_id:
            return JsonResponse({
                'success': False,
                'message': 'No se encontró información de transacción',
                'error': 'NO_TRANSACTION_DATA'
            })
        
        try:
            transaccion = Transaccion.objects.get(id=transaccion_id)
        except Transaccion.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Transacción no encontrada',
                'error': 'TRANSACTION_NOT_FOUND'
            })
        
        # Verificar que el usuario tenga email
        if not transaccion.usuario.email:
            return JsonResponse({
                'success': False,
                'message': 'El usuario asociado a esta transacción no tiene email registrado',
                'error': 'NO_EMAIL'
            })
        
        # Preparar datos de la transacción para el token
        transaccion_data = {
            'transaccion_id': transaccion.id,
            'cliente_id': transaccion.cliente.id,
            'tipo': transaccion.tipo,
            'monto': str(transaccion.monto),
            'moneda_id': transaccion.moneda.id,
            'precio_final': transaccion.precio_final,
            'medio_pago': transaccion.medio_pago,
            'medio_cobro': transaccion.medio_cobro
        }
        
        # Crear token y enviar email
        result = create_transaction_token(transaccion.usuario, transaccion_data)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': result['message'],
                'expires_at': result['expires_at'].isoformat(),
                'expiry_minutes': settings.TWO_FACTOR_AUTH.get('TOKEN_EXPIRY_MINUTES', 1)
            })
        else:
            return JsonResponse({
                'success': False,
                'message': result['message'],
                'error': result.get('error', 'UNKNOWN_ERROR')
            })
            
    except Exception as e:
        logger.error(f"Error en send_2fa_token: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor',
            'error': 'SERVER_ERROR'
        })

@require_http_methods(["POST"])
def verify_2fa_token(request):
    """
    Vista AJAX para verificar el token 2FA ingresado por el usuario.
    """
    try:
        # Verificar si 2FA está habilitado
        if not is_2fa_enabled():
            return JsonResponse({
                'success': False,
                'message': 'El sistema de verificación 2FA no está habilitado',
                'error': '2FA_DISABLED'
            })
        
        # Obtener transacción de la sesión
        transaccion_id = request.session.get('transaccion')
        if not transaccion_id:
            return JsonResponse({
                'success': False,
                'message': 'No se encontró información de transacción',
                'error': 'NO_TRANSACTION_DATA'
            })
        
        try:
            transaccion = Transaccion.objects.get(id=transaccion_id)
        except Transaccion.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Transacción no encontrada',
                'error': 'TRANSACTION_NOT_FOUND'
            })
        
        # Obtener token del request
        data = json.loads(request.body)
        token_input = data.get('token', '').strip()
        
        if not token_input:
            return JsonResponse({
                'success': False,
                'message': 'Debes ingresar el código de verificación',
                'error': 'EMPTY_TOKEN'
            })
        
        # Validar formato del token (6 dígitos)
        if not token_input.isdigit() or len(token_input) != 6:
            return JsonResponse({
                'success': False,
                'message': 'El código debe contener exactamente 6 dígitos',
                'error': 'INVALID_FORMAT'
            })
        
        # Validar el token
        result = validate_2fa_token(transaccion.usuario, token_input)
        
        if result['success']:
            logger.info(f"Token 2FA validado exitosamente para transacción {transaccion.id}")
            
            # Construir URL de redirección
            redirect_url = f'/ingreso-billetes/{transaccion.token}/'
            
            return JsonResponse({
                'success': True,
                'message': 'Token verificado correctamente. Continuando con la transacción...',
                'transaccion_id': transaccion.id,
                'redirect_url': redirect_url
            })
        else:
            return JsonResponse({
                'success': False,
                'message': result['message'],
                'error': result.get('error', 'VALIDATION_FAILED')
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Datos inválidos en la solicitud',
            'error': 'INVALID_JSON'
        })
    except Exception as e:
        logger.error(f"Error en verify_2fa_token: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor',
            'error': 'SERVER_ERROR'
        })
