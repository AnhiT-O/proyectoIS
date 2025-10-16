"""
Modelos para los medios de acreditación del sistema.

Este módulo contiene los modelos que representan los diferentes medios de acreditación
que pueden tener asociados los clientes del sistema, como cuentas bancarias y billeteras
electrónicas.

Clases:
    MedioAcreditacion: Modelo abstracto base con campos comunes.
    CuentaBancaria: Modelo que representa una cuenta bancaria de un cliente.
    Billetera: Modelo que representa una billetera electrónica de un cliente.
"""

from django.db import models

class MedioAcreditacion(models.Model):
    """
    Modelo abstracto base para medios de acreditación.
    
    Esta clase define los campos comunes que comparten todos los medios
    de acreditación como cuentas bancarias y billeteras electrónicas.
    
    Attributes:
        nombre_titular (CharField): Nombre completo del titular.
        nro_documento (CharField): Número de documento del titular.
        cliente (ForeignKey): Referencia al cliente propietario.
        fecha_creacion (DateTimeField): Fecha y hora de creación del registro.
        activo (BooleanField): Estado activo/inactivo del medio de acreditación.
    """
    
    # Nombre completo del titular del medio de acreditación
    nombre_titular = models.CharField(
        max_length=100,
        help_text="Nombre completo del titular"
    )
    
    # Número de documento de identidad del titular
    nro_documento = models.CharField(
        max_length=20,
        help_text="Número de documento del titular (CI, RUC, etc.)"
    )
    
    # Relación con el cliente propietario
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        help_text="Cliente propietario del medio de acreditación"
    )
    
    class Meta:
        """Metadatos del modelo base."""
        abstract = True  # Esto hace que sea un modelo abstracto (no crea tabla)


class CuentaBancaria(MedioAcreditacion):
    """
    Modelo que representa una cuenta bancaria asociada a un cliente.
    
    Hereda de MedioAcreditacion los campos comunes: nombre_titular, 
    nro_documento, cliente, fecha_creacion, activo.
    """
    
    BANCO_CHOICES = [
        ('-------', 'Seleccione un banco'),
        ('ATLAS', 'Banco Atlas'),
        ('BANCOP', 'BANCOP'),
        ('BASA', 'Banco Basa'),
        ('BNF', 'Banco Nacional de Fomento (BNF)'),
        ('CITIBANK', 'Citibank'),
        ('CONTINENTAL', 'Banco Continental'),
        ('FAMILIAR', 'Banco Familiar'),
        ('GNB', 'Banco GNB'),
        ('INTERFISA', 'Interfisa Banco'),
        ('ITAU', 'Banco Itaú'),
        ('SUDAMERIS', 'Banco Sudameris'),
        ('UENO', 'ueno bank'),
        ('ZETA', 'Zeta Banco'),
        ('FINLATINA', 'Financiera Finlatina'),
        ('TU_FINANCIERA', 'Tu Financiera'), 
        ('PARAGUAYO_JAPONESA', 'Financiera Paraguayo Japonesa'),
        ('FIC', 'FIC - Financiera'),
        ('COOP_UNIVERSITARIA', 'Cooperativa Universitaria'),
        ('COOP_SAGRADOS_CORAZONES', 'Cooperativa Sagrados Corazones'),
        ('COOP_CHORTITZER', 'Cooperativa Chortitzer'),
    ]
    
    banco = models.CharField(
        max_length=30,
        choices=BANCO_CHOICES,
        help_text="Banco al que pertenece la cuenta bancaria"
    )
    
    numero_cuenta = models.CharField(
        max_length=30,
        help_text="Número de la cuenta bancaria"
    )
    
    # Sobreescribimos la relación para tener related_name específico
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        related_name='cuentas_bancarias',
        help_text="Cliente propietario de la cuenta bancaria"
    )
    
    class Meta:
        """Metadatos del modelo CuentaBancaria."""
        db_table = 'cuenta_bancaria'
        verbose_name = 'Cuenta Bancaria'
        verbose_name_plural = 'Cuentas Bancarias'
        default_permissions = []  # Deshabilitar permisos por defecto
        
    def __str__(self):
        """Representación en cadena de la cuenta bancaria."""
        return f"{self.get_banco_display()} - {self.numero_cuenta} ({self.nombre_titular})"


class Billetera(MedioAcreditacion):
    """
    Modelo que representa una billetera electrónica asociada a un cliente.
    
    Hereda de MedioAcreditacion los campos comunes: nombre_titular, 
    nro_documento, cliente, fecha_creacion, activo.
    """
    
    TIPO_BILLETERA_CHOICES = [
        ('-------', 'Seleccione un tipo de billetera'),
        ('tigo', 'Tigo Money'),
        ('personal', 'Billetera Personal'),
        ('zimple', 'Zimple'),
    ]
    
    tipo_billetera = models.CharField(
        max_length=30,
        choices=TIPO_BILLETERA_CHOICES,
        help_text="Tipo de billetera electrónica"
    )
    
    telefono = models.CharField(
        max_length=30,
        help_text="Número de teléfono asociado a la billetera"
    )
    
    # Sobreescribimos la relación para tener related_name específico
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        related_name='billeteras',
        help_text="Cliente propietario de la billetera"
    )
    
    def get_tipo_billetera_display(self):
        """Método personalizado para mostrar el tipo de billetera correctamente."""
        display_map = {
            'tigo': 'Tigo Money',
            'personal': 'Billetera Personal',
            'zimple': 'Zimple',
        }
        
        if self.tipo_billetera in display_map:
            return display_map[self.tipo_billetera]
        
        return dict(self.TIPO_BILLETERA_CHOICES).get(self.tipo_billetera, self.tipo_billetera)
    
    def __str__(self):
        """Representación en cadena de la billetera."""
        return f"{self.get_tipo_billetera_display()} - {self.telefono} ({self.nombre_titular})"
    
    class Meta:
        """Metadatos del modelo Billetera."""
        db_table = 'billetera'
        verbose_name = 'Billetera'
        verbose_name_plural = 'Billeteras'
        default_permissions = []  # Deshabilitar permisos por defecto

class TarjetaLocal(MedioAcreditacion):
    """
    Modelo que representa una tarjeta de crédito local (Panal o Cabal) asociada a un cliente.
    
    Hereda de MedioAcreditacion los campos comunes: nombre_titular, 
    nro_documento, cliente.
    """
    
    TIPO_TARJETA_CHOICES = [
        ('PANAL', 'Panal'),
        ('CABAL', 'Cabal'),
    ]
    
    brand = models.CharField(
        max_length=10,
        choices=TIPO_TARJETA_CHOICES,
        help_text="Tipo de tarjeta local"
    )
    
    numero_tarjeta = models.CharField(
        max_length=19,  # Formato: XXXX XXXX XXXX XXXX
        help_text="Número completo de la tarjeta"
    )

    last4 = models.CharField(
        max_length=4
    )
    
    mes_expiracion = models.IntegerField(
        help_text="Mes de expiración (1-12)"
    )
    
    anio_expiracion = models.IntegerField(
        help_text="Año de expiración (YYYY)"
    )
    
    cvv = models.CharField(
        max_length=4,
        help_text="Código de seguridad CVV"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de creación del registro"
    )
    
    activo = models.BooleanField(
        default=True,
        help_text="Indica si la tarjeta está activa"
    )
    
    # Sobreescribimos la relación para tener related_name específico
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        related_name='tarjetas_locales',
        help_text="Cliente propietario de la tarjeta"
    )
    
    def get_last4(self):
        """Obtiene los últimos 4 dígitos de la tarjeta."""
        return self.numero_tarjeta.replace(' ', '')[-4:]
    
    def get_numero_enmascarado(self):
        """Retorna el número de tarjeta enmascarado."""
        return f"**** **** **** {self.get_last4()}"
    
    def save(self, *args, **kwargs):
        """Sobrescribe el método save para actualizar last4 automáticamente."""
        self.last4 = self.get_last4()
        super().save(*args, **kwargs)
    
    class Meta:
        """Metadatos del modelo TarjetaLocal."""
        db_table = 'tarjeta_local'
        verbose_name = 'Tarjeta Local'
        verbose_name_plural = 'Tarjetas Locales'
        default_permissions = []  # Deshabilitar permisos por defecto