from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
import re
from .models import Usuario
from clientes.models import Cliente

class RegistroUsuarioForm(UserCreationForm):
    """
    Formulario personalizado para el registro de usuarios.

    Attributes:
        username (CharField): Campo para el nombre de usuario.
        email (EmailField): Campo para el correo electrónico.
        telefono (CharField): Campo para el número de teléfono.
        first_name (CharField): Campo para el nombre.
        last_name (CharField): Campo para el apellido.
        numero_documento (CharField): Campo para la cédula de identidad.
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'autofocus': True
        }),
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
    telefono = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': "El número de teléfono es obligatorio.",
            'unique': "Ya existe un usuario registrado con este número de teléfono.",
            'max_length': "El número de teléfono no puede tener más de 15 caracteres."
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
    numero_documento = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': "El número de documento es obligatorio.",
            'max_length': "El número de documento no puede tener más de 13 caracteres.",
            'unique': "Ya existe un usuario registrado con este número de documento."
        }
    )

    class Meta:
        """
        Meta información para el formulario.

        Attributes:
            model (Model): El modelo asociado al formulario.
            fields (tuple): Campos incluidos en el formulario.
        """
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'telefono', 'numero_documento', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario y personaliza los widgets de los campos de contraseña.
        """
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_numero_documento(self):
        """
        Valida que el número de documento sea numérico y tenga al menos 4 dígitos.

        Raises:
            ValidationError: Si el número de documento no es numérico o tiene menos de 4 dígitos.

        Returns:
            Cadena de texto: El número de documento validado.
        """
        documento = self.cleaned_data.get('numero_documento')
        if not documento.isdigit():
            raise ValidationError("El número de documento debe ser numérico.")
        if len(documento) < 4:
            raise ValidationError("El número de documento debe tener al menos 4 dígitos.")
        return documento
    
    def clean_telefono(self):
        """
        Valida que el número de teléfono sea numérico y tenga entre 6 y 15 dígitos.

        Raises:
            ValidationError: Si el número de teléfono no es numérico o no tiene entre 6 y 15 dígitos.

        Returns:
            Cadena de texto: El número de teléfono validado.
        """
        telefono = self.cleaned_data.get('telefono')
        if not telefono.isdigit():
            raise ValidationError("El número de teléfono debe ser numérico.")
        if len(telefono) < 6 or len(telefono) > 15:
            raise ValidationError("El número de teléfono debe tener entre 6 y 15 dígitos.")
        return telefono

    def clean_password1(self):
        """
        Validación personalizada para el campo de contraseña. Verifica que la contraseña tenga más de 8 caracteres,
        contenga al menos un caracter especial y al menos un número.

        Raises:
            ValidationError: Si la contraseña no cumple con los requisitos.

        Returns:
            Cadena de texto: La contraseña validada.
        """
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
        """
        Verifica que las contraseñas ingresadas en los campos password1 y password2 coincidan.

        Raises:
            ValidationError: Si las contraseñas no coinciden.

        Returns:
            Cadena de texto: La contraseña confirmada.
        """
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError("Las contraseñas no coinciden.")
        
        return password2

    def save(self, commit=True):
        """
        Guarda el usuario con los datos del formulario.

        Args:
            commit (bool): Si es True, guarda el usuario en la base de datos.

        Returns:
            Usuario: La instancia del usuario guardado.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.numero_documento = self.cleaned_data['numero_documento']
        if commit:
            user.save()
        return user


class RecuperarPasswordForm(PasswordResetForm):
    """
    Formulario personalizado para recuperación de contraseña.

    Attributes:
        email (EmailField): Campo para el correo electrónico desde el cual se solicita la recuperación.
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'autofocus': True
        }),
        error_messages={
            'required': "El correo electrónico es obligatorio.",
            'invalid': "Ingrese un correo electrónico válido."
        }
    )

    def clean_email(self):
        """
        Valida que el correo electrónico exista en la base de datos y que el usuario esté activo.

        Raises:
            ValidationError: Si no existe una cuenta activa asociada al correo electrónico.
        
        Returns:
            Cadena de texto: El correo electrónico validado.
        """
        email = self.cleaned_data.get('email')
        if email:
            # Verificar que el email esté registrado y que el usuario esté activo
            try:
                user = Usuario.objects.get(email=email, is_active=True)
            except Usuario.DoesNotExist:
                raise ValidationError("No existe una cuenta activa asociada a este correo electrónico.")
        return email


class EstablecerPasswordForm(SetPasswordForm):
    """
    Formulario personalizado para establecer nueva contraseña.

    Attributes:
        new_password1 (CharField): Campo para la nueva contraseña.
        new_password2 (CharField): Campo para confirmar la nueva contraseña.
    """
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nueva contraseña',
            'autofocus': True
        }),
        strip=False,
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar nueva contraseña'
        }),
        strip=False,
    )

    def clean_new_password1(self):
        """
        Validación personalizada para el campo de nueva contraseña. Verifica que la contraseña tenga más de 8 caracteres,
        contenga al menos un caracter especial y al menos un número.

        Raises:
            ValidationError: Si la contraseña no cumple con los requisitos.
        
        Returns:
            Cadena de texto: La nueva contraseña validada.
        """
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
    """
    Formulario para asignar roles a usuarios.

    Attributes:
        rol (ModelMultipleChoiceField): Campo para seleccionar múltiples roles.
    
    Note:
        El rol 'Administrador' está excluido de las opciones disponibles.
    """
    rol = forms.ModelMultipleChoiceField(
        queryset=Group.objects.exclude(name='Administrador').order_by('name'),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Roles disponibles',
        error_messages={
            'required': "Debes seleccionar al menos un rol."
        }
    )

    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario y personaliza el queryset del campo de roles para excluir los roles que el usuario ya tiene.

        Note:
            El rol 'Administrador' está excluido de las opciones disponibles.
        """
        usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)
        
        if usuario:
            # Excluir roles que el usuario ya tiene
            roles_actuales = usuario.groups.all()
            self.fields['rol'].queryset = Group.objects.exclude(
                name='Administrador'
            ).exclude(
                id__in=roles_actuales.values_list('id', flat=True)
            ).order_by('name')


class AsignarClienteForm(forms.Form):
    """
    Formulario para asignar clientes a usuarios.

    Attributes:
        clientes (ModelMultipleChoiceField): Campo para seleccionar múltiples clientes.
    """
    clientes = forms.ModelMultipleChoiceField(
        queryset=Cliente.objects.all().order_by('nombre'),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Clientes disponibles',
        error_messages={
            'required': "Debes seleccionar al menos un cliente."
        }
    )

    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario y personaliza el queryset del campo de clientes para excluir los clientes que el usuario ya tiene asignados.
        """
        usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)
        
        if usuario:
            # Excluir clientes que ya están asignados al usuario
            clientes_asignados = usuario.clientes_operados.all()
            self.fields['clientes'].queryset = Cliente.objects.exclude(
                id__in=clientes_asignados.values_list('id', flat=True)
            ).order_by('nombre')
            
            # Personalizar la etiqueta de cada cliente
            self.fields['clientes'].label_from_instance = lambda obj: f"{obj.nombre} ({obj.numero_documento})"
