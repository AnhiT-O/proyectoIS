"""
Vistas específicas para autenticación de dos factores (2FA) en transacciones.

Este módulo contiene las vistas AJAX y de procesamiento específicas
para manejar el flujo de 2FA en transacciones.

Author: Sistema de Desarrollo Global Exchange  
Date: 2024
"""

import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from .utils_2fa import (
    is_2fa_enabled, create_transaction_token, 
    validate_2fa_token, get_token_status
)
from .models import Transaccion, calcular_conversion
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

@login_required
@require_http_methods(["POST"])
def send_2fa_token(request):
    """
    Vista AJAX para enviar token 2FA al email del usuario.
    Se llama cuando el usuario hace clic en "Confirmar transacción".
    
    Returns:
        JsonResponse: Resultado del envío del token
    """
    try:
        # Verificar si 2FA está habilitado
        if not is_2fa_enabled():
            return JsonResponse({
                'success': False,
                'message': 'El sistema de verificación 2FA no está habilitado',
                'error': '2FA_DISABLED'
            })
        
        # Verificar que el usuario tenga email
        if not request.user.email:
            return JsonResponse({
                'success': False,
                'message': 'No tienes un email registrado en tu cuenta',
                'error': 'NO_EMAIL'
            })
        
        # Obtener datos de la transacción desde la sesión
        transaccion_id = request.session.get('transaccion_id')
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
        result = create_transaction_token(request.user, transaccion_data)
        
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

@login_required
@require_http_methods(["POST"])
def verify_2fa_token(request):
    """
    Vista AJAX para verificar el token 2FA ingresado por el usuario.
    
    Returns:
        JsonResponse: Resultado de la verificación del token
    """
    try:
        # Verificar si 2FA está habilitado
        if not is_2fa_enabled():
            return JsonResponse({
                'success': False,
                'message': 'El sistema de verificación 2FA no está habilitado',
                'error': '2FA_DISABLED'
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
        result = validate_2fa_token(request.user, token_input)
        
        if result['success']:
            # Token válido - ahora procesar la transacción
            transaccion_data = result['transaccion_data']
            
            try:
                # Obtener la transacción
                transaccion = Transaccion.objects.get(id=transaccion_data['transaccion_id'])
                
                # Cambiar estado de la transacción a confirmada
                transaccion.estado = 'Confirmada'
                transaccion.save()
                
                # Limpiar sesión
                if 'transaccion_id' in request.session:
                    del request.session['transaccion_id']
                
                logger.info(f"Transacción {transaccion.id} confirmada via 2FA por usuario {request.user.username}")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Transacción confirmada exitosamente',
                    'transaccion_id': transaccion.id,
                    'redirect_url': f'/operaciones/detalle/{transaccion.id}/'
                })
                
            except Transaccion.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Error: transacción no encontrada',
                    'error': 'TRANSACTION_NOT_FOUND'
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

@login_required
@require_http_methods(["GET"])
def get_token_status_view(request):
    """
    Vista AJAX para obtener el estado actual del token del usuario.
    
    Returns:
        JsonResponse: Estado del token (válido, expirado, etc.)
    """
    try:
        if not is_2fa_enabled():
            return JsonResponse({
                'success': False,
                'message': 'El sistema de verificación 2FA no está habilitado',
                'error': '2FA_DISABLED'
            })
        
        status = get_token_status(request.user)
        
        return JsonResponse({
            'success': True,
            'token_status': status
        })
        
    except Exception as e:
        logger.error(f"Error en get_token_status_view: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error al obtener estado del token',
            'error': 'SERVER_ERROR'
        })

@login_required
@require_http_methods(["POST"])
def resend_2fa_token(request):
    """
    Vista AJAX para reenviar el token 2FA.
    
    Returns:
        JsonResponse: Resultado del reenvío del token
    """
    try:
        if not is_2fa_enabled():
            return JsonResponse({
                'success': False,
                'message': 'El sistema de verificación 2FA no está habilitado',
                'error': '2FA_DISABLED'
            })
        
        # Verificar que el usuario tenga email
        if not request.user.email:
            return JsonResponse({
                'success': False,
                'message': 'No tienes un email registrado en tu cuenta',
                'error': 'NO_EMAIL'
            })
        
        # Obtener datos de la transacción desde la sesión
        transaccion_id = request.session.get('transaccion_id')
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
        
        # Crear nuevo token y enviar email
        result = create_transaction_token(request.user, transaccion_data)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': 'Nuevo código enviado a tu email',
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
        logger.error(f"Error en resend_2fa_token: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor',
            'error': 'SERVER_ERROR'
        })