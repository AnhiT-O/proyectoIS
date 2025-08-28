from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
import re
from .models import Usuario
from clientes.models import Cliente

class RegistroUsuarioForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': "El nombre de usuario es obligatorio.",
            'max_length': "El nombre de usuario no puede tener más de 30 caracteres.",
            'unique': "Ya existe un usuario registrado con este nombre de usuario."
        }
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        error_messages={
            'invalid': "Introduce un correo electrónico válido.",
            'required': "El correo electrónico es obligatorio.",
            'unique': "Ya existe un usuario registrado con este correo electrónico."
        }
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': "El nombre es obligatorio.",
            'max_length': "El nombre no puede tener más de 40 caracteres."
        }
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': "El apellido es obligatorio.",
            'max_length': "El apellido no puede tener más de 40 caracteres."
        }
    )
    tipo_cedula = forms.ChoiceField(
        choices=Usuario.TIPO_CEDULA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    cedula_identidad = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': "La cédula de identidad es obligatoria.",
            'max_length': "La cédula de identidad no puede tener más de 11 caracteres.",
            'unique': "Ya existe un usuario registrado con esta cédula."
        }
    )

    class Meta:
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'tipo_cedula', 'cedula_identidad', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_cedula_identidad(self):
        cedula = self.cleaned_data.get('cedula_identidad')
        if not cedula.isdigit():
            raise ValidationError("La cédula de identidad debe ser numérica.")
        if len(cedula) < 4:
            raise ValidationError("La cédula de identidad debe tener al menos 4 dígitos.")
        return cedula

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
        if commit:
            user.save()
        return user


class RecuperarPasswordForm(PasswordResetForm):
    """Formulario personalizado para recuperación de contraseña"""
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico',
            'autofocus': True
        }),
        label='Correo electrónico'
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Verificar que el email esté registrado y que el usuario esté activo
            try:
                user = Usuario.objects.get(email=email, is_active=True)
            except Usuario.DoesNotExist:
                raise ValidationError("No existe una cuenta activa asociada a este correo electrónico.")
        return email

    def get_users(self, email):
        """Sobrescribir método para obtener solo usuarios activos"""
        return Usuario.objects.filter(
            email__iexact=email,
            is_active=True
        )


class EstablecerPasswordForm(SetPasswordForm):
    """Formulario personalizado para establecer nueva contraseña"""
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nueva contraseña'
        }),
        strip=False,
    )
    new_password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar nueva contraseña'
        }),
        strip=False,
    )

    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')

        if not password1:
            raise ValidationError("La contraseña es obligatoria.")

        if len(password1) <= 8:
            raise ValidationError("La contraseña debe tener más de 8 caracteres.")

        if not re.search(r'[^A-Za-z0-9]', password1):
            raise ValidationError("La contraseña debe contener al menos un caracter especial.")

        if not re.search(r'\d', password1):
            raise ValidationError("La contraseña debe contener al menos un número.")

        return password1


class AsignarRolForm(forms.Form):
    """Formulario para asignar roles a usuarios"""
    rol = forms.ModelChoiceField(
        queryset=Group.objects.exclude(name='administrador').order_by('name'),
        empty_label="Seleccionar rol",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'width: 100%; padding: 0.5rem;'
        }),
        label='Rol'
    )

    def __init__(self, *args, **kwargs):
        usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)
        
        if usuario:
            # Excluir roles que el usuario ya tiene
            roles_actuales = usuario.groups.all()
            self.fields['rol'].queryset = Group.objects.exclude(
                name='administrador'
            ).exclude(
                id__in=roles_actuales.values_list('id', flat=True)
            ).order_by('name')

    def clean_rol(self):
        rol = self.cleaned_data.get('rol')
        if not rol:
            raise ValidationError("Debe seleccionar un rol.")
        return rol


class AsignarClienteForm(forms.Form):
    """Formulario para asignar clientes a usuarios"""
    clientes = forms.ModelMultipleChoiceField(
        queryset=Cliente.objects.all().order_by('nombre', 'apellido'),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Clientes disponibles',
        required=False
    )

    def __init__(self, *args, **kwargs):
        usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)
        
        if usuario:
            # Excluir clientes que ya están asignados al usuario
            clientes_asignados = usuario.clientes_operados.all()
            self.fields['clientes'].queryset = Cliente.objects.exclude(
                id__in=clientes_asignados.values_list('id', flat=True)
            ).order_by('nombre', 'apellido')
            
            # Personalizar la etiqueta de cada cliente
            self.fields['clientes'].label_from_instance = lambda obj: f"{obj.nombre} {obj.apellido} ({obj.docCliente})"

    def clean_clientes(self):
        clientes = self.cleaned_data.get('clientes')
        if not clientes:
            raise ValidationError("Debe seleccionar al menos un cliente.")
        return clientes
