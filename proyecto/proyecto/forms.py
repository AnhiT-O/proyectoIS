from django import forms
from django.contrib.auth.forms import AuthenticationForm
from monedas.models import Moneda
from transacciones.models import Recargos
from decimal import Decimal

class LoginForm(AuthenticationForm):
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
        # Verifica si el usuario está bloqueado
        if user.bloqueado:
            raise forms.ValidationError(
                self.error_messages['blocked'],
                code='blocked',
            )
        super().confirm_login_allowed(user)


class SimuladorForm(forms.Form):
    OPERACION_CHOICES = [
        ('compra', 'Compra'),
        ('venta', 'Venta'),
    ]
    
    moneda = forms.ModelChoiceField(
        queryset=Moneda.objects.filter(activa=True),
        empty_label="Selecciona una moneda",
        error_messages={'required': 'Debes seleccionar una moneda.'}
    )
    monto = forms.DecimalField(
        error_messages={
            'required': 'Debes ingresar un monto numérico.',
            'invalid': 'Por favor, ingrese un monto válido.'
        }
    )
    operacion = forms.ChoiceField(
        choices=OPERACION_CHOICES,
        error_messages={'required': 'Debes seleccionar una operación.'}
    )
    recargo = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'recargo'}),
        error_messages={'required': 'Debes seleccionar un método de pago.'}
    )
    
    def __init__(self, *args, **kwargs):
        self.cliente = kwargs.pop('cliente', None)
        super().__init__(*args, **kwargs)
        
        # Cargar opciones de recargo dinámicamente desde la base de datos
        recargo_choices = []
        for recargo_obj in Recargos.objects.all().order_by('recargo'):
            if recargo_obj.recargo == 0:
                label = f"{recargo_obj.nombre}"
            else:
                label = f"{recargo_obj.nombre} (recargo del {recargo_obj.recargo}%)"
            recargo_choices.append((str(recargo_obj.id), label))
        
        self.fields['recargo'].choices = [('', 'Efectivo, Cheque, Transferencia')] + recargo_choices
    
    def clean_monto(self):
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
    
    def clean_moneda(self):
        moneda = self.cleaned_data.get('moneda')
        if moneda and not moneda.activa:
            raise forms.ValidationError('La moneda seleccionada no es válida.')
        return moneda
    
    def realizar_conversion(self):
        """
        Realiza la conversión de moneda basada en los datos validados del formulario.
        Debe llamarse solo después de que is_valid() retorne True.
        """
        if not self.is_valid():
            raise ValueError("El formulario no es válido. Llame a is_valid() primero.")
        
        moneda = self.cleaned_data['moneda']
        monto = self.cleaned_data['monto']
        operacion = self.cleaned_data['operacion']
        recargo_id = self.cleaned_data.get('recargo')
        
        # Obtener precios según la segmentación del cliente
        if self.cliente:
            precios = moneda.get_precios_cliente(self.cliente)
        else:
            precios = {
                'precio_compra': moneda.calcular_precio_compra(),
                'precio_venta': moneda.calcular_precio_venta()
            }
        
        # Realizar la conversión según el tipo de operación
        if operacion == 'compra':
            # Compra: moneda extranjera a PYG (cuántos guaraníes necesito para comprar X moneda extranjera)
            resultado = monto * precios['precio_venta']
        else:  # venta
            # Venta: moneda extranjera a PYG (cuántos guaraníes recibo por X moneda extranjera)
            resultado = monto * precios['precio_compra']
        
        # Aplicar recargo basado en la tabla Recargos
        recargo_aplicado = False
        porcentaje_recargo = 0
        
        if recargo_id:
            try:
                recargo_obj = Recargos.objects.get(id=recargo_id)
                if recargo_obj.recargo > 0:
                    # Convertir porcentaje a decimal (ej: 1% -> 1.01, 2% -> 1.02)
                    multiplicador_recargo = Decimal('1') + (Decimal(str(recargo_obj.recargo)) / Decimal('100'))
                    resultado = resultado * multiplicador_recargo
                    recargo_aplicado = True
                    porcentaje_recargo = float(recargo_obj.recargo)
            except Recargos.DoesNotExist:
                pass  # Si no existe el recargo, no se aplica ningún recargo
        
        return {
            'success': True,
            'resultado_numerico': int(resultado),
            'tipo_resultado': 'guaranies',
            'recargo_aplicado': recargo_aplicado,
            'porcentaje_recargo': porcentaje_recargo
        }