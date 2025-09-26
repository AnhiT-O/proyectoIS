from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

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

class Transaccion(models.Model):
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10)  # 'compra' o 'venta'
    moneda = models.ForeignKey('monedas.Moneda', on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=30, decimal_places=8)
    medio_pago = models.CharField(max_length=50) 
    medio_cobro = models.CharField(max_length=100, default='')  # Agregar campo medio_cobro 
    fecha_hora = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='Pendiente')
    token = models.CharField(max_length=255, blank=True, null=True)  # Campo para el token
    token_expiracion = models.DateTimeField(blank=True, null=True)  # Campo para la expiración del token
    
    class Meta:
        verbose_name = "Transacción"
        verbose_name_plural = "Transacciones"
        db_table = "transacciones"
        default_permissions = []
        permissions = []  # De momento no hay permisos necesarios
    
    def __str__(self):
        return f"{self.tipo.title()} - {self.cliente} - {self.monto} {self.moneda.simbolo}"
    
    def token_valido(self):
        """
        Verifica si el token aún es válido (no ha expirado)
        """
        if not self.token or not self.token_expiracion:
            return False
        return timezone.now() < self.token_expiracion
    
    def establecer_token_con_expiracion(self, token):
        """
        Establece el token y su tiempo de expiración (5 minutos)
        """
        self.token = token
        self.token_expiracion = timezone.now() + timedelta(minutes=5)
        self.save()
    
    @classmethod
    def limpiar_tokens_expirados(cls):
        """
        Elimina todas las transacciones con tokens expirados
        """
        now = timezone.now()
        transacciones_expiradas = cls.objects.filter(
            token__isnull=False,
            token_expiracion__lt=now
        )
        count = transacciones_expiradas.count()
        transacciones_expiradas.delete()
        return count
    
    def save(self, *args, **kwargs):
        """
        Actualiza la fecha_hora cuando el estado cambia
        """
        if self.pk:  # Si la instancia ya existe
            try:
                old_instance = Transaccion.objects.get(pk=self.pk)
                if old_instance.estado != self.estado:
                    self.fecha_hora = timezone.now()
            except Transaccion.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)