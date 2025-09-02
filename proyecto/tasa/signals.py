from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from .models import TasaCambio

@receiver(post_migrate)
def asignar_permisos_roles(sender, **kwargs):
    """
    Asigna los permisos necesarios a los roles de administrador y analista cambiario
    """
    # Verificar si es la app correcta
    if sender.name != 'tasa':
        return

    try:
        # Obtener el content type para TasaCambio
        content_type = ContentType.objects.get_for_model(TasaCambio)

        # Definir los permisos
        permisos = {
            'ver_tasa': 'Puede ver tasas de cambio',
            'crear_tasa': 'Puede crear tasas de cambio',
            'editar_tasa': 'Puede editar tasas de cambio',
            'activar_tasa': 'Puede activar/desactivar tasas de cambio'
        }
        
        # Crear los permisos si no existen
        for codename, name in permisos.items():
            Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=content_type
            )

        # Obtener todos los permisos creados
        todos_permisos = Permission.objects.filter(content_type=content_type)
        permisos_analista = Permission.objects.filter(
            content_type=content_type,
            codename__in=['ver_tasa', 'editar_tasa']
        )

        # Asignar permisos al grupo administrador
        grupo_admin = Group.objects.get(name='administrador')
        grupo_admin.permissions.add(*todos_permisos)
        print("✅ Permisos de tasas asignados al grupo administrador")

        # Asignar permisos al grupo analista cambiario
        grupo_analista = Group.objects.get(name='analista cambiario')
        grupo_analista.permissions.add(*permisos_analista)
        print("✅ Permisos de tasas asignados al grupo analista cambiario")

    except Group.DoesNotExist as e:
        print(f"❌ Error: Grupo no encontrado - {str(e)}")
    except Exception as e:
        print(f"❌ Error asignando permisos de tasas: {str(e)}")
        analista = Roles.objects.get(name='analista cambiario')
        administrador = Roles.objects.get(name='administrador')
        
        # Obtener el content type para el modelo TasaCambio
        content_type = ContentType.objects.get_for_model(TasaCambio)
        
        # Permisos para el analista cambiario
        permisos_analista = Permission.objects.filter(
            content_type=content_type,
            codename__in=['ver_tasa', 'editar_tasa']
        )
        analista.permissions.add(*permisos_analista)
        print("Permisos de tasa asignados al rol de analista cambiario.")
        
        # Todos los permisos para el administrador
        permisos_admin = Permission.objects.filter(
            content_type=content_type,
            codename__in=['ver_tasa', 'editar_tasa', 'crear_tasa', 'activar_tasa']
        )
        administrador.permissions.add(*permisos_admin)
        print("Permisos de tasa asignados al rol de administrador.")
        
    except Roles.DoesNotExist as e:
        print(f"Error: Rol no encontrado - {str(e)}")
    except Exception as e:
        print(f"Error al asignar permisos: {str(e)}")
