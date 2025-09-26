from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager, Group
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.validators import UnicodeUsernameValidator

class Usuario(AbstractBaseUser, PermissionsMixin):
    TIPO_CEDULA_CHOICES = [
        ('CI', 'Cédula de Identidad'),
        ('RUC', 'Registro Único de Contribuyente')
    ]
    
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[username_validator]
    )
    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=40)
    email = models.EmailField(unique=True)

    tipo_cedula = models.CharField(
        max_length=3,
        choices=TIPO_CEDULA_CHOICES,
        null=False,
        blank=False
    )
    cedula_identidad = models.CharField(
        max_length=13,
        unique=True
    )
    cliente_activo = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_activos'
    )
    bloqueado = models.BooleanField(
        default=False,
        help_text='Indica si el usuario está bloqueado en el sistema'
    )

    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    
    def obtener_roles(self):
        """Obtiene una lista de nombres de roles a los que pertenece el usuario"""
        return list(self.groups.values_list('name', flat=True))
    
    def get_full_name(self):
        """
        Retorna el nombre completo del usuario.
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"
    
    class Meta:
        db_table = 'usuarios'
        default_permissions = []  # Deshabilita permisos predeterminados
        permissions = [
            ("bloqueo", "Puede bloquear o desbloquear usuarios"),
            ("asignacion_clientes", "Puede asignar clientes a usuarios"),
            ("asignacion_roles", "Puede asignar roles a usuarios")
        ]
