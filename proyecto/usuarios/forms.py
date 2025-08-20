from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
import re
from .models import Usuario

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de usuario'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
    )
    
    error_messages = {
        'invalid_login': "Por favor, introduce un nombre de usuario y contraseña correctos. "
                        "Ten en cuenta que ambos campos distinguen entre mayúsculas y minúsculas.",
        'inactive': "Esta cuenta está inactiva.",
    }

class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    tipo_cedula = forms.ChoiceField(
        choices=Usuario.TIPO_CEDULA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    cedula_identidad = forms.CharField(
        max_length=14,
        required=False,  # Hacemos el campo opcional en el formulario
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'tipo_cedula', 'cedula_identidad', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_cedula_identidad(self):
        cedula = self.cleaned_data.get('cedula_identidad')
        tipo_cedula = self.cleaned_data.get('tipo_cedula')
        
        if not cedula:
            raise ValidationError("La cédula es obligatoria.")
        
        if not cedula.isdigit():
            raise ValidationError("La cédula debe contener solo números.")
        
        if tipo_cedula == 'CI':
            if len(cedula) < 4 or len(cedula) > 12:
                raise ValidationError("La Cédula de Identidad debe tener entre 4 y 12 dígitos.")
        elif tipo_cedula == 'RUC':
            if len(cedula) < 5 or len(cedula) > 13:
                raise ValidationError("El RUC debe tener entre 5 y 13 dígitos.")

        # Verificar unicidad excluyendo usuarios inactivos con cédula duplicada
        existing_user = Usuario.objects.filter(cedula_identidad=cedula).first()
        if existing_user and existing_user.is_active:
            raise ValidationError("Ya existe un usuario registrado con esta cédula.")
        
        return cedula

    def clean_email(self):
        email = self.cleaned_data.get('email')
        existing_user = Usuario.objects.filter(email=email).first()
        if existing_user:
            if existing_user.is_active:
                raise ValidationError("Ya existe un usuario registrado con este correo electrónico.")
            else:
                raise ValidationError("Una cuenta con este correo electrónico ya existe, pero no está activada. Revisa su bandeja de entrada")
        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')

        if not password1:
            raise ValidationError("La contraseña es obligatoria.")

        if len(password1) <= 8:
            raise ValidationError("La contraseña debe tener más de 8 caracteres.")

        if not re.search(r'[^A-Za-z0-9]', password1):
            raise ValidationError("La contraseña debe contener al menos un caracter especial.")

        if not re.search(r'\d', password1):
            raise ValidationError("La contraseña debe contener al menos un número.")

        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError("Las contraseñas no coinciden.")
        
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.tipo_cedula = self.cleaned_data['tipo_cedula']
        user.cedula_identidad = self.cleaned_data['cedula_identidad']
        user.is_active = False  # Usuario inactivo hasta confirmar email
        if commit:
            user.save()
        return user
