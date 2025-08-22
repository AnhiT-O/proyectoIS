from django import forms
from .models import Rol
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

class RolForm(forms.ModelForm):
    permisos = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(RolForm, self).__init__(*args, **kwargs)
        # Obtener todos los permisos disponibles y organizarlos por modelo
        permisos = []
        content_types = ContentType.objects.all().order_by('model')
        for ct in content_types:
            ct_perms = Permission.objects.filter(content_type=ct)
            if ct_perms.exists():
                permisos.extend([(p.id, f"{ct.model.capitalize()}: {p.name}") for p in ct_perms])
        
        self.fields['permisos'].choices = permisos
        
        # Si estamos editando un rol existente, marcar los permisos seleccionados
        if self.instance.pk:
            self.initial['permisos'] = self.instance.permisos.values_list('id', flat=True)
        
        # Personalizar los widgets con clases de estilo
        self.fields['nombre'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingrese el nombre del rol'
        })
        self.fields['descripcion'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingrese una descripción para el rol',
            'rows': '4'
        })
        self.fields['activo'].widget.attrs.update({
            'class': 'form-check-input'
        })

    class Meta:
        model = Rol
        fields = ['nombre', 'descripcion', 'permisos', 'activo']
