"""
Utilidades para autenticación de dos factores (2FA) en transacciones del Tauser.

Este módulo contiene todas las funciones necesarias para implementar
el sistema de autenticación de dos factores para transacciones en Tauser,
incluyendo generación de tokens, envío de emails y validaciones.

Funcionalidades principales:
    - Verificación de estado de 2FA en el sistema
    - Generación de tokens aleatorios de 6 dígitos
    - Envío de tokens por email
    - Validación de tokens ingresados por usuarios
    - Gestión del ciclo de vida de tokens (creación, validación, expiración)
    - Limpieza de tokens expirados

Configuración requerida en settings.py:
    ENABLE_2FA_TRANSACTIONS: bool - Habilita/deshabilita el sistema 2FA
    TWO_FACTOR_AUTH: dict - Configuración de parámetros del sistema 2FA
        - TOKEN_LENGTH: int - Longitud del token (default: 6)
        - TOKEN_EXPIRY_MINUTES: int - Minutos de validez del token (default: 1)
        - EMAIL_SUBJECT: str - Asunto del email
        - EMAIL_FROM: str - Email remitente

Author: Sistema de Desarrollo Global Exchange
Date: 2025
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
    
    Esta función consulta la configuración del sistema para determinar
    si la autenticación de dos factores está activa para las transacciones.
    
    Returns:
        bool: True si el 2FA está habilitado, False en caso contrario
    """
    return getattr(settings, 'ENABLE_2FA_TRANSACTIONS', False)

def generate_2fa_token():
    """
    Genera un token aleatorio de dígitos numéricos.
    
    Utiliza la configuración TOKEN_LENGTH del sistema para determinar
    la longitud del token. Por defecto genera 6 dígitos.
    
    Returns:
        str: Token numérico aleatorio
    """
    token_length = settings.TWO_FACTOR_AUTH.get('TOKEN_LENGTH', 6)
    return ''.join(random.choices(string.digits, k=token_length))

def send_2fa_email(usuario, token):
    """
    Envía un email con el token 2FA al usuario.
    
    Renderiza un template HTML con el token y lo envía al email del usuario.
    También genera una versión de texto plano como fallback.
    
    Args:
        usuario (Usuario): Usuario al que enviar el token. Debe tener un email válido.
        token (str): Token numérico a enviar al usuario
        
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
        html_message = render_to_string('emails/2fa_token.html', context)
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
    
    Esta es la función principal para iniciar el flujo 2FA. Genera un token,
    lo almacena en la base de datos asociado a los datos de la transacción,
    y envía el token al usuario por email.
    
    Args:
        usuario (Usuario): Usuario para el que crear el token
        transaccion_data (dict): Datos de la transacción a almacenar
        
    Returns:
        dict: Diccionario con el resultado de la operación
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
    
    Busca el token más reciente no usado del usuario, verifica que no haya
    expirado y que coincida con el token ingresado. Si es válido, marca el
    token como usado y devuelve los datos de la transacción asociada.
    
    Args:
        usuario (Usuario): Usuario que intenta validar el token
        token_input (str): Token numérico ingresado por el usuario
        
    Returns:
        dict: Diccionario con el resultado de la validación
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
    
    Elimina todos los tokens cuya fecha de expiración sea anterior al momento
    actual.
    
    Returns:
        int: Número de tokens eliminados
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
        dict: Diccionario con información del estado del token
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
