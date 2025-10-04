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
