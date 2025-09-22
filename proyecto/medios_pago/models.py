from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver


class MedioPago(models.Model):
    TIPO_MEDIO_CHOICES = [
        ('tarjeta_credito', 'Tarjeta de Crédito'),
        ('transferencia', 'Transferencia'),
        ('efectivo', 'Efectivo'),
        ('billetera_electronica', 'Billetera Electrónica'),
        ('cheque', 'Cheque'),
    ]

    tipo = models.CharField(
        max_length=25,
        choices=TIPO_MEDIO_CHOICES,
        unique=True,
        verbose_name='Tipo de Medio de Pago'
    )
    
    # Relación many-to-many directa con monedas (sigue igual)
    monedas = models.ManyToManyField(
        'monedas.Moneda',
        related_name='medios_pago',
        verbose_name='Monedas',
        help_text='Monedas soportadas por este medio de pago'
    )

    
    # Campos de estado y auditoría
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Determina si este medio de pago está activo y disponible para usar'
    )

    def __str__(self):
        return f"{self.get_tipo_display()}"
    
    @property
    def es_efectivo(self):
        """Retorna True si el medio de pago es efectivo"""
        return self.tipo == 'efectivo'
    
    @property
    def permite_moneda_extranjera(self):
        """Retorna True si el medio de pago permite operaciones en moneda extranjera"""
        return self.tipo in ['efectivo', 'cheque']
    
    @property
    def requiere_tauser(self):
        """Retorna True si el medio de pago requiere un tauser para procesar"""
        return self.tipo == 'efectivo'

    class Meta:
        db_table = 'medios_pago'
        verbose_name = 'Medio de Pago'
        verbose_name_plural = 'Medios de Pago'
        default_permissions = []  # Deshabilita permisos predeterminados
        ordering = ['tipo']

@receiver(post_migrate)
def crear_medios_pago_iniciales(sender, **kwargs):
    """
    Crea automáticamente los 5 medios de pago después de ejecutar las migraciones
    """
    # Solo crear si la migración es de la app medios_pago
    if kwargs['app_config'].name == 'medios_pago':
        # Importar Moneda aquí para evitar problemas de importación circular
        from monedas.models import Moneda
        
        # Definir los medios de pago a crear
        medios_pago_data = [
            {
                'nombre': 'Efectivo',
                'tipo': 'efectivo',
                'relacionar_todas_monedas': True
            },
            {
                'nombre': 'Transferencia Bancaria',
                'tipo': 'transferencia',
                'relacionar_todas_monedas': False
            },
            {
                'nombre': 'Tarjeta de Crédito',
                'tipo': 'tarjeta_credito',
                'relacionar_todas_monedas': False,
                'monedas_especificas': ['USD']
            },
            {
                'nombre': 'Billetera Electrónica',
                'tipo': 'billetera_electronica',
                'relacionar_todas_monedas': False
            },
            {
                'nombre': 'Cheque',
                'tipo': 'cheque',
                'relacionar_todas_monedas': False
            }
        ]
        
        for medio_data in medios_pago_data:
            # Verificar si ya existe el medio de pago
            medio_pago, created = MedioPago.objects.get_or_create(
                tipo=medio_data['tipo'],
                defaults={'activo': True}
            )
            
            if created:
                # Relacionar con monedas según las reglas
                if medio_data.get('relacionar_todas_monedas', False):
                    # Relacionar con todas las monedas existentes
                    todas_monedas = Moneda.objects.all()
                    medio_pago.monedas.set(todas_monedas)
                    print(f"✓ {medio_data['nombre']} creado y relacionado con todas las monedas")
                elif medio_data.get('monedas_especificas'):
                    # Relacionar con monedas específicas
                    for simbolo_moneda in medio_data['monedas_especificas']:
                        try:
                            moneda = Moneda.objects.get(simbolo=simbolo_moneda)
                            medio_pago.monedas.add(moneda)
                            print(f"✓ {medio_data['nombre']} creado y relacionado con {simbolo_moneda}")
                        except Moneda.DoesNotExist:
                            print(f"⚠ Moneda {simbolo_moneda} no encontrada para {medio_data['nombre']}")
                else:
                    print(f"✓ {medio_data['nombre']} creado sin relaciones con monedas")


@receiver(post_save, sender='monedas.Moneda')
def relacionar_nueva_moneda_con_efectivo(sender, instance, created, **kwargs):
    """
    Cuando se crea una nueva moneda, automáticamente la relaciona con el medio de pago 'efectivo'
    """
    if created:
        try:
            # Buscar el medio de pago efectivo
            medio_efectivo = MedioPago.objects.get(tipo='efectivo')
            # Relacionar la nueva moneda con efectivo
            medio_efectivo.monedas.add(instance)
            print(f"✓ Nueva moneda {instance.simbolo} relacionada automáticamente con Efectivo")
        except MedioPago.DoesNotExist:
            print("⚠ Medio de pago Efectivo no encontrado para relacionar con nueva moneda")