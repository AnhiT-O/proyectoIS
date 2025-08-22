from django.db import migrations, models
import django.db.models.deletion


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
                ('correoElecCliente', models.EmailField(max_length=254, unique=True, verbose_name='Correo Electrónico')),
                ('telefono', models.CharField(max_length=20, verbose_name='Teléfono')),
                ('tipoCliente', models.CharField(choices=[('F', 'Persona Física'), ('J', 'Persona Jurídica')], max_length=1, verbose_name='Tipo de Cliente')),
                ('direccion', models.TextField(blank=True, null=True, verbose_name='Domicilio')),
                ('ocupacion', models.CharField(blank=True, max_length=100, null=True, verbose_name='Ocupación')),
                ('declaracion_jurada', models.BooleanField(default=False, verbose_name='Declaración Jurada Firmada')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'db_table': 'clientes',
            },
        ),
        migrations.CreateModel(
            name='UsuarioCliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='clientes.cliente')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarios.usuario')),
            ],
            options={
                'verbose_name': 'Relación Usuario-Cliente',
                'verbose_name_plural': 'Relaciones Usuario-Cliente',
                'db_table': 'usuarios_clientes',
                'unique_together': {('usuario', 'cliente')},
            },
        ),
        migrations.AddField(
            model_name='cliente',
            name='usuarios',
            field=models.ManyToManyField(related_name='clientes_operados', through='clientes.UsuarioCliente', to='usuarios.usuario', verbose_name='Usuarios operadores'),
        ),
    ]