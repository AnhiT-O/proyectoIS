from django import forms

class TokenForm(forms.Form):
    codigo = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autofocus': True
        }),
        required=True,
        error_messages={'required': 'Debes ingresar el código de transacción.'}
    )