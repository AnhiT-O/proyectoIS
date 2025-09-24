from django.db import models

class CuentaBancaria(models.Model):
    TIPO_CUENTA_CHOICES = [
        ('cuenta_corriente', 'Cuenta Corriente'),
        ('cuenta_ahorro', 'Cuenta de Ahorro'),
    ]
    BANCO_CHOICES = [
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
    tipo_cuenta = models.CharField(
        max_length=30,
        choices=TIPO_CUENTA_CHOICES
    )
    banco = models.CharField(
        max_length=30,
        choices=BANCO_CHOICES
    )
    numero_cuenta = models.CharField(max_length=30)
    nombre_titular = models.CharField(max_length=100)
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        related_name='cuentas_bancarias'
    )

class Billetera(models.Model):
    TIPO_BILLETERA_CHOICES = [
        ('tigo_money', 'Tigo Money'),
        ('billetera_personal', 'Billetera Personal'),
        ('zimple', 'Zimple'),
    ]
    
    tipo_billetera = models.CharField(
        max_length=30,
        choices=TIPO_BILLETERA_CHOICES
    )
    numero_billetera = models.CharField(max_length=30)
    nombre_titular = models.CharField(max_length=100)
    ci = models.CharField(max_length=20)
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        related_name='billeteras'
    )