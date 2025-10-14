"""
Utilidades para autenticación de dos factores (2FA) en transacciones.

Este módulo contiene todas las funciones necesarias para implementar
el sistema de autenticación de dos factores para transacciones,
incluyendo generación de tokens, envío de emails y validaciones.

Author: Sistema de Desarrollo Global Exchange
Date: 2024
"""

import random
import string
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import TransactionToken
import logging

logger = logging.getLogger(__name__)

def is_2fa_enabled():
    """
    Verifica si el 2FA está habilitado globalmente en el sistema.
    
    Returns:
        bool: True si el 2FA está habilitado, False en caso contrario
    """
    return getattr(settings, 'ENABLE_2FA_TRANSACTIONS', False)

def generate_2fa_token():
    """
    Genera un token aleatorio de 6 dígitos.
    
    Returns:
        str: Token de 6 dígitos
    """
    token_length = settings.TWO_FACTOR_AUTH.get('TOKEN_LENGTH', 6)
    return ''.join(random.choices(string.digits, k=token_length))

def send_2fa_email(usuario, token):
    """
    Envía un email con el token 2FA al usuario.
    
    Args:
        usuario (Usuario): Usuario al que enviar el token
        token (str): Token de 6 dígitos a enviar
        
    Returns:
        bool: True si el email se envió correctamente, False en caso contrario
    """
    try:
        # Configuración del email
        subject = settings.TWO_FACTOR_AUTH.get('EMAIL_SUBJECT', 'Código de verificación')
        from_email = settings.TWO_FACTOR_AUTH.get('EMAIL_FROM', settings.EMAIL_HOST_USER)
        recipient_list = [usuario.email]
        
        # Contexto para el template del email
        context = {
            'usuario': usuario,
            'token': token,
            'expiry_minutes': settings.TWO_FACTOR_AUTH.get('TOKEN_EXPIRY_MINUTES', 1)
        }
        
        # Renderizar el template HTML del email
        html_message = render_to_string('transacciones/emails/2fa_token.html', context)
        plain_message = strip_tags(html_message)
        
        # Enviar el email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Token 2FA enviado exitosamente a {usuario.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error al enviar token 2FA a {usuario.email}: {str(e)}")
        return False

def create_transaction_token(usuario, transaccion_data):
    """
    Crea un token de transacción y envía el email de verificación.
    
    Args:
        usuario (Usuario): Usuario para el que crear el token
        transaccion_data (dict): Datos de la transacción a almacenar
        
    Returns:
        dict: Resultado de la operación con éxito/error y detalles
    """
    try:
        # Generar el token usando el modelo
        token_obj = TransactionToken.generate_token(usuario, transaccion_data)
        
        # Enviar email con el token
        email_sent = send_2fa_email(usuario, token_obj.token)
        
        if email_sent:
            return {
                'success': True,
                'message': f'Token de verificación enviado a {usuario.email}',
                'token_id': token_obj.id,
                'expires_at': token_obj.expires_at
            }
        else:
            # Si falla el envío del email, eliminar el token
            token_obj.delete()
            return {
                'success': False,
                'message': 'Error al enviar el email de verificación',
                'error': 'EMAIL_SEND_FAILED'
            }
            
    except Exception as e:
        logger.error(f"Error al crear token de transacción: {str(e)}")
        return {
            'success': False,
            'message': 'Error interno al generar token de verificación',
            'error': str(e)
        }

def validate_2fa_token(usuario, token_input):
    """
    Valida un token 2FA ingresado por el usuario.
    
    Args:
        usuario (Usuario): Usuario que intenta validar el token
        token_input (str): Token ingresado por el usuario
        
    Returns:
        dict: Resultado de la validación con éxito/error y datos de transacción
    """
    try:
        # Buscar el token más reciente no usado del usuario
        token_obj = TransactionToken.objects.filter(
            usuario=usuario,
            used=False
        ).order_by('-created_at').first()
        
        if not token_obj:
            return {
                'success': False,
                'message': 'No hay token de verificación pendiente',
                'error': 'NO_TOKEN_FOUND'
            }
        
        # Verificar si el token ha expirado
        if not token_obj.is_valid():
            token_obj.delete()  # Limpiar token expirado
            return {
                'success': False,
                'message': 'El token de verificación ha expirado',
                'error': 'TOKEN_EXPIRED'
            }
        
        # Verificar si el token coincide
        if token_obj.token != token_input.strip():
            return {
                'success': False,
                'message': 'Token de verificación incorrecto',
                'error': 'INVALID_TOKEN'
            }
        
        # Token válido - marcarlo como usado y devolver datos de transacción
        transaccion_data = token_obj.transaccion_data
        token_obj.mark_as_used()
        
        logger.info(f"Token 2FA validado exitosamente para usuario {usuario.username}")
        
        return {
            'success': True,
            'message': 'Token verificado correctamente',
            'transaccion_data': transaccion_data
        }
        
    except Exception as e:
        logger.error(f"Error al validar token 2FA: {str(e)}")
        return {
            'success': False,
            'message': 'Error interno al validar token',
            'error': str(e)
        }

def cleanup_expired_tokens():
    """
    Limpia tokens expirados de la base de datos.
    Esta función debería ejecutarse periódicamente (por ejemplo, con un cron job).
    """
    try:
        expired_count = TransactionToken.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()[0]
        
        if expired_count > 0:
            logger.info(f"Eliminados {expired_count} tokens expirados")
            
        return expired_count
        
    except Exception as e:
        logger.error(f"Error al limpiar tokens expirados: {str(e)}")
        return 0

def get_token_status(usuario):
    """
    Obtiene el estado del token actual del usuario.
    
    Args:
        usuario (Usuario): Usuario para verificar el estado del token
        
    Returns:
        dict: Estado del token (exists, valid, expires_at, etc.)
    """
    try:
        token_obj = TransactionToken.objects.filter(
            usuario=usuario,
            used=False
        ).order_by('-created_at').first()
        
        if not token_obj:
            return {
                'exists': False,
                'valid': False,
                'message': 'No hay token pendiente'
            }
        
        is_valid = token_obj.is_valid()
        
        return {
            'exists': True,
            'valid': is_valid,
            'expires_at': token_obj.expires_at,
            'created_at': token_obj.created_at,
            'time_remaining': (token_obj.expires_at - timezone.now()).total_seconds() if is_valid else 0,
            'message': 'Token válido' if is_valid else 'Token expirado'
        }
        
    except Exception as e:
        logger.error(f"Error al obtener estado del token: {str(e)}")
        return {
            'exists': False,
            'valid': False,
            'message': 'Error al verificar estado del token'
        }