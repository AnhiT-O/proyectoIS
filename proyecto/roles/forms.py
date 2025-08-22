from django import forms
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import Roles

class RolForm(forms.ModelForm):
    permisos = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=forms.CheckboxSelectMultiple,
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
