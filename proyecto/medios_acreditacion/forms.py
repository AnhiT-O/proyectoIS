from django import forms
from .models import CuentaBancaria, Billetera

class CuentaBancariaForm(forms.ModelForm):
    banco = forms.ChoiceField(
        choices=CuentaBancaria.BANCO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Debes seleccionar un banco.',
        }
    )
    numero_cuenta = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Debes ingresar el número de cuenta.',
            'max_length': 'El número de cuenta no puede exceder los 30 caracteres.'
        }
    )
    nombre_titular = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Debes ingresar el nombre del titular.',
            'max_length': 'El nombre del titular no puede exceder los 100 caracteres.'
        }
    )
    nro_documento = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Debes ingresar el número de documento del titular.',
            'max_length': 'El número de documento no puede exceder los 20 caracteres.'
        }
    )

    class Meta:
        model = CuentaBancaria
        fields = ['banco', 'numero_cuenta', 'nombre_titular', 'nro_documento']

    def clean_banco(self):
        banco = self.cleaned_data.get('banco')
        if banco == '-------':
            raise forms.ValidationError('Debes seleccionar un banco válido.')
        return banco

class BilleteraForm(forms.ModelForm):
    tipo_billetera = forms.ChoiceField(
        choices=Billetera.TIPO_BILLETERA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Debes seleccionar un tipo de billetera.',
        }
    )
    telefono = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Debes ingresar el número de teléfono asociado a la billetera.',
            'max_length': 'El número de teléfono no puede exceder los 15 caracteres.'
        }
    )
    nombre_titular = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Debes ingresar el nombre del titular.',
            'max_length': 'El nombre del titular no puede exceder los 100 caracteres.'
        }
    )
    nro_documento = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Debes ingresar el número de documento del titular.',
            'max_length': 'El número de documento no puede exceder los 20 caracteres.'
        }
    )
    class Meta:
        model = Billetera
        fields = ['tipo_billetera', 'telefono', 'nombre_titular', 'nro_documento']
    
    def clean_tipo_billetera(self):
        tipo_billetera = self.cleaned_data.get('tipo_billetera')
        if tipo_billetera == '-------':
            raise forms.ValidationError('Debes seleccionar un tipo de billetera válido.')
        return tipo_billetera