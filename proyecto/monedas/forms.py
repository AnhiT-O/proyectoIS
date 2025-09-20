from django import forms
from django.core.exceptions import ValidationError
from .models import Moneda, Limitacion

class MonedaForm(forms.ModelForm):

    nombre = forms.CharField(
        error_messages={
            'required': 'Debes ingresar un nombre.',
            'max_length': 'El nombre no puede exceder los 30 caracteres.',
            'unique': 'Ya existe una moneda con este nombre.'
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    simbolo = forms.CharField(
        max_length=3,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'maxlength': '3',
            'style': 'text-transform: uppercase;'
        }),
        error_messages={
            'required': 'Debes ingresar un símbolo.',
            'max_length': 'El símbolo no puede exceder las 3 letras.',
            'unique': 'Ya existe una moneda con este símbolo.'
        }
    )
    tasa_base = forms.IntegerField(
        required=True,
        error_messages={
            'min_value': 'La tasa base debe ser un número positivo.',
            'required': 'Debes ingresar una tasa base.'
        },
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'type': 'number'
        })
    )
    comision_compra = forms.IntegerField(
        required=True,
        error_messages={
            'min_value': 'La comisión de compra debe ser un número positivo.',
            'required': 'Debes ingresar una comisión de compra.'
        },
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'type': 'number'
        })
    )
    comision_venta = forms.IntegerField(
        required=True,
        error_messages={
            'min_value': 'La comisión de venta debe ser un número positivo.',
            'required': 'Debes ingresar una comisión de venta.'
        },
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'type': 'number'
        })
    )
    decimales = forms.IntegerField(
        required=False,
        error_messages={
            'min_value': 'El número de decimales debe ser al menos 0.'
        },
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'step': '1',
            'type': 'number',
            'value': '3'
        })
    )

    stock = forms.IntegerField(
        required= True,
        error_messages={
            'required': 'Debe ingresar una cantidad de stock'
        },
        widget= forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'type': 'number'
        })
    )

    # Campos para limitaciones por segmentación
    limite_vip = forms.DecimalField(
        required=False,
        max_digits=5,
        decimal_places=2,
        label='Límite VIP (%)',
        help_text='Porcentaje del stock que pueden comprar/vender clientes VIP',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '100',
            'step': '0.01',
            'placeholder': '0.00'
        })
    )

    limite_corporativo = forms.DecimalField(
        required=False,
        max_digits=5,
        decimal_places=2,
        label='Límite Corporativo (%)',
        help_text='Porcentaje del stock que pueden comprar/vender clientes Corporativos',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '100',
            'step': '0.01',
            'placeholder': '0.00'
        })
    )

    limite_minorista = forms.DecimalField(
        required=False,
        max_digits=5,
        decimal_places=2,
        label='Límite Minorista (%)',
        help_text='Porcentaje del stock que pueden comprar/vender clientes Minoristas',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '100',
            'step': '0.01',
            'placeholder': '0.00'
        })
    )


    class Meta:
        model = Moneda
        fields = ['nombre', 'simbolo', 'tasa_base', 'decimales', 'comision_compra', 'comision_venta', 'stock']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si estamos editando una moneda existente, cargar las limitaciones
        if self.instance and self.instance.pk:
            limitaciones = Limitacion.objects.filter(moneda=self.instance)
            for limitacion in limitaciones:
                if limitacion.segmentacion == 'VIP':
                    self.fields['limite_vip'].initial = limitacion.porcentaje_limite
                elif limitacion.segmentacion == 'CORPORATIVO':
                    self.fields['limite_corporativo'].initial = limitacion.porcentaje_limite
                elif limitacion.segmentacion == 'MINORISTA':
                    self.fields['limite_minorista'].initial = limitacion.porcentaje_limite

    def clean_simbolo(self):
        """
        Convierte el símbolo a mayúsculas.
        """
        simbolo = self.cleaned_data.get('simbolo')
        if simbolo:
            # Convertir a mayúsculas automáticamente
            simbolo = simbolo.upper()
            
            # Validar que solo contenga letras
            if not simbolo.isalpha():
                raise ValidationError('El símbolo debe contener solo letras.')
        return simbolo

    def clean_decimales(self):
        value = self.cleaned_data.get('decimales')
        return value if value is not None else 3

    def clean_tasa_base(self):
        """
        Valida que la tasa base sea un número positivo.
        """
        tasa_base = self.cleaned_data.get('tasa_base')
        if tasa_base is not None and tasa_base < 0:
            raise ValidationError('La tasa base debe ser un número positivo.')
        return tasa_base

    def clean_comision_compra(self):
        """
        Valida que la comisión de compra sea un número positivo.
        """
        comision_compra = self.cleaned_data.get('comision_compra')
        if comision_compra is not None and comision_compra < 0:
            raise ValidationError('La comisión de compra debe ser un número positivo.')
        return comision_compra

    def clean_comision_venta(self):
        """
        Valida que la comisión de venta sea un número positivo.
        """
        comision_venta = self.cleaned_data.get('comision_venta')
        if comision_venta is not None and comision_venta < 0:
            raise ValidationError('La comisión de venta debe ser un número positivo.')
        return comision_venta

    def clean_limite_vip(self):
        """Valida que el límite VIP esté entre 0 y 100"""
        limite = self.cleaned_data.get('limite_vip')
        if limite is not None and (limite < 0 or limite > 100):
            raise ValidationError('El límite debe estar entre 0 y 100%.')
        return limite

    def clean_limite_corporativo(self):
        """Valida que el límite Corporativo esté entre 0 y 100"""
        limite = self.cleaned_data.get('limite_corporativo')
        if limite is not None and (limite < 0 or limite > 100):
            raise ValidationError('El límite debe estar entre 0 y 100%.')
        return limite

    def clean_limite_minorista(self):
        """Valida que el límite Minorista esté entre 0 y 100"""
        limite = self.cleaned_data.get('limite_minorista')
        if limite is not None and (limite < 0 or limite > 100):
            raise ValidationError('El límite debe estar entre 0 y 100%.')
        return limite

    def save(self, commit=True):
        """Guarda la moneda y sus limitaciones"""
        moneda = super().save(commit=commit)
        
        if commit:
            # Guardar limitaciones
            limitaciones_data = [
                ('VIP', self.cleaned_data.get('limite_vip')),
                ('CORPORATIVO', self.cleaned_data.get('limite_corporativo')),
                ('MINORISTA', self.cleaned_data.get('limite_minorista')),
            ]
            
            for segmentacion, porcentaje in limitaciones_data:
                if porcentaje is not None:
                    # Actualizar o crear la limitación
                    Limitacion.objects.update_or_create(
                        moneda=moneda,
                        segmentacion=segmentacion,
                        defaults={'porcentaje_limite': porcentaje}
                    )
                else:
                    # Si no se especifica porcentaje, eliminar la limitación si existe
                    Limitacion.objects.filter(
                        moneda=moneda,
                        segmentacion=segmentacion
                    ).delete()
        
        return moneda