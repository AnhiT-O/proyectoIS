from django.db import migrations
from django.db.migrations import Migration

def crear_rol_administrador(apps, schema_editor):
    Rol = apps.get_model('roles', 'Rol')
    Permission = apps.get_model('auth.Permission')
    
    # Verificar si el rol administrador ya existe
    if not Rol.objects.filter(id=2).exists():
        rol_admin = Rol.objects.create(
            id=2,
            nombre='Administrador',
            descripcion='Rol con acceso total al sistema',
            activo=True
        )
        # Asignar todos los permisos disponibles
        permisos = Permission.objects.all()
        rol_admin.permisos.set(permisos)

def revertir_rol_administrador(apps, schema_editor):
    Rol = apps.get_model('roles', 'Rol')
    Rol.objects.filter(id=2).delete()

class Migration(Migration):
    dependencies = [
        ('roles', '0001_initial'),
        ('auth', '__latest__'),
    ]

    operations = [
        migrations.RunPython(
            crear_rol_administrador,
            revertir_rol_administrador
        ),
    ]
