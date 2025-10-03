"""
Formularios para el sistema de transacciones de Global Exchange.

Este módulo contiene los formularios utilizados en el proceso de transacciones,
incluyendo la selección de monedas, montos y configuración de recargos.

Formularios principales:
    - SeleccionMonedaMontoForm: Selección de moneda y monto para transacciones
    - RecargoForm: Gestión de recargos por medio de pago
"""

from django import forms
from monedas.models import Moneda
from decimal import Decimal
from .models import Recargos, LimiteGlobal


class SeleccionMonedaMontoForm(forms.Form):
    """
    Formulario para seleccionar moneda y monto en operaciones de compra/venta.
    
    Este formulario permite al usuario seleccionar la moneda extranjera
    y especificar el monto que desea comprar o vender. Incluye validaciones
    específicas para cada moneda según sus decimales configurados.
    
    Fields:
        moneda (ModelChoiceField): Selector de moneda activa del sistema
        monto (DecimalField): Monto en la moneda seleccionada
        
    Validaciones:
        - El monto debe ser positivo y mayor al mínimo permitido
        - Se respetan los decimales configurados para cada moneda
        - Consistente con el comportamiento del simulador
    """
    
    moneda = forms.ModelChoiceField(
        queryset=Moneda.objects.filter(activa=True),
        empty_label="",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_moneda'
        }),
        required=True,
        error_messages={'required': 'Debes seleccionar una moneda.'}
    )

    monto = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'id_monto',
            'placeholder': 'Ingresa el monto en la moneda extranjera',
            'step': '1',
            'min': '1'
        }),
        required=True,
        error_messages={'required': 'Debes ingresar un monto numérico.'}
    )

    def clean(self):
        """
        Validación personalizada para el monto en moneda extranjera.
        
        Realiza validaciones específicas sobre el monto ingresado:
        - Verifica que sea un valor positivo
        - Comprueba que respete el monto mínimo según los decimales de la moneda
        - Convierte el monto a tipo Decimal para precisión
        
        Returns:
            dict: Datos limpios del formulario incluyendo monto_decimal
            
        Raises:
            ValidationError: Si el monto no cumple las validaciones
        """
        cleaned_data = super().clean()
        moneda = cleaned_data.get('moneda')
        monto = cleaned_data.get('monto')
        
        if monto is not None and moneda is not None:
            try:
                monto = Decimal(monto)
                if monto <= 0:
                    self.add_error('monto', 'El monto debe ser mayor a 0.')
                    return cleaned_data
                
                # Para monto en moneda extranjera, usar los decimales de la moneda seleccionada
                monto_minimo = Decimal('1') / (Decimal('10') ** moneda.decimales)
                if monto < monto_minimo:
                    self.add_error('monto', f'El monto mínimo para {moneda.nombre} es {monto_minimo} {moneda.simbolo}.')
                    return cleaned_data
                    
            except (ValueError, TypeError):
                self.add_error('monto', 'Por favor, ingrese un monto válido.')
                return cleaned_data
        
        # Agregar el monto convertido a los datos limpios
        cleaned_data['monto_decimal'] = monto
        return cleaned_data


class VariablesForm(forms.Form):
    """
    Formulario para editar los recargos por medio de pago y los límites globales de transacciones.
    
    Este formulario permite a los administradores modificar:
    - Los porcentajes de recargo para cada medio de pago (VISA, MASTERCARD, billeteras electrónicas)
    - Los límites diarios y mensuales globales según la ley de casas de cambio
    
    Fields:
        recargo_visa (DecimalField): Porcentaje de recargo para tarjetas VISA
        recargo_mastercard (DecimalField): Porcentaje de recargo para tarjetas MASTERCARD
        recargo_tigo_money (DecimalField): Porcentaje de recargo para Tigo Money
        recargo_billetera_personal (DecimalField): Porcentaje de recargo para Billetera Personal
        recargo_zimple (DecimalField): Porcentaje de recargo para Zimple
        limite_diario (IntegerField): Límite diario global en guaraníes
        limite_mensual (IntegerField): Límite mensual global en guaraníes
    """
    
    # Campos para recargos
    recargo_visa = forms.DecimalField(
        max_digits=4,
        decimal_places=1,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1'
        }),
        error_messages={
            'min_value': 'El recargo no puede ser negativo.',
            'max_value': 'El recargo no puede exceder el 100%.',
            'invalid': 'Ingrese un valor decimal válido.'
        }
    )
    
    recargo_mastercard = forms.DecimalField(
        max_digits=4,
        decimal_places=1,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1'
        }),
        error_messages={
            'min_value': 'El recargo no puede ser negativo.',
            'max_value': 'El recargo no puede exceder el 100%.',
            'invalid': 'Ingrese un valor decimal válido.'
        }
    )
    
    recargo_tigo_money = forms.DecimalField(
        max_digits=4,
        decimal_places=1,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1'
        }),
        error_messages={
            'min_value': 'El recargo no puede ser negativo.',
            'max_value': 'El recargo no puede exceder el 100%.',
            'invalid': 'Ingrese un valor decimal válido.'
        }
    )
    
    recargo_billetera_personal = forms.DecimalField(
        max_digits=4,
        decimal_places=1,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1'
        }),
        error_messages={
            'min_value': 'El recargo no puede ser negativo.',
            'max_value': 'El recargo no puede exceder el 100%.',
            'invalid': 'Ingrese un valor decimal válido.'
        }
    )
    
    recargo_zimple = forms.DecimalField(
        max_digits=4,
        decimal_places=1,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1'
        }),
        error_messages={
            'min_value': 'El recargo no puede ser negativo.',
            'max_value': 'El recargo no puede exceder el 100%.',
            'invalid': 'Ingrese un valor decimal válido.'
        }
    )
    
    # Campos para límites globales
    limite_diario = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        }),
        error_messages={
            'min_value': 'El límite diario debe ser al menos 1 guaraní.',
            'invalid': 'Ingrese un valor entero válido.'
        }
    )
    
    limite_mensual = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        }),
        error_messages={
            'min_value': 'El límite diario debe ser al menos 1 guaraní.',
            'invalid': 'Ingrese un valor entero válido.'
        }
    )
    
    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario con los valores actuales de la base de datos.
        
        Carga automáticamente los valores existentes de recargos y límites globales
        para que aparezcan pre-poblados en el formulario.
        """
        super().__init__(*args, **kwargs)
        
        # Cargar valores actuales de recargos
        try:
            visa_recargo = Recargos.objects.get(marca='VISA')
            self.fields['recargo_visa'].initial = visa_recargo.recargo
        except Recargos.DoesNotExist:
            self.fields['recargo_visa'].initial = 1.0
            
        try:
            mastercard_recargo = Recargos.objects.get(marca='MASTERCARD')
            self.fields['recargo_mastercard'].initial = mastercard_recargo.recargo
        except Recargos.DoesNotExist:
            self.fields['recargo_mastercard'].initial = 1.5
            
        try:
            tigo_recargo = Recargos.objects.get(marca='Tigo Money')
            self.fields['recargo_tigo_money'].initial = tigo_recargo.recargo
        except Recargos.DoesNotExist:
            self.fields['recargo_tigo_money'].initial = 2.0
            
        try:
            billetera_recargo = Recargos.objects.get(marca='Billetera Personal')
            self.fields['recargo_billetera_personal'].initial = billetera_recargo.recargo
        except Recargos.DoesNotExist:
            self.fields['recargo_billetera_personal'].initial = 2.0
            
        try:
            zimple_recargo = Recargos.objects.get(marca='Zimple')
            self.fields['recargo_zimple'].initial = zimple_recargo.recargo
        except Recargos.DoesNotExist:
            self.fields['recargo_zimple'].initial = 3.0
        
        # Cargar valores actuales de límites globales
        try:
            limite_global = LimiteGlobal.objects.first()
            if limite_global:
                self.fields['limite_diario'].initial = limite_global.limite_diario
                self.fields['limite_mensual'].initial = limite_global.limite_mensual
            else:
                # Valores por defecto si no existe registro
                self.fields['limite_diario'].initial = 90000000
                self.fields['limite_mensual'].initial = 450000000
        except LimiteGlobal.DoesNotExist:
            self.fields['limite_diario'].initial = 90000000
            self.fields['limite_mensual'].initial = 450000000
    
    def save(self):
        """
        Guarda los cambios en la base de datos.
        
        Actualiza todos los registros de recargos existentes y el registro
        de límites globales con los nuevos valores del formulario.
        
        Returns:
            dict: Diccionario con información sobre los cambios realizados
        """
        if not self.is_valid():
            return False
        
        # Actualizar recargos
        recargos_data = [
            ('VISA', self.cleaned_data['recargo_visa']),
            ('MASTERCARD', self.cleaned_data['recargo_mastercard']),
            ('Tigo Money', self.cleaned_data['recargo_tigo_money']),
            ('Billetera Personal', self.cleaned_data['recargo_billetera_personal']),
            ('Zimple', self.cleaned_data['recargo_zimple']),
        ]
        
        for marca, nuevo_recargo in recargos_data:
            try:
                recargo_obj = Recargos.objects.get(marca=marca)
                recargo_anterior = recargo_obj.recargo
                recargo_obj.recargo = nuevo_recargo
                recargo_obj.save()
            except Recargos.DoesNotExist:
                # Si no existe, crear el recargo
                medio = 'Tarjeta de Crédito' if marca in ['VISA', 'MASTERCARD'] else 'Billetera Electrónica'
                Recargos.objects.create(
                    marca=marca,
                    medio=medio,
                    recargo=nuevo_recargo
                )
        
        # Actualizar límites globales
        limite_global, created = LimiteGlobal.objects.get_or_create(
            defaults={
                'limite_diario': self.cleaned_data['limite_diario'],
                'limite_mensual': self.cleaned_data['limite_mensual']
            }
        )
        
        if not created:
            limite_global.limite_diario = self.cleaned_data['limite_diario']
            limite_global.limite_mensual = self.cleaned_data['limite_mensual']
            limite_global.save()
        
        return True
