from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

class Usuario(AbstractUser):
    TIPO_CEDULA_CHOICES = [
        ('RUC', 'Registro Único de Contribuyente'),
        ('CI', 'Cédula de Identidad'),
    ]
    
    # Hacer campos obligatorios heredados de AbstractUser
    first_name = models.CharField(
        max_length=70, 
        null=False, 
        blank=False
    )
    last_name = models.CharField(
        max_length=70, 
        null=False, 
        blank=False
    )
    email = models.EmailField(
        null=False, 
        blank=False
    )
    
    # Campos adicionales
    tipo_cedula = models.CharField(
        max_length=3,
        choices=TIPO_CEDULA_CHOICES,
        null=False,
        blank=False
    )
    cedula_identidad = models.CharField(
        max_length=14,
        null=False,
        blank=False
    )
    cliente_activo = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_activos'
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name', 'tipo_cedula', 'cedula_identidad']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'