from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0001_initial'),
        ('clientes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UsuarioCliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('cliente', models.ForeignKey(on_delete=models.deletion.CASCADE, to='clientes.cliente')),
                ('usuario', models.ForeignKey(on_delete=models.deletion.CASCADE, to='usuarios.usuario')),
            ],
            options={
                'verbose_name': 'Relación Usuario-Cliente',
                'verbose_name_plural': 'Relaciones Usuario-Cliente',
                'db_table': 'usuarios_clientes',
                'unique_together': {('usuario', 'cliente')},
            },
        ),
    ]