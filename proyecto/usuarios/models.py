from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.db import models
from django.utils import timezone
from django.contrib.auth.validators import UnicodeUsernameValidator

class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Modelo personalizado de usuario que extiende AbstractBaseUser y PermissionsMixin.
    
    Attributes:
        username (CharField): Nombre de usuario. Debe ser único. Máximo 30 caracteres. Utiliza UnicodeUsernameValidator para validación.
        first_name (CharField): Nombre del usuario. Máximo 40 caracteres.
        last_name (CharField): Apellido del usuario. Máximo 40 caracteres.
        email (EmailField): Correo electrónico del usuario. Debe ser único.
        tipo_documento (CharField): Tipo de cédula del usuario. Opciones: 'CI' (Cédula de Identidad), 'RUC' (Registro Único de Contribuyente).
        numero_documento (CharField): Número de cédula de identidad del usuario. Debe ser único. Máximo 13 caracteres.
        cliente_activo (ForeignKey): Referencia a un cliente seleccionado para operar con él. Puede ser nulo.
        bloqueado (BooleanField): Indica si el usuario está bloqueado en el sistema. Por defecto es False.
        is_active (BooleanField): Indica si el usuario activó su cuenta. Por defecto es False.
        date_joined (DateTimeField): Fecha y hora en que el usuario se creó. Por defecto es la fecha y hora en que lo hizo.

    Note:
        -   El modelo utiliza UserManager como su gestor de objetos.
        -   Se deshabilitan los permisos predeterminados de Django.
        -   Se definen permisos personalizados para bloquear/desbloquear usuarios, asignar/desasignar clientes y roles a usuarios.
    """
    tipo_documento_CHOICES = [
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

    tipo_documento = models.CharField(
        max_length=3,
        choices=tipo_documento_CHOICES,
        null=False,
        blank=False
    )
    numero_documento = models.CharField(
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
        """
        Obtiene una lista de nombres de roles a los que pertenece el usuario.

        Returns:
            Lista: Lista de nombres de los roles.
        """
        return list(self.groups.values_list('name', flat=True))
    
    def es_admin(self):
        """
        Verifica si el usuario tiene el rol de 'Administrador'.

        Returns:
            bool: True si el usuario es administrador, False en caso contrario.
        """
        return 'Administrador' in self.obtener_roles()
    
    def nombre_completo(self):
        """
        Obtiene el nombre completo del usuario.

        Returns:
            Cadena de texto: Nombre completo en el formato "Nombre Apellido".
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        """
        Retorna una representación legible del usuario.
        Returns:
            Cadena de texto: Representación del usuario en el formato "Nombre Apellido (username)".
        """
        return f"{self.first_name} {self.last_name} ({self.username})"
    
    class Meta:
        """
        Metadatos del modelo Usuario.

        Attributes:
            db_table (str): Nombre de la tabla en la base de datos.
            default_permissions (list): Lista de permisos predeterminados deshabilitados.
            permissions (list): Lista de permisos personalizados para el modelo.
        """
        db_table = 'usuarios'
        default_permissions = []  # Deshabilita permisos predeterminados
        permissions = [
            ("bloqueo", "Puede bloquear o desbloquear usuarios"),
            ("asignacion_clientes", "Puede asignar clientes a usuarios"),
            ("asignacion_roles", "Puede asignar roles a usuarios")
        ]
