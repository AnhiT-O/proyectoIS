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
    permisos = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.exclude(
            codename__startswith='add_'
        ).exclude(
            codename__startswith='change_'
        ).exclude(
            codename__startswith='delete_'
        ).exclude(
            codename__startswith='view_'
        ),
        widget=PermissionCheckboxSelectMultiple,
        required=False,
        label="Permisos"
    )

    def __init__(self, *args, **kwargs):
        super(RolForm, self).__init__(*args, **kwargs)
        
        # Si estamos editando un rol existente, establecer los permisos actuales
        if self.instance.pk:
            self.fields['permisos'].initial = self.instance.permissions.all()
        
        # Personalizar los widgets con clases de estilo
        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingrese el nombre del rol'
        })
        
        self.fields['descripcion'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingrese una descripción para el rol',
            'rows': '4'
        })

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
