from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class Usuario(AbstractUser):
    TIPO_CEDULA_CHOICES = [
        ('RUC', 'Registro Único de Contribuyente'),
        ('CI', 'Cédula de Identidad'),
    ]
    
    tipo_cedula = models.CharField(max_length=3, choices=TIPO_CEDULA_CHOICES)
    cedula_identidad = models.CharField(max_length=8, unique=True)
    email = models.EmailField(unique=True)

    # Usar username como campo de autenticación
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name', 'tipo_cedula', 'cedula_identidad']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'