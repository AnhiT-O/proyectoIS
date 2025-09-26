"""
Modelos para los medios de acreditación del sistema.

Este módulo contiene los modelos que representan los diferentes medios de acreditación
que pueden tener asociados los clientes del sistema, como cuentas bancarias y billeteras
electrónicas.

Clases:
    CuentaBancaria: Modelo que representa una cuenta bancaria de un cliente.
    Billetera: Modelo que representa una billetera electrónica de un cliente.
"""

from django.db import models


class CuentaBancaria(models.Model):
    """
    Modelo que representa una cuenta bancaria asociada a un cliente.
    
    Esta clase define los datos necesarios para almacenar información de cuentas bancarias
    que pueden ser utilizadas como medio de acreditación para transacciones.
    
    Attributes:
        BANCO_CHOICES (list): Lista de tuplas con los bancos disponibles en el sistema.
        banco (CharField): Banco al que pertenece la cuenta.
        numero_cuenta (CharField): Número de la cuenta bancaria.
        nombre_titular (CharField): Nombre completo del titular de la cuenta.
        nro_documento (CharField): Número de documento del titular.
        cliente (ForeignKey): Referencia al cliente propietario de la cuenta.
        
    Meta:
        db_table (str): Nombre de la tabla en la base de datos.
    """
    # Opciones disponibles para los bancos del sistema
    # Incluye bancos comerciales, financieras y cooperativas de Paraguay
    BANCO_CHOICES = [
        ('-------', 'Seleccione un banco'),  # Opción por defecto
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
    
    # Campo para el banco seleccionado, con validación mediante choices
    banco = models.CharField(
        max_length=30,
        choices=BANCO_CHOICES,
        help_text="Banco al que pertenece la cuenta bancaria"
    )
    
    # Número de cuenta bancaria (puede incluir letras y números)
    numero_cuenta = models.CharField(
        max_length=30,
        help_text="Número de la cuenta bancaria"
    )
    
    # Nombre completo del titular de la cuenta
    nombre_titular = models.CharField(
        max_length=100,
        help_text="Nombre completo del titular de la cuenta"
    )
    
    # Número de documento de identidad del titular
    nro_documento = models.CharField(
        max_length=20,
        help_text="Número de documento del titular (CI, RUC, etc.)"
    )
    
    # Relación con el cliente propietario de la cuenta
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        related_name='cuentas_bancarias',
        help_text="Cliente propietario de la cuenta bancaria"
    )
    class Meta:
        """Metadatos del modelo CuentaBancaria."""
        db_table = 'cuenta_bancaria'  # Nombre personalizado de la tabla en BD
        verbose_name = 'Cuenta Bancaria'
        verbose_name_plural = 'Cuentas Bancarias'
        
    def __str__(self):
        """
        Representación en cadena de la cuenta bancaria.
        
        Returns:
            str: Formato "Banco - Número de cuenta (Titular)"
        """
        return f"{self.get_banco_display()} - {self.numero_cuenta} ({self.nombre_titular})"


class Billetera(models.Model):
    """
    Modelo que representa una billetera electrónica asociada a un cliente.
    
    Esta clase define los datos necesarios para almacenar información de billeteras
    electrónicas que pueden ser utilizadas como medio de acreditación para transacciones.
    
    Attributes:
        TIPO_BILLETERA_CHOICES (list): Lista de tuplas con los tipos de billetera disponibles.
        tipo_billetera (CharField): Tipo de billetera electrónica.
        telefono (CharField): Número de teléfono asociado a la billetera.
        nombre_titular (CharField): Nombre completo del titular de la billetera.
        nro_documento (CharField): Número de documento del titular.
        cliente (ForeignKey): Referencia al cliente propietario de la billetera.
        
    Meta:
        db_table (str): Nombre de la tabla en la base de datos.
    """
    # Opciones disponibles para los tipos de billetera electrónica
    # Incluye las principales billeteras digitales disponibles en Paraguay
    TIPO_BILLETERA_CHOICES = [
        ('-------', 'Seleccione un tipo de billetera'),
        ('tigo', 'Tigo Money'),
        ('personal', 'Billetera Personal'),
        ('zimple', 'Zimple'),
    ]
    
    # Campo para el tipo de billetera seleccionada, con validación mediante choices
    tipo_billetera = models.CharField(
        max_length=30,
        choices=TIPO_BILLETERA_CHOICES,
        help_text="Tipo de billetera electrónica"
    )
    
    # Número de teléfono asociado a la billetera
    telefono = models.CharField(
        max_length=30,
        help_text="Número de teléfono asociado a la billetera"
    )
    
    # Nombre completo del titular de la billetera
    nombre_titular = models.CharField(
        max_length=100,
        help_text="Nombre completo del titular de la billetera"
    )
    
    # Número de documento de identidad del titular
    nro_documento = models.CharField(
        max_length=20,
        help_text="Número de documento del titular (CI, RUC, etc.)"
    )
    
    # Relación con el cliente propietario de la billetera
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        related_name='billeteras',
        help_text="Cliente propietario de la billetera"
    )
    
    def get_tipo_billetera_display(self):
        """
        Método personalizado para mostrar el tipo de billetera correctamente.
        
        Este método proporciona un mapeo personalizado para mostrar los nombres
        de las billeteras de forma consistente, especialmente para valores que
        pueden contener guiones bajos o formatos especiales.
        
        Returns:
            str: Nombre formateado del tipo de billetera para mostrar al usuario.
        """
        # Mapeo personalizado para valores que pueden tener guiones bajos
        display_map = {
            'tigo': 'Tigo Money',
            'personal': 'Billetera Personal',
            'zimple': 'Zimple',
        }
        
        # Si el valor está en el mapeo personalizado, usar ese
        if self.tipo_billetera in display_map:
            return display_map[self.tipo_billetera]
        
        # Si no está en el mapeo, usar el método por defecto de Django
        return dict(self.TIPO_BILLETERA_CHOICES).get(self.tipo_billetera, self.tipo_billetera)
    
    def __str__(self):
        """
        Representación en cadena de la billetera.
        
        Returns:
            str: Formato "Tipo de billetera - Teléfono (Titular)"
        """
        return f"{self.get_tipo_billetera_display()} - {self.telefono} ({self.nombre_titular})"
    
    class Meta:
        """Metadatos del modelo Billetera."""
        db_table = 'billetera'  # Nombre personalizado de la tabla en BD
        verbose_name = 'Billetera'
        verbose_name_plural = 'Billeteras'