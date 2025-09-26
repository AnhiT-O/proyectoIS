"""
Configuración de la aplicación medios_acreditacion.

Este módulo contiene la configuración específica de la aplicación Django
que maneja los medios de acreditación del sistema, incluyendo cuentas bancarias
y billeteras electrónicas.

La configuración incluye metadatos de la aplicación como el nombre interno,
el nombre para mostrar en el admin y el tipo de campo automático por defecto.

Clases:
    MediosAcreditacionConfig: Configuración principal de la aplicación.
"""

from django.apps import AppConfig


class MediosAcreditacionConfig(AppConfig):
    """
    Configuración de la aplicación medios_acreditacion.
    
    Esta clase define la configuración específica para la aplicación que gestiona
    los medios de acreditación de los clientes, como cuentas bancarias y billeteras
    electrónicas.
    
    Attributes:
        default_auto_field (str): Tipo de campo automático por defecto para las claves primarias.
        name (str): Nombre interno de la aplicación Django.
        verbose_name (str): Nombre legible para mostrar en la interfaz de administración.
    """
    
    # Tipo de campo automático por defecto para claves primarias
    # BigAutoField permite un rango más amplio de valores que AutoField
    default_auto_field = 'django.db.models.BigAutoField'
    
    # Nombre interno de la aplicación (debe coincidir con el nombre del directorio)
    name = 'medios_acreditacion'
    
    # Nombre legible para mostrar en el admin de Django y otras interfaces
    verbose_name = 'Medios de Acreditación'
    
    def ready(self):
        """
        Método que se ejecuta cuando la aplicación está lista.
        
        Se ejecuta una vez cuando Django inicializa la aplicación.
        Útil para registrar señales, realizar configuraciones adicionales
        o ejecutar código de inicialización.
        
        Actualmente no se realizan acciones adicionales en este método.
        """
        # TODO: Registrar señales si es necesario
        # TODO: Configurar permisos personalizados si es necesario
        pass
