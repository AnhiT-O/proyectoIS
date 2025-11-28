"""
Vistas específicas para autenticación de dos factores (2FA) en transacciones.

Este módulo contiene las vistas AJAX y de procesamiento específicas
para manejar el flujo de 2FA en transacciones.

Funcionalidades:
    - Envío de tokens 2FA por email
    - Verificación de tokens ingresados por el usuario
    - Consulta de estado de tokens
    - Reenvío de tokens expirados o perdidos

Endpoints:
    POST /transacciones/2fa/send/ - Enviar token 2FA
    POST /transacciones/2fa/verify/ - Verificar token ingresado
    GET  /transacciones/2fa/status/ - Consultar estado del token
    POST /transacciones/2fa/resend/ - Reenviar token

Todas las vistas requieren autenticación de usuario y devuelven
respuestas JSON para ser consumidas por JavaScript en el frontend.

Author: Sistema de Desarrollo Global Exchange  
Date: 2025
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
    Obtiene los datos de la transacción de la sesión, genera un token
    y lo envía por email.
    
    Decoradores:
        @login_required: Requiere usuario autenticado
        @require_http_methods(["POST"]): Solo acepta método POST
    
    Args:
        request (HttpRequest): Objeto request de Django con:
            - user: Usuario autenticado
            - session['transaccion_id']: ID de la transacción pendiente
    
    Returns:
        JsonResponse: Respuesta JSON con estructura:
            En caso de éxito:
                {
                    'success': True,
                    'message': str - Mensaje de confirmación,
                    'expires_at': str - Fecha de expiración ISO format,
                    'expiry_minutes': int - Minutos de validez del token
                }
            En caso de error:
                {
                    'success': False,
                    'message': str - Descripción del error,
                    'error': str - Código de error
                }
    
    Códigos de error:
        - 2FA_DISABLED: El sistema 2FA no está habilitado
        - NO_EMAIL: El usuario no tiene email registrado
        - NO_TRANSACTION_DATA: No se encontró transacción en la sesión
        - TRANSACTION_NOT_FOUND: La transacción no existe en la BD
        - EMAIL_SEND_FAILED: Error al enviar el email
        - SERVER_ERROR: Error interno del servidor
        
    Example (JavaScript):
        fetch('/transacciones/2fa/send/', {
            method: 'POST',
            headers: {'X-CSRFToken': csrftoken}
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Token enviado, expira en:', data.expiry_minutes);
            }
        });
    
    Note:
        - Requiere que exista transaccion_id en la sesión
        - El token se envía al email del usuario autenticado
        - El token expira según la configuración TOKEN_EXPIRY_MINUTES
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
    
    Valida el token ingresado contra el token almacenado en la base de datos.
    Si es válido, prepara la transacción para continuar con el flujo normal.
    
    Decoradores:
        @login_required: Requiere usuario autenticado
        @require_http_methods(["POST"]): Solo acepta método POST
    
    Args:
        request (HttpRequest): Objeto request de Django con:
            - user: Usuario autenticado
            - body: JSON con {'token': str} - Token de 6 dígitos ingresado
    
    Returns:
        JsonResponse: Respuesta JSON con estructura:
            En caso de éxito:
                {
                    'success': True,
                    'message': str - Mensaje de confirmación,
                    'transaccion_id': int - ID de la transacción verificada,
                    'confirmacion_url': str - URL para enviar POST,
                    'requires_post': True - Indica que se debe hacer POST
                }
            En caso de error:
                {
                    'success': False,
                    'message': str - Descripción del error,
                    'error': str - Código de error
                }
    
    Códigos de error:
        - 2FA_DISABLED: El sistema 2FA no está habilitado
        - EMPTY_TOKEN: No se ingresó ningún token
        - INVALID_FORMAT: El token no tiene el formato correcto (6 dígitos)
        - NO_TOKEN_FOUND: No hay token pendiente para el usuario
        - TOKEN_EXPIRED: El token ha expirado
        - INVALID_TOKEN: El token ingresado es incorrecto
        - TRANSACTION_NOT_FOUND: La transacción no existe
        - INVALID_JSON: Los datos enviados no son JSON válido
        - SERVER_ERROR: Error interno del servidor
        
    Example (JavaScript):
        fetch('/transacciones/2fa/verify/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({token: '123456'})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.requires_post) {
                // Hacer POST a la URL de confirmación con accion='confirmar'
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = data.confirmacion_url;
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'accion';
                input.value = 'confirmar';
                form.appendChild(input);
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = csrftoken;
                form.appendChild(csrfInput);
                document.body.appendChild(form);
                form.submit();
            }
        });
    
    Note:
        - El token debe ser exactamente 6 dígitos numéricos
        - El token se marca como usado después de una verificación exitosa
        - Se envía POST a compra_confirmacion o venta_confirmacion con accion='confirmar'
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
            # Token válido - continuar con el flujo normal de la transacción
            transaccion_data = result['transaccion_data']
            
            try:
                # Obtener la transacción
                transaccion = Transaccion.objects.get(id=transaccion_data['transaccion_id'])
                
                # No cambiar el estado aquí, dejar que el flujo normal lo maneje
                # Restaurar la transacción_id en la sesión para el flujo normal
                request.session['transaccion_id'] = transaccion.id
                
                logger.info(f"Token 2FA validado exitosamente para transacción {transaccion.id} por usuario {request.user.username}")
                
                # Enviar POST a confirmación según el tipo de transacción
                if transaccion.tipo == 'compra':
                    confirmacion_url = '/operaciones/comprar/confirmacion/'
                else:  # venta
                    confirmacion_url = '/operaciones/vender/confirmacion/'
                
                return JsonResponse({
                    'success': True,
                    'message': 'Token verificado correctamente. Continuando con la transacción...',
                    'transaccion_id': transaccion.id,
                    'confirmacion_url': confirmacion_url,
                    'requires_post': True  # Indica que se debe hacer POST en lugar de redirect
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
    
    Consulta y devuelve información sobre el token más reciente del usuario,
    incluyendo si existe, si es válido, y tiempo restante hasta expiración.
    Útil para actualizar la UI del frontend (temporizadores, etc.).
    
    Decoradores:
        @login_required: Requiere usuario autenticado
        @require_http_methods(["GET"]): Solo acepta método GET
    
    Args:
        request (HttpRequest): Objeto request de Django con:
            - user: Usuario autenticado
    
    Returns:
        JsonResponse: Respuesta JSON con estructura:
            En caso de éxito:
                {
                    'success': True,
                    'token_status': {
                        'exists': bool - Si existe un token,
                        'valid': bool - Si el token es válido,
                        'expires_at': datetime - Fecha de expiración,
                        'created_at': datetime - Fecha de creación,
                        'time_remaining': float - Segundos restantes,
                        'message': str - Descripción del estado
                    }
                }
            En caso de error:
                {
                    'success': False,
                    'message': str - Descripción del error,
                    'error': str - Código de error
                }
    
    Códigos de error:
        - 2FA_DISABLED: El sistema 2FA no está habilitado
        - SERVER_ERROR: Error interno del servidor
        
    Example (JavaScript):
        fetch('/transacciones/2fa/status/')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.token_status.valid) {
                const seconds = data.token_status.time_remaining;
                updateCountdown(seconds);
            }
        });
    
    Note:
        - No modifica el estado del token
        - Puede llamarse repetidamente para actualizar el estado
        - Útil para implementar temporizadores en el frontend
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
    
    Genera un nuevo token y lo envía por email. Útil cuando el token anterior
    ha expirado o el usuario no recibió el email. Invalida el token anterior
    al crear uno nuevo.
    
    Decoradores:
        @login_required: Requiere usuario autenticado
        @require_http_methods(["POST"]): Solo acepta método POST
    
    Args:
        request (HttpRequest): Objeto request de Django con:
            - user: Usuario autenticado
            - session['transaccion_id']: ID de la transacción pendiente
    
    Returns:
        JsonResponse: Respuesta JSON con estructura:
            En caso de éxito:
                {
                    'success': True,
                    'message': str - Mensaje de confirmación,
                    'expires_at': str - Fecha de expiración ISO format,
                    'expiry_minutes': int - Minutos de validez del nuevo token
                }
            En caso de error:
                {
                    'success': False,
                    'message': str - Descripción del error,
                    'error': str - Código de error
                }
    
    Códigos de error:
        - 2FA_DISABLED: El sistema 2FA no está habilitado
        - NO_EMAIL: El usuario no tiene email registrado
        - NO_TRANSACTION_DATA: No se encontró transacción en la sesión
        - TRANSACTION_NOT_FOUND: La transacción no existe en la BD
        - EMAIL_SEND_FAILED: Error al enviar el email
        - SERVER_ERROR: Error interno del servidor
        
    Example (JavaScript):
        fetch('/transacciones/2fa/resend/', {
            method: 'POST',
            headers: {'X-CSRFToken': csrftoken}
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Nuevo código enviado a tu email');
                resetCountdown(data.expiry_minutes * 60);
            }
        });
    
    Note:
        - Invalida automáticamente el token anterior
        - El nuevo token tiene la misma duración que el anterior
        - Requiere que exista transaccion_id en la sesión
        - Útil para implementar botón "Reenviar código"
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