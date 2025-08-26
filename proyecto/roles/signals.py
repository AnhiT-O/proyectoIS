from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver

@receiver(post_migrate)
def asignar_permisos_administrador(sender, **kwargs):
    """
    Asigna todos los permisos existentes a un grupo llamado 'Administradores'.
    """

    # Obtener o crear el grupo
    admin, created = Group.objects.get_or_create(name='administrador')

    # Obtener todos los permisos
    all_permissions = Permission.objects.all()

    # Asignar los permisos al grupo
    admin.permissions.set(all_permissions)
    print(f"Al grupo 'administrador' se le han asignado todos los permisos después de migrar {sender.name}.")