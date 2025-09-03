from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver

@receiver(post_migrate)
def asignar_permisos_administrador(sender, **kwargs):
    """
    Asigna todos los permisos existentes a un grupo llamado 'Administradores'.
    """

    # Obtener o crear el grupo
    admin = Group.objects.get_or_create(name='Administrador')[0]

    # Obtener todos los permisos
    all_permissions = Permission.objects.all()

    # Asignar los permisos al grupo
    admin.permissions.set(all_permissions)
    print(f"Al grupo 'Administrador' se le han asignado todos los permisos del modelo {sender.name}.")