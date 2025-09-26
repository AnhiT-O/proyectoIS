from django import forms
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import Roles

class PermissionCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    """Widget personalizado para mostrar solo la descripción de los permisos"""
    
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

    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
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
            'rows': 4
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
        super(RolForm, self).__init__(*args, **kwargs)
        
        # Si estamos editando un rol existente, establecer los permisos actuales
        if self.instance.pk:
            self.fields['permisos'].initial = self.instance.permissions.all()

    def save(self, commit=True):
        rol = super().save(commit=commit)
        if commit:
            # Asignar permisos seleccionados
            permisos = self.cleaned_data.get('permisos', [])
            rol.permissions.set(permisos)
        return rol

    class Meta:
        model = Roles
        fields = ['name', 'descripcion']
