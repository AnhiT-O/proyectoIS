from django.db import models
from django.core.exceptions import ValidationError
from usuarios.models import Usuario

class Cliente(models.Model):
    TIPO_CLIENTE_CHOICES = [
        ('F', 'Persona Física'),
        ('J', 'Persona Jurídica'),
    ]
    TIPO_DOCUMENTO_CHOICES = [
        ('CI', 'Cédula de Identidad'),
        ('RUC', 'Registro Único de Contribuyente'),
    ]
    
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    tipoDocCliente = models.CharField(
        max_length=3,
        choices=TIPO_DOCUMENTO_CHOICES
    )
    docCliente = models.CharField(
        max_length=20,
        unique=True
    )
    correoElecCliente = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)
    tipoCliente = models.CharField(
        max_length=1,
        choices=TIPO_CLIENTE_CHOICES
    )
    direccion = models.TextField(max_length=100)
    ocupacion = models.CharField(max_length=30)
    declaracion_jurada = models.BooleanField(default=False)
    usuarios = models.ManyToManyField(
        'usuarios.Usuario',
        through='UsuarioCliente',
        related_name='clientes_operados',
        verbose_name='Usuarios operadores'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Validaciones del modelo
        """
        super().clean()
        
        # Validar coherencia entre tipo de cliente y tipo de documento
        if self.tipoCliente and self.tipoDocCliente:
            if self.tipoCliente == 'J' and self.tipoDocCliente != 'RUC':
                raise ValidationError({
                    'tipoDocCliente': 'Las personas jurídicas deben usar RUC'
                })

    def save(self, *args, **kwargs):
        """
        Sobrescribir save para ejecutar validaciones
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
        
    class Meta:
        db_table = 'clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        default_permissions = []  # Deshabilita permisos predeterminados
        permissions = [
            ("gestion", "Puede gestionar clientes (crear y editar)")
        ]

class UsuarioCliente(models.Model):
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE)
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usuarios_clientes'
        unique_together = ['usuario', 'cliente']
        verbose_name = 'Relación Usuario-Cliente'
        verbose_name_plural = 'Relaciones Usuario-Cliente'
        default_permissions = []  # Deshabilita permisos predeterminados

    def __str__(self):
        return f"{self.usuario.email} - {self.cliente.nombre}"