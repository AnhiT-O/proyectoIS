from django.db import migrations

def create_predefined_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='analista cambiario')
    Group.objects.get_or_create(name='administrador')

class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0006_crear_grupos_predefinidos'),
        ('auth', '__first__'),  # Esto asegura que todas las migraciones de auth se ejecuten primero
    ]

    operations = [
        migrations.RunPython(create_predefined_roles),
    ]