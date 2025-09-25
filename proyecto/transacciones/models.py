from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class Recargos(models.Model):
    nombre = models.CharField(max_length=50)
    recargo = models.SmallIntegerField(default=0)

    class Meta:
        verbose_name = "Recargo"
        verbose_name_plural = "Recargos"
        db_table = "recargos"
        default_permissions = []  # Deshabilita permisos predeterminados
        permissions = [
            ('edicion', 'Puede editar recargos'),
        ]

    def __str__(self):
        return self.nombre

@receiver(post_migrate)
def crear_recargos(sender, **kwargs):
    """
    Crea automáticamente los recargos después de ejecutar las migraciones
    """
    # Solo crear si la migración es de la app transacciones
    if kwargs['app_config'].name == 'transacciones':

        if not Recargos.objects.filter(nombre='Tarjeta de Crédito').exists():
            Recargos.objects.create(
                nombre='Tarjeta de Crédito',
                recargo=1
            )

        if not Recargos.objects.filter(nombre='Tigo Money').exists():
            Recargos.objects.create(
                nombre='Tigo Money',
                recargo=2
            )

        if not Recargos.objects.filter(nombre='Billetera Personal').exists():
            Recargos.objects.create(
                nombre='Billetera Personal',
                recargo=2
            )

        if not Recargos.objects.filter(nombre='Zimple').exists():
            Recargos.objects.create(
                nombre='Zimple',
                recargo=3
            )