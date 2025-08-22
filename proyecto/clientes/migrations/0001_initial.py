from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, verbose_name='Nombre')),
                ('apellido', models.CharField(max_length=100, verbose_name='Apellido')),
                ('tipoDocCliente', models.CharField(choices=[('CI', 'Cédula de Identidad'), ('RUC', 'Registro Único de Contribuyente')], max_length=3, verbose_name='Tipo de Documento')),
                ('docCliente', models.CharField(max_length=20, unique=True, verbose_name='Número de Documento')),
                ('correoElecCliente', models.EmailField(unique=True, verbose_name='Correo Electrónico')),
                ('telefono', models.CharField(max_length=20, verbose_name='Teléfono')),
                ('tipoCliente', models.CharField(choices=[('F', 'Persona Física'), ('J', 'Persona Jurídica')], max_length=1, verbose_name='Tipo de Cliente')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('usuarios', models.ManyToManyField(related_name='clientes', to='usuarios.usuario', verbose_name='Usuarios asignados')),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'db_table': 'clientes',
            },
        ),
    ]