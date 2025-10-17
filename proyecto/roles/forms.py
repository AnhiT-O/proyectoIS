from django import forms
from django.contrib.auth.models import Permission
from .models import Roles

class PermissionCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    """
    Widget personalizado para mostrar solo la descripción de los permisos.
    Extiende CheckboxSelectMultiple para personalizar la representación de las opciones.

    Args:
        forms (CheckboxSelectMultiple): Widget base de Django para selección múltiple con checkboxes.
    
    Returns:
        diccionario: Diccionario que representa una opción en el widget, con la etiqueta personalizada.
    """
    
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        # Si el valor es un Permission, usar su descripción (name) en lugar del codename
        if value and hasattr(value, 'instance'):
            try:
                permission = Permission.objects.get(pk=value.instance.pk)
                option['label'] = permission.name  # Usar el nombre/descripción del permiso
            except Permission.DoesNotExist:
                pass
        elif value:
            try:
                permission = Permission.objects.get(pk=value)
                option['label'] = permission.name  # Usar el nombre/descripción del permiso
            except Permission.DoesNotExist:
                pass
        return option

class RolForm(forms.ModelForm):
    """
    Formulario para crear y editar roles, incluyendo la asignación de permisos personalizados.

    Attributes:
        name (CharField): Campo para el nombre del rol. Máximo 100 caracteres.
        descripcion (CharField): Campo para la descripción del rol.
        permisos (ModelMultipleChoiceField): Campo para seleccionar múltiples permisos personalizados. Opcional.

    Note:
        -   Este formulario excluye los permisos predeterminados de Django (add, change, delete, view).
    """

    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        }),
        error_messages={
            'required': 'Debes ingresar un nombre.',
            'max_length': 'El nombre no puede exceder los 100 caracteres.',
        }
    )

    descripcion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6
        })
    )

    permisos = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.exclude(
            codename__startswith='add_'
        ).exclude(
            codename__startswith='change_'
        ).exclude(
            codename__startswith='delete_'
        ).exclude(
            codename__startswith='view_'
        ), # excluye permisos predeterminados de Django
        widget=PermissionCheckboxSelectMultiple,
        required=False
    )

    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario y, si se está editando un rol existente, marca los permisos que ya tiene.
        """

        super(RolForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['permisos'].initial = self.instance.permissions.all()

    def save(self, commit=True):
        """
        Guarda el rol y asigna los permisos seleccionados.

        Args:
            commit (bool): Si es True, guarda el rol en la base de datos inmediatamente.

        Returns:
            Roles: La instancia del rol guardado.
        """

        rol = super().save(commit=commit)
        if commit:
            # Asignar permisos seleccionados
            permisos = self.cleaned_data.get('permisos', [])
            rol.permissions.set(permisos)
        return rol

    class Meta:
        """
        Meta información del formulario.

        Attributes:
            model (Roles): El modelo asociado al formulario.
            fields (list): Lista de campos incluidos en el formulario.
        """
        model = Roles
        fields = ['name', 'descripcion']
