from django import forms
from django.contrib.auth.forms import AuthenticationForm
from monedas.models import Moneda
from transacciones.models import Recargos
from decimal import Decimal

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
        recargo (ChoiceField): Campo para seleccionar el método de pago.
    """
    OPERACION_CHOICES = [
        ('compra', 'Compra'),
        ('venta', 'Venta'),
    ]
    
    moneda = forms.ModelChoiceField(
        queryset=Moneda.objects.filter(activa=True),
        empty_label="Selecciona una moneda",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'moneda',
            }),
        error_messages={'required': 'Debes seleccionar una moneda.'}
    )
    monto = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01',
            'placeholder': 'Seleccione primero una moneda',
            'id': 'monto',
        }),
        error_messages={
            'required': 'Debes ingresar un monto numérico.',
            'invalid': 'Por favor, ingrese un monto válido.'
        }
    )
    operacion = forms.ChoiceField(
        choices=OPERACION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'operacion',
            })
    )
    medio_pago = forms.ChoiceField(
        choices=[
            ('no_recargo', 'Efectivo/Cheque/Transferencia'),
            ({'brand': 'VISA'}, 'Tarjeta de Crédito Visa'),
            ({'brand': 'MASTERCARD'}, 'Tarjeta de Crédito Mastercard'),
            ('Tigo Money', 'Tigo Money'),
            ('Billetera Personal', 'Billetera Personal'),
            ('Zimple', 'Zimple')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}))
    medio_cobro = forms.ChoiceField(
        choices=[
            ('no_recargo', 'Efectivo/Transferencia'),
            ({'tipo_billetera': 'Tigo Money'}, 'Tigo Money'),
            ({'tipo_billetera': 'Billetera Personal'}, 'Billetera Personal'),
            ({'tipo_billetera': 'Zimple'}, 'Zimple')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}))
    
    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario y carga las opciones de recargo desde la base de datos.
        """
        self.cliente = kwargs.pop('cliente', None)
        super().__init__(*args, **kwargs)
    
    def clean_monto(self):
        """
        Valida el campo monto según las reglas específicas de la operación y moneda seleccionada.
        -   Si el monto es menor o igual a 0, lanza un error.
        -   Valida que el monto mínimo sea acorde a los decimales de la moneda seleccionada.
        """
        monto = self.cleaned_data.get('monto')
        operacion = self.data.get('operacion')
        moneda = self.data.get('moneda')
        
        if monto is None:
            return monto
            
        if monto <= 0:
            raise forms.ValidationError('El monto debe ser mayor a 0.')
        
        # Validaciones específicas por operación
        if operacion == 'compra':
            # Para compra, usar los decimales de la moneda seleccionada (moneda extranjera)
            if moneda:
                try:
                    moneda_obj = Moneda.objects.get(id=moneda, activa=True)
                    monto_minimo = Decimal('1') / (Decimal('10') ** moneda_obj.decimales)
                    if monto < monto_minimo:
                        raise forms.ValidationError(f'El monto mínimo para compra es {monto_minimo} {moneda_obj.simbolo}.')
                except (Moneda.DoesNotExist, ValueError):
                    # Fallback si no se puede obtener la moneda
                    if monto < Decimal('0.01'):
                        raise forms.ValidationError('El monto mínimo para compra es 0.01.')
            else:
                # Fallback si no hay moneda seleccionada
                if monto < Decimal('0.01'):
                    raise forms.ValidationError('El monto mínimo para compra es 0.01.')
                
        elif operacion == 'venta':
            # Para venta, usar los decimales de la moneda seleccionada (moneda extranjera)
            if moneda:
                try:
                    moneda_obj = Moneda.objects.get(id=moneda, activa=True)
                    monto_minimo = Decimal('1') / (Decimal('10') ** moneda_obj.decimales)
                    if monto < monto_minimo:
                        raise forms.ValidationError(f'El monto mínimo para venta es {monto_minimo} {moneda_obj.simbolo}.')
                except (Moneda.DoesNotExist, ValueError):
                    # Fallback si no se puede obtener la moneda
                    if monto < Decimal('0.01'):
                        raise forms.ValidationError('El monto mínimo para venta es 0.01.')
            else:
                # Fallback si no hay moneda seleccionada
                if monto < Decimal('0.01'):
                    raise forms.ValidationError('El monto mínimo para venta es 0.01.')
        
        return monto