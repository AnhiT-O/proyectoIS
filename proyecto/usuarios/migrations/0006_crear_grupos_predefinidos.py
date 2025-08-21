from django.db import migrations

def crear_grupos_predefinidos(apps, schema_editor):
    # Obtenemos el modelo Group
    Group = apps.get_model('auth', 'Group')
    
    # Creamos los grupos si no existen
    Group.objects.get_or_create(name='administrador')
    Group.objects.get_or_create(name='analista cambiario')

def eliminar_grupos_predefinidos(apps, schema_editor):
    # Obtenemos el modelo Group
    Group = apps.get_model('auth', 'Group')
    
    # Eliminamos los grupos
    Group.objects.filter(name='analista cambiario').delete()
    Group.objects.filter(name='administrador').delete()

class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0005_alter_usuario_cedula_identidad_alter_usuario_email_and_more'),
    ]

    operations = [
        migrations.RunPython(crear_grupos_predefinidos, eliminar_grupos_predefinidos),
    ]
