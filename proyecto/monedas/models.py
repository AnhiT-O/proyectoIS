from django.db import models
from django.forms import ValidationError

class Moneda(models.Model):
    nombre = models.CharField(
        max_length=100,
        unique=True,
        blank=False,
        null=False,
        error_messages={
            'unique': 'Ya existe una moneda con este nombre.'
        },
        verbose_name='Nombre de la moneda'
    )
    simbolo = models.CharField(
        max_length=3,
        unique=True,
        blank=False,
        null=False,
        error_messages={
            'unique': 'Ya existe una moneda con este símbolo.',
            'max_length': 'El símbolo de la moneda no puede tener más de 3 caracteres.'
        },
        verbose_name='Símbolo de la moneda'
    )
    activa = models.BooleanField(
        default=True,
        verbose_name='Moneda activa',
        help_text='Determina si la moneda está activa para operaciones'
    )

    class Meta:
        verbose_name = 'Moneda'
        verbose_name_plural = 'Monedas'
        default_permissions = []  # Deshabilita permisos predeterminados
        permissions = [
            ("crear", "Puede crear monedas"),
            ("editar", "Puede editar monedas"),
            ("activacion", "Puede activar/desactivar monedas")
        ]

    def clean(self):
        super().clean()
        if self.simbolo and not self.simbolo.isupper():
            raise ValidationError({'simbolo': 'El símbolo debe contener solo letras en mayúsculas.'})

    def __str__(self):
        return self.nombre
