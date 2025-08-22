# clientes/models.py
from django.db import models
from usuarios.models import Usuario  # tu modelo custom de usuario

class Cliente(models.Model):
    TIPO_CLIENTE = [
        ('PF', 'Persona Física'),
        ('PJ', 'Persona Jurídica'),
    ]

    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    tipo = models.CharField(max_length=2, choices=TIPO_CLIENTE)

    # Relación muchos a muchos con Usuario
    usuarios = models.ManyToManyField(
        Usuario,
        through='UsuarioCliente',   # tabla intermedia
        related_name='clientes'
    )

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"


class UsuarioCliente(models.Model):  # tabla intermedia
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha_asociacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'cliente')  # evita duplicados

    def __str__(self):
        return f"{self.usuario.username} ↔ {self.cliente.nombre}"
