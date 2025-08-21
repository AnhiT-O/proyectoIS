from django.db import migrations

def create_predefined_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='analista cambiario')
    Group.objects.get_or_create(name='administrador')

class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),  # Cambia 'tu_app' y '0001_initial' según corresponda
        ('auth', '0012_alter_user_first_name_max_length'),  # Asegúrate de que la dependencia de auth sea correcta
    ]

    operations = [
        migrations.RunPython(create_predefined_roles),
    ]