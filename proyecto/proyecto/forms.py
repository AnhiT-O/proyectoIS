from django import forms
from django.contrib.auth.forms import AuthenticationForm
from monedas.models import Moneda
from decimal import Decimal
from django.contrib import messages

class LoginForm(AuthenticationForm):
    """
    Formulario de inicio de sesión personalizado.

    Attributes:
        username (CharField): Campo para el nombre de usuario.
        password (CharField): Campo para la contraseña.
    """
    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'autofocus': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    error_messages = {
        'invalid_login': "El nombre de usuario y contraseña no coinciden. Inténtelo de nuevo.",
        'blocked': "Esta cuenta está bloqueada. Por favor contacta con el administrador."
    }

    def confirm_login_allowed(self, user):
        """ 
        Verifica si el usuario no está bloqueado para iniciar sesión.
        """
        if user.bloqueado:
            raise forms.ValidationError(
                self.error_messages['blocked'],
                code='blocked',
            )
        super().confirm_login_allowed(user)


class SimuladorForm(forms.Form):
    """
    Formulario para simular conversiones de moneda.

    Attributes:
        moneda (ModelChoiceField): Campo para seleccionar la moneda.
        monto (DecimalField): Campo para ingresar el monto a convertir.
        operacion (ChoiceField): Campo para seleccionar el tipo de operación (compra o venta).
        medio_pago (ChoiceField): Campo para seleccionar el medio de pago.
        medio_cobro (ChoiceField): Campo para seleccionar el medio de cobro.
    """
    
    moneda = forms.ModelChoiceField(
        queryset=Moneda.objects.filter(activa=True),
        empty_label="",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'moneda',
            }),
        error_messages={'required': 'Debes seleccionar una moneda.'}
    )
    monto = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '1',
            'min': '1',
            'id': 'monto',
        }),
        required=True,
        error_messages={
            'required': 'Debes ingresar un monto numérico.',
        }
    )
    operacion = forms.ChoiceField(
        choices=[
        ('compra', 'Compra'),
        ('venta', 'Venta'),
        ],
        initial='compra'
    )
    medio_pago = forms.ChoiceField(
        choices=[
                ('Efectivo', 'Efectivo'),
                ('Transferencia', 'Transferencia'),
                ('{"brand": "VISA"}', 'Tarjeta de Crédito Visa'),
                ('{"brand": "MASTERCARD"}', 'Tarjeta de Crédito Mastercard'),
                ('Tigo Money', 'Tigo Money'),
                ('Billetera Personal', 'Billetera Personal'),
                ('Zimple', 'Zimple')
            ],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'medio_pago',
        }))
    medio_cobro = forms.ChoiceField(
        choices=[
                ('Efectivo', 'Efectivo'),
                ('Cuenta Bancaria', 'Cuenta Bancaria'),
                ('{"tipo_billetera": "Tigo Money"}', 'Tigo Money'),
                ('{"tipo_billetera": "Billetera Personal"}', 'Billetera Personal'),
                ('{"tipo_billetera": "Zimple"}', 'Zimple')
            ],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'medio_cobro',
        }))
    
    def clean_monto(self):
        """
        Valida el campo monto según las reglas específicas de la operación y moneda seleccionada.
        
        -   Si el monto es menor o igual a 0, lanza un error.
        -   Valida que el monto mínimo sea acorde a los decimales de la moneda seleccionada.
        """
        monto = self.cleaned_data.get('monto')
        moneda = self.data.get('moneda')
        medio_pago = self.cleaned_data.get('medio_pago')
        medio_cobro = self.cleaned_data.get('medio_cobro')
            
        if monto <= 0:
            raise forms.ValidationError('El monto debe ser mayor a 0.')
        if moneda:
            try:
                moneda_obj = Moneda.objects.get(id=moneda, activa=True)
                monto_minimo = Decimal('1') / (Decimal('10') ** moneda_obj.decimales)
                if monto < monto_minimo:
                    raise forms.ValidationError(f'El monto mínimo para compra es {monto_minimo} {moneda_obj.simbolo}.')
            except (Moneda.DoesNotExist, ValueError):
                messages.error(self.request, 'Error al obtener la moneda seleccionada.')
        else:
            raise forms.ValidationError('Selecciona primero una moneda.')
        
        return monto