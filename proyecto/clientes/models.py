from django.db import models
from usuarios.models import Usuario

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)
    direccion = models.TextField(blank=True, null=True)
    usuarios = models.ManyToManyField(
        Usuario,
        related_name='clientes',
        verbose_name='Usuarios asignados'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
        
    class Meta:
        db_table = 'clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'