"""
Formularios para el sistema TAUser (Terminal Autónomo de Usuario).

Este módulo contiene los formularios utilizados en el sistema TAUser para la entrada
y validación de datos por parte de los clientes en las terminales autónomas.

Classes:
    TokenForm: Formulario para ingreso y validación de tokens de transacción
    IngresoForm: Formulario para carga de archivos con información de billetes

Author: Equipo de desarrollo Global Exchange
Date: 2025
"""

from django import forms


class TokenForm(forms.Form):
    """
    Formulario para el ingreso y validación de tokens de transacción.
    
    Este formulario se utiliza en las terminales TAUser para que los clientes
    ingresen el token de 8 caracteres que recibieron del sistema principal
    para procesar sus transacciones de manera segura.
    
    Attributes:
        codigo (CharField): Campo de texto para ingresar el token alfanumérico
            - Máximo 8 caracteres
            - Solo acepta caracteres alfanuméricos (letras y números)
            - Campo obligatorio con enfoque automático
            - Incluye validación personalizada de formato
    
    Validation:
        - Verifica que el código tenga exactamente 8 caracteres
        - Valida que solo contenga caracteres alfanuméricos
        - Muestra mensajes de error personalizados
    
    Usage:
        form = TokenForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data['codigo']
            # Procesar el token...
    """
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
        """
        Valida el formato del código de transacción ingresado.
        
        Realiza validaciones específicas para garantizar que el token
        cumple con los requisitos de seguridad del sistema:
        - Longitud exacta de 8 caracteres
        - Solo caracteres alfanuméricos (sin espacios ni símbolos)
        
        Returns:
            str: El código validado y limpio
            
        Raises:
            ValidationError: Si el código no cumple con el formato requerido
            
        Note:
            Esta validación es crítica para la seguridad del sistema,
            ya que previene inyección de código malicioso y garantiza
            la integridad de los tokens de transacción.
        """
        codigo = self.cleaned_data.get('codigo')
        if not codigo.isalnum() or len(codigo) != 8:
            raise forms.ValidationError('El código debe ser alfanumérico y tener exactamente 8 caracteres.')
        return codigo
    
class IngresoForm(forms.Form):
    """
    Formulario para la carga de archivos con información de billetes.
    
    Este formulario se utiliza tanto para el ingreso de billetes a la caja fuerte
    del TAUser como para el procesamiento de pagos en transacciones. El archivo
    debe contener información estructurada sobre los billetes (moneda, valor, cantidad).
    
    Attributes:
        archivo (FileField): Campo de carga de archivo de texto plano
            - Solo acepta archivos .txt
            - Máximo 5MB de tamaño
            - Debe estar codificado en UTF-8
            - Contiene datos tabulados de billetes
    
    File Format Expected:
        Línea 1: "Ingreso" o "Extraccion" (para caja fuerte)
        Líneas siguientes: [Moneda][TAB][Valor][TAB][Cantidad]
        
        Ejemplo:
        ```
        Ingreso
        Dólar	1	50
        Dólar	5	20
        Guaraní	50000	10
        ```
    
    Validation:
        - Verifica extensión .txt
        - Limita tamaño a 5MB
        - Valida codificación UTF-8
        - Previene carga de archivos maliciosos
    
    Usage:
        form = IngresoForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = form.cleaned_data['archivo']
            # Procesar contenido del archivo...
    """
    archivo = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.txt'
        }),
        required=True,
        error_messages={'required': 'Debes seleccionar un archivo .txt.'}
    )

    def clean_archivo(self):
        """
        Valida el archivo cargado para garantizar seguridad e integridad.
        
        Realiza múltiples validaciones sobre el archivo subido para prevenir
        problemas de seguridad y garantizar que el contenido pueda ser procesado
        correctamente por el sistema TAUser.
        
        Validations Performed:
            1. Extensión de archivo: Solo acepta archivos .txt
            2. Tamaño de archivo: Máximo 5MB para prevenir DoS
            3. Codificación: Debe ser UTF-8 válido
            4. Contenido: Debe ser texto plano legible
        
        Returns:
            InMemoryUploadedFile: El archivo validado listo para procesamiento
            
        Raises:
            ValidationError: Si el archivo no cumple con alguna validación:
                - Extensión incorrecta
                - Tamaño excesivo
                - Codificación inválida
                - Contenido no legible
        
        Security Notes:
            - Previene carga de archivos ejecutables
            - Limita el tamaño para evitar ataques DoS
            - Valida la codificación para prevenir inyección
            - Resetea el puntero del archivo después de la validación
        """
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

class Token2FAForm(forms.Form):
    codigo_2fa = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autofocus': True,
            'maxlength': 6,
            'placeholder': 'Ingrese el código de 6 dígitos'
        }),
        required=True,
        error_messages={'required': 'Debes ingresar el código de verificación 2FA.'}
    )

    def clean_codigo_2fa(self):
        codigo = self.cleaned_data.get('codigo_2fa')
        if not codigo.isdigit() or len(codigo) != 6:
            raise forms.ValidationError('El código debe contener exactamente 6 dígitos numéricos.')
        return codigo
    