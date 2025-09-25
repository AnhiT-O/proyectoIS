from django.db import models

class CuentaBancaria(models.Model):
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
        choices=BANCO_CHOICES
    )
    numero_cuenta = models.CharField(max_length=30)
    nombre_titular = models.CharField(max_length=100)
    nro_documento = models.CharField(max_length=20)
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        related_name='cuentas_bancarias'
    )
    class Meta:
        db_table = 'cuenta_bancaria'


class Billetera(models.Model):
    TIPO_BILLETERA_CHOICES = [
        ('-------', 'Seleccione un tipo de billetera'),
        ('tigo', 'Tigo Money'),
        ('personal', 'Billetera Personal'),
        ('zimple', 'Zimple'),
    ]
    
    tipo_billetera = models.CharField(
        max_length=30,
        choices=TIPO_BILLETERA_CHOICES
    )
    telefono = models.CharField(max_length=30)
    nombre_titular = models.CharField(max_length=100)
    nro_documento = models.CharField(max_length=20)
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        related_name='billeteras'
    )
    class Meta:
        db_table = 'billetera'