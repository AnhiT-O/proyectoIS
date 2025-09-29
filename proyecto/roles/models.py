from django.db import models
from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class Roles(Group):
    """
    Modelo que extiende auth.Group para agregar una descripción a cada rol.

    Attributes:
        descripcion (TextField): Descripción del rol.

    Note:
        -   Se deshabilitan los permisos predeterminados de Django.
        -   Se define un permiso personalizado "gestion" para la gestión de roles.
    """
    descripcion = models.TextField(blank=True, null=True)
    
    class Meta:
        """
        Meta opciones para el modelo Roles.
        
        Attributes:
            verbose_name (str): Nombre singular del modelo.
            verbose_name_plural (str): Nombre plural del modelo.
            db_table (str): Nombre de la tabla en la base de datos.
            default_permissions (list): Lista de permisos predeterminados (vacía para deshabilitarlos).
            permissions (list): Lista de permisos personalizados asociados al modelo.
        """
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        db_table = 'roles'
        default_permissions = []
        permissions = [
            ("gestion", "Puede gestionar roles (crear y editar)"),
        ]

    def __str__(self):
        """
        Representación en cadena del objeto Roles.
        Returns:
            Cadena de texto: Nombre del rol.
        """
        return self.name
    
    @property
    def nombre(self):
        """
        Alias para mantener compatibilidad con código existente.

        Returns:
            Cadena de texto: Nombre del rol.

        Example:
            .. code-block:: python
            
                rol = Roles.objects.get(name='Controlador')
                print(rol.nombre)  # Salida: Controlador
        """
        return self.name


@receiver(post_migrate)
def crear_roles_predefinidos(sender, **kwargs):
    """
    Crea los roles predefinidos después de ejecutar las migraciones.

    Args:
        sender: El remitente de la señal (AppConfig).
        **kwargs: Argumentos adicionales.
    """
    # Definir los roles predefinidos con sus descripciones
    roles_predefinidos = [
        {
            'name': 'Operador',
            'descripcion': 'Rol para usuarios que operan en el sistema, no posee ningún permiso especial, pero pueden operar con clientes y realizar transacciones.'
        },
        {
            'name': 'Analista cambiario',
            'descripcion': 'Rol responsable del análisis de tipos de cambio, pueden gestionar cotizaciones y recargos de transacciones.'
        },
        {
            'name': 'Administrador',
            'descripcion': 'Rol con acceso completo al sistema, posee todos los permisos disponibles.'
        }
    ]
    
    for rol_data in roles_predefinidos:
        rol, created = Roles.objects.get_or_create(
            name=rol_data['name'],
            defaults={'descripcion': rol_data['descripcion']}
        )
        if created:
            print(f"Rol '{rol.nombre}' creado exitosamente.")
