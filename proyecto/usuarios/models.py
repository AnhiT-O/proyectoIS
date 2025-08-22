from django.contrib.auth.models import AbstractUser, Group
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
    bloqueado = models.BooleanField(
        default=False,
        help_text='Indica si el usuario está bloqueado en el sistema'
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name', 'tipo_cedula', 'cedula_identidad']

    def esta_bloqueado(self):
        """Método para verificar si el usuario está bloqueado"""
        return self.bloqueado
    
    def asignar_grupo(self, nombre_grupo):
        """Asigna el usuario a un grupo específico"""
        try:
            grupo = Group.objects.get(name=nombre_grupo)
            self.groups.add(grupo)
            return True
        except Group.DoesNotExist:
            raise ValidationError(f"El grupo '{nombre_grupo}' no existe")
    
    def remover_grupo(self, nombre_grupo):
        """Remueve el usuario de un grupo específico"""
        try:
            grupo = Group.objects.get(name=nombre_grupo)
            self.groups.remove(grupo)
            return True
        except Group.DoesNotExist:
            raise ValidationError(f"El grupo '{nombre_grupo}' no existe")
    
    def es_administrador(self):
        """Verifica si el usuario pertenece al grupo de administradores"""
        return self.groups.filter(name='administrador').exists()
    
    def es_analista_cambiario(self):
        """Verifica si el usuario pertenece al grupo de analistas cambiarios"""
        return self.groups.filter(name='analista cambiario').exists()
    
    def es_operador(self):
        """Verifica si el usuario pertenece al grupo de operadores"""
        return self.groups.filter(name='operador').exists()
    
    def obtener_grupos(self):
        """Obtiene una lista de nombres de grupos a los que pertenece el usuario"""
        return list(self.groups.values_list('name', flat=True))
    
    def asignar_grupo_por_defecto(self):
        """Asigna un grupo por defecto al usuario (operador)"""
        if not self.groups.exists():
            self.asignar_grupo('operador')
    
    def save(self, *args, **kwargs):
        """Sobrescribe el método save para asignar grupo por defecto"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Si es un usuario nuevo y no es superusuario, asignar grupo por defecto
        if is_new and not self.is_superuser:
            self.asignar_grupo_por_defecto()
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'