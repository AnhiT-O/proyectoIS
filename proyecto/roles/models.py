from django.db import models
from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class Roles(Group):
    """
    Modelo que extiende auth.Group para agregar funcionalidad específica de roles
    """
    descripcion = models.TextField(blank=True, null=True, help_text="Descripción detallada del rol")
    
    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        db_table = 'roles'
        default_permissions = []  # Deshabilita permisos predeterminados
        permissions = [
            ("gestion", "Puede gestionar roles (crear y editar)"),
        ]

    def __str__(self):
        return self.name
    
    @property
    def nombre(self):
        """Alias para mantener compatibilidad con código existente"""
        return self.name


@receiver(post_migrate)
def crear_roles_predefinidos(sender, **kwargs):
    """
    Crea los roles predefinidos después de ejecutar las migraciones
    y actualiza permisos del administrador con cada migración
    """
    # Definir los roles predefinidos con sus descripciones
    roles_predefinidos = [
        {
            'name': 'operador',
            'descripcion': 'Rol encargado de realizar operaciones básicas del sistema, incluyendo registro de transacciones y consultas de clientes.'
        },
        {
            'name': 'analista cambiario',
            'descripcion': 'Rol responsable del análisis de tipos de cambio, generación de reportes financieros y supervisión de operaciones cambiarias.'
        },
        {
            'name': 'administrador',
            'descripcion': 'Rol con acceso completo al sistema, incluyendo gestión de usuarios, configuración del sistema y supervisión general.'
        }
    ]
    
    for rol_data in roles_predefinidos:
        rol, created = Roles.objects.get_or_create(
            name=rol_data['name'],
            defaults={'descripcion': rol_data['descripcion']}
        )
        
        if created:
            print(f"Rol '{rol.name}' creado exitosamente.")
