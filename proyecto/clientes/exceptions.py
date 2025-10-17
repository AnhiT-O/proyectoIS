"""
Excepciones personalizadas para el módulo de clientes.

Este módulo contiene las excepciones personalizadas utilizadas en la gestión
de clientes, especialmente en el procesamiento de tarjetas de crédito y
métodos de pago con Stripe.

Autor: Equipo de desarrollo
Fecha: 2025
"""


class TarjetaNoPermitida(Exception):
    """
    Excepción lanzada cuando se intenta agregar una tarjeta que no es de crédito.
    
    Esta excepción se utiliza cuando el sistema detecta que el tipo de tarjeta
    (funding type) no es 'credit', ya que solo se permiten tarjetas de crédito
    en el sistema.
    
    Attributes:
        message (str): Mensaje descriptivo del error
    
    Examples:
        >>> if payment_method.card.funding != 'credit':
        ...     raise TarjetaNoPermitida("Solo se permiten tarjetas de crédito")
    """
    
    def __init__(self, message="Solo se permiten tarjetas de crédito"):
        """
        Inicializa la excepción con un mensaje personalizado.
        
        Args:
            message (str): Mensaje descriptivo del error. Por defecto indica
                         que solo se permiten tarjetas de crédito.
        """
        self.message = message
        super().__init__(self.message)


class MarcaNoPermitida(Exception):
    """
    Excepción lanzada cuando se intenta agregar una tarjeta de una marca no permitida.
    
    Esta excepción se utiliza cuando la marca de la tarjeta de crédito no está
    registrada en la tabla de Recargos del sistema, lo que significa que no
    se pueden procesar transacciones con esa marca específica.
    
    Attributes:
        message (str): Mensaje descriptivo del error
        marca (str): La marca de tarjeta que causó el error (opcional)
    
    Examples:
        >>> if not Recargos.objects.filter(marca=marca_tarjeta).exists():
        ...     raise MarcaNoPermitida(f"La marca {marca_tarjeta} no está permitida")
    """
    
    def __init__(self, message="La marca de la tarjeta no está permitida", marca=None):
        """
        Inicializa la excepción con un mensaje personalizado y opcionalmente la marca.
        
        Args:
            message (str): Mensaje descriptivo del error. Por defecto indica
                         que la marca no está permitida.
            marca (str, optional): La marca de tarjeta que causó el error.
        """
        self.message = message
        self.marca = marca
        super().__init__(self.message)