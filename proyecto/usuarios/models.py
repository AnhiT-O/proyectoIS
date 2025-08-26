from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager, Group
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MinLengthValidator, RegexValidator

class Usuario(AbstractBaseUser, PermissionsMixin):
    TIPO_CEDULA_CHOICES = [
        ('RUC', 'Registro Único de Contribuyente'),
        ('CI', 'Cédula de Identidad'),
    ]
    
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        max_length=30,
        unique=True,
        help_text='Requerido. 150 caracteres o menos. Letras, dígitos y @/./+/-/_ solamente.',
        validators=[username_validator],
        error_messages={
            'unique': "Un usuario con ese nombre de usuario ya existe.",
            'invalid': "El nombre de usuario solo puede contener letras, dígitos y @/./+/-/_.", 
            'max_length': "El nombre de usuario no puede exceder los 30 caracteres."
        }
    )
    first_name = models.CharField(
        max_length=40, 
        null=False, 
        blank=False
    )
    last_name = models.CharField(
        max_length=40, 
        null=False, 
        blank=False
    )
    email = models.EmailField(
        null=False, 
        blank=False
    )

    tipo_cedula = models.CharField(
        max_length=3,
        choices=TIPO_CEDULA_CHOICES,
        null=False,
        blank=False
    )
    cedula_identidad = models.CharField(
        max_length=11,
        null=False,
        blank=False,
        validators=[
            MinLengthValidator(4, "La cédula de identidad debe tener al menos 4 caracteres."),
            RegexValidator(r'^\d+$', 'La cédula de identidad solo puede contener dígitos.')
        ],
        error_messages={
            'max_length': "La cédula de identidad no puede exceder los 11 caracteres."
        }
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
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name', 'tipo_cedula', 'cedula_identidad']

    def esta_bloqueado(self):
        """Método para verificar si el usuario está bloqueado"""
        return self.bloqueado

    def es_administrador(self):
        """Verifica si el usuario pertenece al rol de administrador"""
        return self.groups.filter(name='administrador').exists()
    
    def es_analista_cambiario(self):
        """Verifica si el usuario pertenece al rol de analista cambiario"""
        return self.groups.filter(name='analista cambiario').exists()
    
    def es_operador(self):
        """Verifica si el usuario pertenece al rol de operador"""
        return self.groups.filter(name='operador').exists()
    
    def obtener_roles(self):
        """Obtiene una lista de nombres de roles a los que pertenece el usuario"""
        return list(self.groups.values_list('name', flat=True))
    
    def get_full_name(self):
        """
        Retorna el nombre completo del usuario.
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username

    def save(self, *args, **kwargs):
        """Sobrescribe el método save para asignar rol por defecto"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and self.groups.count() == 0:
            try:
                from django.contrib.auth.models import Group
                operador_role = Group.objects.get(name='operador')
                self.groups.add(operador_role)
            except Group.DoesNotExist:
                pass  # Si no existe el rol, no hacer nada

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        default_permissions = []  # Deshabilita permisos predeterminados
        permissions = [
            ("bloqueo", "Puede bloquear o desbloquear usuarios"),
            ("asignacion_clientes", "Puede asignar clientes a usuarios"),
            ("asignacion_roles", "Puede asignar roles a usuarios")
        ]
