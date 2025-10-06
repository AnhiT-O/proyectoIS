from django import forms

class TokenForm(forms.Form):
    codigo = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autofocus': True,
            'maxlength': 8
        }),
        required=True,
        error_messages={'required': 'Debes ingresar el código de transacción.'}
    )

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if not codigo.isalnum() or len(codigo) != 8:
            raise forms.ValidationError('El código debe ser alfanumérico y tener exactamente 8 caracteres.')
        return codigo
    
class CajaFuerteForm(forms.Form):
    archivo = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.txt'
        }),
        required=True,
        error_messages={'required': 'Debes seleccionar un archivo .txt.'}
    )

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            # Verificar que sea un archivo .txt
            if not archivo.name.endswith('.txt'):
                raise forms.ValidationError('El archivo debe tener extensión .txt.')
            
            # Verificar el tamaño del archivo (máximo 5MB)
            if archivo.size > 5 * 1024 * 1024:
                raise forms.ValidationError('El archivo no debe superar los 5MB.')
            
            # Verificar que el contenido sea texto plano
            try:
                archivo.seek(0)
                contenido = archivo.read().decode('utf-8')
                archivo.seek(0)  # Resetear el puntero del archivo
            except UnicodeDecodeError:
                raise forms.ValidationError('El archivo debe contener texto válido en UTF-8.')
        
        return archivo
    
class BilleteForm(forms.Form):
    archivo = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.txt'
        }),
        required=True,
        error_messages={'required': 'Debes seleccionar un archivo .txt.'}
    )

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            # Verificar que sea un archivo .txt
            if not archivo.name.endswith('.txt'):
                raise forms.ValidationError('El archivo debe tener extensión .txt.')
            
            # Verificar el tamaño del archivo (máximo 5MB)
            if archivo.size > 5 * 1024 * 1024:
                raise forms.ValidationError('El archivo no debe superar los 5MB.')
            
            # Verificar que el contenido sea texto plano
            try:
                archivo.seek(0)
                contenido = archivo.read().decode('utf-8')
                archivo.seek(0)  # Resetear el puntero del archivo
            except UnicodeDecodeError:
                raise forms.ValidationError('El archivo debe contener texto válido en UTF-8.')
        
        return archivo
    