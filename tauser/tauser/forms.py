from django import forms

class CodigoForm(forms.Form):
    codigo = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autofocus': True
        }),
        required=True,
        error_messages={
            'required': 'Debes ingresar el código de transacción.',
            'max_length': 'El código no excede los 50 caracteres.'
        }
    )