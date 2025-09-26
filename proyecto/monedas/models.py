from django.db import models
from django.forms import ValidationError
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone
from datetime import date


class Moneda(models.Model):
    """
    Modelo que representa una moneda en el sistema de casa de cambio.
    
    Permite gestionar diferentes monedas con sus respectivas tasas de cambio,
    comisiones y stock disponible. Incluye funcionalidad para calcular precios
    de compra y venta aplicando beneficios específicos de clientes.
    
    Attributes:
        nombre (str): Nombre completo de la moneda (ej: "Dólar estadounidense")
        simbolo (str): Código de 3 letras de la moneda (ej: "USD")
        activa (bool): Indica si la moneda está disponible para transacciones
        tasa_base (int): Tasa base de cambio respecto al guaraní
        comision_compra (int): Comisión aplicada en operaciones de compra
        comision_venta (int): Comisión aplicada en operaciones de venta
        decimales (int): Número de decimales permitidos para esta moneda
        fecha_cotizacion (datetime): Fecha de la última actualización de cotización
        stock (int): Cantidad disponible en stock de la moneda
    """
    nombre = models.CharField(
        max_length=30,
        unique=True,
        blank=False,
        null=False
    )
    simbolo = models.CharField(
        max_length=3,
        unique=True,
        blank=False,
        null=False
    )
    activa = models.BooleanField(default=True)
    tasa_base = models.IntegerField(default=0)
    comision_compra = models.IntegerField(default=0)
    comision_venta = models.IntegerField(default=0)
    decimales = models.SmallIntegerField(default=3)
    fecha_cotizacion = models.DateTimeField(auto_now=True)
    stock = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para actualizar automáticamente la fecha
        de cotización cuando se modifican las tasas o comisiones.
        
        Args:
            *args: Argumentos posicionales
            **kwargs: Argumentos con nombre
        """
        # Si la moneda ya existe, verificar si cambiaron los campos de cotización
        if self.pk:
            old = Moneda.objects.get(pk=self.pk)
            if (
                self.tasa_base != old.tasa_base or
                self.comision_compra != old.comision_compra or
                self.comision_venta != old.comision_venta
            ):
                # Actualizar la fecha de cotización si cambiaron las tasas o comisiones
                self.fecha_cotizacion = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        """
        Metadatos del modelo Moneda.
        
        Define permisos personalizados para la gestión de monedas,
        deshabilitando los permisos predeterminados de Django.
        """
        verbose_name = 'Moneda'
        verbose_name_plural = 'Monedas'
        db_table = 'monedas'
        default_permissions = []  # Deshabilita permisos predeterminados
        permissions = [
            ("gestion", "Puede gestionar monedas (crear y editar)"),
            ("activacion", "Puede activar/desactivar monedas"),
            ("cotizacion", "Puede actualizar cotización de monedas")
        ]

    def calcular_precio_venta(self, porcentaje_beneficio=0):
        """
        Calcula el precio de venta aplicando el beneficio del cliente.
        
        El precio se calcula como: tasa_base + comision_venta - (comision_venta * beneficio)
        Esto significa que el beneficio reduce la comisión que paga el cliente.
        
        Args:
            porcentaje_beneficio (float): Porcentaje de beneficio del cliente (0-100)
            
        Returns:
            int: Precio de venta calculado en guaraníes por unidad de moneda extranjera
            
        Example:
            Para USD con tasa_base=7400, comision_venta=250 y beneficio=10%:
            precio_venta = 7400 + 250 - (250 * 0.10) = 7625
        """
        tasa_base = self.tasa_base
        comision_venta = self.comision_venta
        beneficio = porcentaje_beneficio / 100
        
        precio = int(tasa_base + comision_venta - (comision_venta * beneficio))
        return precio

    def calcular_precio_compra(self, porcentaje_beneficio=0):
        """
        Calcula el precio de compra aplicando el beneficio del cliente.
        
        El precio se calcula como: tasa_base - comision_compra + (comision_compra * beneficio)
        El beneficio aumenta el precio que la casa de cambio paga al cliente.
        
        Args:
            porcentaje_beneficio (float): Porcentaje de beneficio del cliente (0-100)
            
        Returns:
            int: Precio de compra calculado en guaraníes por unidad de moneda extranjera
            
        Example:
            Para USD con tasa_base=7400, comision_compra=200 y beneficio=10%:
            precio_compra = 7400 - 200 + (200 * 0.10) = 7220
        """
        tasa_base = self.tasa_base
        comision_compra = self.comision_compra
        beneficio = porcentaje_beneficio / 100

        precio = int(tasa_base - comision_compra + (comision_compra * beneficio))
        return precio

    def get_precios_cliente(self, cliente):
        """
        Obtiene los precios de compra y venta para un cliente específico
        aplicando su porcentaje de beneficio según su segmento.
        
        Args:
            cliente (Cliente): Instancia del cliente o None para precios sin beneficio
            
        Returns:
            dict: Diccionario con 'precio_venta' y 'precio_compra' calculados
            
        Example:
            {
                'precio_venta': 7625,
                'precio_compra': 7220
            }
        """
        # Si hay un cliente, usamos su beneficio_segmento
        porcentaje_beneficio = 0
        if cliente:
            porcentaje_beneficio = cliente.beneficio_segmento
        
        return {
            'precio_venta': self.calcular_precio_venta(porcentaje_beneficio),
            'precio_compra': self.calcular_precio_compra(porcentaje_beneficio)
        }

    def clean(self):
        """
        Validaciones personalizadas del modelo.
        
        Verifica que el símbolo de la moneda esté en mayúsculas.
        
        Raises:
            ValidationError: Si el símbolo no está en mayúsculas
        """
        super().clean()
        if self.simbolo and not self.simbolo.isupper():
            raise ValidationError({'simbolo': 'El símbolo debe contener solo letras en mayúsculas.'})

    def __str__(self):
        """
        Representación en string del modelo.
        
        Returns:
            str: Nombre de la moneda
        """
        return self.nombre


@receiver(post_migrate)
def crear_moneda_usd(sender, **kwargs):
    """
    Signal que crea automáticamente la moneda USD después de ejecutar las migraciones.
    
    Esta función se ejecuta automáticamente después de cada migración y verifica
    si ya existe la moneda USD. Si no existe, la crea con valores predeterminados
    para asegurar que el sistema tenga al menos una moneda funcional.
    
    Args:
        sender: El sender del signal (AppConfig)
        **kwargs: Argumentos del signal, incluyendo 'app_config'
        
    Note:
        Solo se ejecuta cuando la migración corresponde a la app 'monedas'
        para evitar ejecuciones innecesarias.
    """
    # Solo crear si la migración es de la app monedas
    if kwargs['app_config'].name == 'monedas':
        # Verificar si ya existe la moneda USD
        if not Moneda.objects.filter(simbolo='USD').exists():
            Moneda.objects.create(
                nombre='Dólar estadounidense',
                simbolo='USD',
                activa=True,
                tasa_base=7400,
                comision_compra=200,
                comision_venta=250,
                decimales=2,
                stock=1000000
            )
            print("✓ Moneda USD creada automáticamente")


class LimiteGlobal(models.Model):
    """
    Modelo para almacenar los límites globales de transacciones que aplican
    a todos los clientes según la normativa legal de casas de cambio.
    
    Permite configurar límites diarios y mensuales que restricen la cantidad
    máxima de dinero que un cliente puede operar en el sistema. Incluye
    funcionalidad para gestionar períodos de vigencia de los límites.
    
    Attributes:
        limite_diario (int): Límite máximo diario en guaraníes para todos los clientes
        limite_mensual (int): Límite máximo mensual en guaraníes para todos los clientes
        fecha_inicio (date): Fecha desde cuando entra en vigor este límite
        fecha_fin (date): Fecha hasta cuando está vigente (opcional)
        activo (bool): Indica si este límite está actualmente en uso
        
    Note:
        Solo puede haber un límite activo al mismo tiempo. Los límites se aplican
        a las transacciones convertidas a guaraníes para uniformizar el control.
    """
    limite_diario = models.IntegerField(
        default=90000000,
        help_text="Límite diario global en guaraníes"
    )
    limite_mensual = models.IntegerField(
        default=450000000,
        help_text="Límite mensual global en guaraníes"
    )
    fecha_inicio = models.DateField(
        default=date.today,
        help_text="Fecha desde cuando rige este límite"
    )
    fecha_fin = models.DateField(
        null=True, 
        blank=True,
        help_text="Fecha hasta cuando rige este límite (opcional)"
    )
    activo = models.BooleanField(
        default=True,
        help_text="Indica si este límite está vigente"
    )

    class Meta:
        """
        Metadatos del modelo LimiteGlobal.
        
        Define permisos específicos para la gestión de límites y
        deshabilita los permisos predeterminados de Django.
        """
        verbose_name = 'Límite Global'
        verbose_name_plural = 'Límites Globales'
        db_table = 'limite_global'
        default_permissions = []
        permissions = [
            ("gestion", "Puede gestionar límites globales"),
        ]

    def clean(self):
        """
        Validaciones personalizadas del modelo LimiteGlobal.
        
        Verifica que:
        - Los límites sean mayores a 0
        - El límite diario no sea mayor al mensual
        
        Raises:
            ValidationError: Si alguna validación falla
        """
        super().clean()
        if self.limite_diario <= 0:
            raise ValidationError({'limite_diario': 'El límite diario debe ser mayor a 0'})
        if self.limite_mensual <= 0:
            raise ValidationError({'limite_mensual': 'El límite mensual debe ser mayor a 0'})
        if self.limite_diario > self.limite_mensual:
            raise ValidationError({'limite_diario': 'El límite diario no puede ser mayor al mensual'})

    def __str__(self):
        """
        Representación en string del modelo.
        
        Returns:
            str: Descripción de los límites con formato legible
        """
        return f"Límite Diario: {self.limite_diario:,} - Mensual: {self.limite_mensual:,}"

    @classmethod
    def obtener_limite_vigente(cls):
        """
        Retorna el límite global vigente para la fecha actual.
        
        Busca el límite que esté activo y cuya fecha de inicio sea menor o igual
        a hoy, y que no tenga fecha de fin o que la fecha de fin sea mayor o igual a hoy.
        
        Returns:
            LimiteGlobal: Instancia del límite vigente o None si no hay ninguno
            
        Example:
            limite = LimiteGlobal.obtener_limite_vigente()
            if limite:
                print(f"Límite diario: {limite.limite_diario}")
        """
        hoy = date.today()
        return cls.objects.filter(
            activo=True,
            fecha_inicio__lte=hoy
        ).filter(
            models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gte=hoy)
        ).first()


class ConsumoLimiteCliente(models.Model):
    """
    Modelo para registrar el consumo acumulado de límites por cliente.
    
    Mantiene un registro del consumo diario y mensual de cada cliente,
    actualizándose con cada transacción realizada. Permite el control
    y seguimiento del cumplimiento de los límites establecidos.
    
    Este modelo se resetea automáticamente:
    - Consumo diario: Se resetea cada día
    - Consumo mensual: Se resetea cada mes
    
    Attributes:
        cliente (ForeignKey): Referencia al cliente propietario del consumo
        fecha (date): Fecha del registro de consumo (normalmente hoy)
        consumo_diario (int): Consumo acumulado del día en guaraníes
        consumo_mensual (int): Consumo acumulado del mes en guaraníes
        
    Note:
        Todos los consumos se almacenan en guaraníes independientemente
        de la moneda original de la transacción para facilitar el control.
    """
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        related_name='consumos_limite'
    )
    fecha = models.DateField(
        default=date.today,
        help_text="Fecha del registro de consumo"
    )
    consumo_diario = models.IntegerField(
        default=0,
        help_text="Consumo acumulado del día en guaraníes"
    )
    consumo_mensual = models.IntegerField(
        default=0,
        help_text="Consumo acumulado del mes en guaraníes"
    )

    class Meta:
        """
        Metadatos del modelo ConsumoLimiteCliente.
        
        Define una restricción de unicidad para evitar duplicados
        por cliente y fecha, y deshabilita permisos predeterminados.
        """
        verbose_name = 'Consumo de Límite Cliente'
        verbose_name_plural = 'Consumos de Límites Clientes'
        db_table = 'consumo_limite_cliente'
        unique_together = ['cliente', 'fecha']  # Un registro por cliente por fecha
        default_permissions = []

    def clean(self):
        """
        Validaciones personalizadas del modelo.
        
        Verifica que los consumos no sean negativos.
        
        Raises:
            ValidationError: Si algún consumo es negativo
        """
        super().clean()
        if self.consumo_diario < 0:
            raise ValidationError({'consumo_diario': 'El consumo diario no puede ser negativo'})
        if self.consumo_mensual < 0:
            raise ValidationError({'consumo_mensual': 'El consumo mensual no puede ser negativo'})

    def __str__(self):
        """
        Representación en string del modelo.
        
        Returns:
            str: Descripción del consumo con nombre del cliente, fecha y consumo diario
        """
        return f"{self.cliente.nombre} - {self.fecha} - Diario: {self.consumo_diario:,}"


@receiver(post_migrate)
def crear_limite_global_inicial(sender, **kwargs):
    """
    Signal que crea automáticamente el límite global inicial después de las migraciones.
    
    Esta función se ejecuta automáticamente después de cada migración y verifica
    si ya existe algún límite global. Si no existe ninguno, crea uno con valores
    predeterminados según la normativa legal paraguaya.
    
    Args:
        sender: El sender del signal (AppConfig)
        **kwargs: Argumentos del signal, incluyendo 'app_config'
        
    Note:
        Los valores iniciales son:
        - Límite diario: 90,000,000 guaraníes (90 millones)
        - Límite mensual: 450,000,000 guaraníes (450 millones)
    """
    if kwargs['app_config'].name == 'monedas':
        if not LimiteGlobal.objects.exists():
            LimiteGlobal.objects.create(
                limite_diario=90000000,  # 90 millones
                limite_mensual=450000000,  # 450 millones
                activo=True
            )
            print("Límite global inicial creado automáticamente")

@receiver(models.signals.post_save, sender='clientes.Cliente')
def crear_consumo_limite_cliente(sender, instance, created, **kwargs):
    """
    Signal que crea automáticamente un registro de ConsumoLimiteCliente
    cuando se crea un nuevo cliente.
    
    Esta función se ejecuta cada vez que se guarda un Cliente y, si es un
    cliente nuevo (created=True), le crea su registro de consumo inicial
    con valores en cero.
    
    Args:
        sender: El modelo Cliente
        instance: La instancia del cliente que se está guardando
        created (bool): True si es un cliente nuevo, False si se está actualizando
        **kwargs: Argumentos adicionales del signal
        
    Note:
        Esto asegura que todos los clientes tengan su registro de consumo
        disponible desde el momento de su creación.
    """
    if created:
        ConsumoLimiteCliente.objects.create(
            cliente=instance,
            fecha=date.today(),
            consumo_diario=0,
            consumo_mensual=0
        )
