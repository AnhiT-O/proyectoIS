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
    
    MONEDA_CHOICES = [
        ('PYG', 'Guaraníes'),
        ('USD', 'Dólares'),
    ]
    
    TIPO_BILLETERA_CHOICES = [
        ('tigo_money', 'Tigo Money'),
        ('billetera_personal', 'Billetera Personal'),
    ]

    tipo = models.CharField(
        max_length=25,
        choices=TIPO_MEDIO_CHOICES,
        verbose_name='Tipo de Medio de Pago'
    )
    
    # Campos específicos para tarjeta de crédito 'TC'
    moneda_tc = models.CharField(
        max_length=3,
        choices=MONEDA_CHOICES,
        blank=True,
        null=True,
        verbose_name='Moneda para Tarjeta de Crédito',
        help_text='Solo aplicable para tarjetas de crédito. Debe ser PYG o USD'
    )
    
    # Campos adicionales para tarjeta de crédito (cuando un usuario la agrega)
    numero_tarjeta = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Número de Tarjeta',
        help_text='Número de la tarjeta de crédito (16 dígitos)'
    )
    cvv_tarjeta = models.CharField(
        max_length=3,
        blank=True,
        null=True,
        verbose_name='CVV',
        help_text='Código de verificación de la tarjeta (3 dígitos)'
    )
    nombre_titular_tarjeta = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Nombre del Titular de la Tarjeta',
        help_text='Nombre completo del titular como aparece en la tarjeta'
    )
    fecha_vencimiento_tc = models.DateField(
        blank=True,
        null=True,
        verbose_name='Fecha de Vencimiento',
        help_text='Fecha de vencimiento de la tarjeta de crédito'
    )
    descripcion_tarjeta = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Descripción de la Tarjeta',
        help_text='Descripción breve para identificar la tarjeta (ej: "Tarjeta personal", "Tarjeta de empresa")'
    )
    
    # Campos específicos para billeteras electrónicas
    tipo_billetera = models.CharField(
        max_length=25,
        choices=TIPO_BILLETERA_CHOICES,
        blank=True,
        null=True,
        verbose_name='Tipo de Billetera Electrónica'
    )
    numero_billetera = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Número de Billetera Electrónica'
    )
    
    # Campos específicos para cuentas bancarias (transferencias)
    cuenta_destino = models.CharField(
        max_length=3,
        blank=True,
        null=True,
        verbose_name='Cuenta de Destino',
        help_text='Cuenta bancaria donde se acreditarán los pagos con tarjeta'
    )
    numero_cuenta = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Número de Cuenta'
    )
    
    # Campos adicionales para cuenta bancaria (cuando un usuario la agrega)
    banco = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Banco',
        help_text='Nombre del banco donde está la cuenta'
    )
    cedula_ruc_cuenta = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Cédula o RUC',
        help_text='Cédula de identidad o RUC asociado a la cuenta bancaria'
    )
    nombre_titular_cuenta = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Nombre del Titular de la Cuenta',
        help_text='Nombre completo del titular de la cuenta bancaria'
    )
    tipo_cuenta = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Tipo de Cuenta',
        help_text='Tipo de cuenta bancaria (corriente, ahorro, etc.)'
    )
    
    # Relaciones many-to-many
    clientes = models.ManyToManyField(
        'clientes.Cliente',
        related_name='medios_pago',
        verbose_name='Clientes',
        help_text='Clientes que pueden usar este medio de pago'
    )
    monedas = models.ManyToManyField(
        'monedas.Moneda',
        related_name='medios_pago',
        verbose_name='Monedas',
        help_text='Monedas soportadas por este medio de pago'
    )
    
    # Campos específicos para cheques
    solo_compra_extranjera = models.BooleanField(
        default=False,
        verbose_name='Solo para Compra Extranjera',
        help_text='Determina si este medio de pago solo puede usarse para compras extranjeras'
    )
    moneda_cheque = models.CharField(
        max_length=3,
        choices=MONEDA_CHOICES,
        blank=True,
        null=True,
        verbose_name='Moneda del Cheque',
        help_text='Moneda en la que debe estar emitido el cheque'
    )
    
    # Campos de estado y auditoría
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Determina si este medio de pago está activo y disponible para usar'
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Eliminado',
        help_text='Indica si este medio de pago fue eliminado lógicamente'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        #Sobrescribir save para ejecutar validaciones
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        """
        Validaciones personalizadas para el modelo
        """
        from django.core.exceptions import ValidationError
        
        # Validar campos específicos de tarjeta de crédito
        if self.tipo == 'tarjeta_credito':
            if self.numero_tarjeta and len(self.numero_tarjeta) != 16:
                raise ValidationError({
                    'numero_tarjeta': 'El número de tarjeta debe tener exactamente 16 dígitos'
                })
            if self.cvv_tarjeta and len(self.cvv_tarjeta) != 3:
                raise ValidationError({
                    'cvv_tarjeta': 'El CVV debe tener exactamente 3 dígitos'
                })
            if self.cvv_tarjeta and not self.cvv_tarjeta.isdigit():
                raise ValidationError({
                    'cvv_tarjeta': 'El CVV debe contener solo números'
                })
            if self.numero_tarjeta and not self.numero_tarjeta.isdigit():
                raise ValidationError({
                    'numero_tarjeta': 'El número de tarjeta debe contener solo números'
                })
            
            # Validar límite de tarjetas por cliente si se están configurando datos
            if self.numero_tarjeta and self.pk:  # Solo si ya existe el objeto
                cliente_tarjetas = self.clientes.first()
                if cliente_tarjetas:
                    tarjetas_configuradas = MedioPago.objects.filter(
                        tipo='tarjeta_credito',
                        clientes=cliente_tarjetas,
                        numero_tarjeta__isnull=False
                    ).exclude(pk=self.pk).count()
                    
                    if tarjetas_configuradas >= 3:
                        raise ValidationError({
                            'numero_tarjeta': 'Un cliente no puede tener más de 3 tarjetas de crédito configuradas'
                        })
        
        # Validar campos específicos de transferencia bancaria
        if self.tipo == 'transferencia':
            if self.cedula_ruc_cuenta and len(self.cedula_ruc_cuenta) < 6:
                raise ValidationError({
                    'cedula_ruc_cuenta': 'La cédula o RUC debe tener al menos 6 caracteres'
                })
        
        super().clean()

    def __str__(self):
        return f"{self.get_tipo_display()}"
    
    def get_descripcion_completa(self):
        """Retorna una descripción detallada del medio de pago para mostrar en el frontend"""
        if self.tipo == 'tarjeta_credito' and self.numero_tarjeta:
            descripcion = self.descripcion_tarjeta or f"Tarjeta terminada en ****{self.numero_tarjeta[-4:]}"
            return descripcion
        elif self.tipo == 'transferencia' and self.numero_cuenta:
            banco_info = f" - {self.banco}" if self.banco else ""
            return f"Cuenta {self.numero_cuenta}{banco_info}"
        elif self.tipo == 'billetera_electronica' and self.numero_billetera:
            tipo_billetera = self.get_tipo_billetera_display() if self.tipo_billetera else "Billetera"
            return f"{tipo_billetera} - {self.numero_billetera}"
        else:
            return self.get_tipo_display()
    
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
    
    @property
    def tarjeta_credito_completa(self):
        """Retorna True si la tarjeta de crédito tiene todos los datos necesarios"""
        if self.tipo != 'tarjeta_credito':
            return False
        return all([
            self.numero_tarjeta,
            self.cvv_tarjeta,
            self.nombre_titular_tarjeta,
            self.fecha_vencimiento_tc,
            self.descripcion_tarjeta
        ])
    
    @property
    def cuenta_bancaria_completa(self):
        """Retorna True si la cuenta bancaria tiene todos los datos necesarios"""
        if self.tipo != 'transferencia':
            return False
        return all([
            self.numero_cuenta,
            self.banco,
            self.nombre_titular_cuenta,
            self.tipo_cuenta
        ])
    
    @property
    def puede_procesar_transacciones(self):
        """Retorna True si el medio de pago puede procesar transacciones"""
        if self.tipo in ['efectivo', 'cheque', 'billetera_electronica']:
            return True
        elif self.tipo == 'tarjeta_credito':
            return self.tarjeta_credito_completa
        elif self.tipo == 'transferencia':
            return self.cuenta_bancaria_completa
        return False

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
            if not MedioPago.objects.filter(tipo=medio_data['tipo']).exists():
                # Crear el medio de pago
                medio_pago = MedioPago.objects.create(
                    tipo=medio_data['tipo']
                )
                
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


@receiver(post_migrate)
def asociar_medios_pago_basicos_a_todos_los_clientes(sender, **kwargs):
    """
    Asocia automáticamente los medios de pago básicos ('efectivo', 'cheque', 'billetera_electronica', 'transferencia') 
    a todos los clientes existentes
    """
    # Solo ejecutar si la migración es de la app medios_pago o clientes
    if kwargs['app_config'].name in ['medios_pago', 'clientes']:
        try:
            # Importar Cliente aquí para evitar problemas de importación circular
            from clientes.models import Cliente
            
            # Definir los medios de pago básicos que se asocian automáticamente
            medios_basicos = ['efectivo', 'cheque', 'billetera_electronica', 'transferencia']
            
            for tipo_medio in medios_basicos:
                try:
                    # Buscar el medio de pago
                    medio_pago = MedioPago.objects.get(tipo=tipo_medio)
                    
                    # Obtener todos los clientes que no tienen este medio asociado
                    clientes_sin_medio = Cliente.objects.exclude(medios_pago=medio_pago)
                    
                    # Asociar el medio de pago a todos los clientes que no lo tienen
                    for cliente in clientes_sin_medio:
                        cliente.medios_pago.add(medio_pago)
                        print(f"✓ {medio_pago.get_tipo_display()} asociado automáticamente al cliente {cliente.nombre}")
                        
                    if clientes_sin_medio.count() == 0:
                        print(f"✓ Todos los clientes ya tienen {medio_pago.get_tipo_display()} asociado")
                        
                except MedioPago.DoesNotExist:
                    print(f"⚠ Medio de pago {tipo_medio} no encontrado para asociar a clientes")
                
        except Exception as e:
            print(f"⚠ Error al asociar medios de pago básicos: {e}")


@receiver(post_save, sender='clientes.Cliente')
def asociar_medios_pago_basicos_a_nuevo_cliente(sender, instance, created, **kwargs):
    """
    Cuando se crea un nuevo cliente, automáticamente le asocia los medios de pago básicos
    ('efectivo', 'cheque', 'billetera_electronica', 'transferencia')
    """
    if created:
        # Definir los medios de pago básicos que se asocian automáticamente
        medios_basicos = ['efectivo', 'cheque', 'billetera_electronica', 'transferencia']
        
        for tipo_medio in medios_basicos:
            try:
                # Buscar el medio de pago
                medio_pago = MedioPago.objects.get(tipo=tipo_medio)
                # Asociar el medio al nuevo cliente
                instance.medios_pago.add(medio_pago)
                print(f"✓ {medio_pago.get_tipo_display()} asociado automáticamente al nuevo cliente {instance.nombre}")
            except MedioPago.DoesNotExist:
                print(f"⚠ Medio de pago {tipo_medio} no encontrado para asociar al nuevo cliente")
