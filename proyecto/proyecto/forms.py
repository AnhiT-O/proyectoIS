from django import forms
from django.contrib.auth.forms import AuthenticationForm
from usuarios.models import Usuario

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Nombre de usuario'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control','placeholder': 'Contraseña'})
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