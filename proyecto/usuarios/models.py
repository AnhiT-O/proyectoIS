from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class Usuario(AbstractUser):
    TIPO_CEDULA_CHOICES = [
        ('RUC', 'Registro Único de Contribuyente'),
        ('CI', 'Cédula de Identidad'),
    ]
    
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    nombre_usuario = models.CharField(max_length=30, unique=True)
    tipo_cedula = models.CharField(max_length=1, choices=TIPO_CEDULA_CHOICES)
    cedula_identidad = models.CharField(max_length=8, unique=True)
    correo_electronico = models.EmailField(unique=True)
    
    # Usar nombre_usuario como campo de autenticación
    USERNAME_FIELD = 'nombre_usuario'
    REQUIRED_FIELDS = ['correo_electronico', 'nombre', 'apellido', 'tipo_cedula', 'cedula_identidad']
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.nombre_usuario})"
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'