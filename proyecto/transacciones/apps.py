"""
Configuración de la aplicación de transacciones para Global Exchange.

Este módulo contiene la configuración específica de la aplicación transacciones,
incluyendo la configuración de campos automáticos y el nombre de la aplicación.

Classes:
    TransaccionesConfig: Configuración principal de la aplicación

Author: Equipo de desarrollo Global Exchange
Date: 2024
"""

from django.apps import AppConfig


class TransaccionesConfig(AppConfig):
    """
    Configuración de la aplicación transacciones.
    
    Define la configuración específica para la aplicación de transacciones
    del sistema Global Exchange, incluyendo el tipo de campo automático
    para las claves primarias.
    
    Attributes:
        default_auto_field (str): Tipo de campo automático para claves primarias
        name (str): Nombre de la aplicación Django
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transacciones'
