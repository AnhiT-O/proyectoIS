from django import forms
from django.core.exceptions import ValidationError
import re
from .models import Cliente

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'nombre', 
            'apellido',
            'tipoDocCliente',
            'docCliente',
            'correoElecCliente',
            'telefono',
            'tipoCliente',
            'direccion',
            'ocupacion',
            'declaracion_jurada'
        ]
        widgets = {
            'tipoDocCliente': forms.Select(attrs={'class': 'form-control'}),
            'tipoCliente': forms.Select(attrs={'class': 'form-control'}),
            'declaracion_jurada': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: 0981123456 o +595981123456'
            }),
            'docCliente': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de documento'
            })
        }

    def clean_telefono(self):
        """
        Valida el formato del número de teléfono paraguayo.
        Acepta formatos: 0981123456, +595981123456, 595981123456
        """
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            # Remover espacios y guiones
            telefono_limpio = re.sub(r'[\s\-]', '', telefono)
            
            # Patrones válidos para Paraguay
            patrones = [
                r'^0(9[6-9])\d{7}$',           # 09XXXXXXXX (móvil)
                r'^0(2[1-9])\d{6,7}$',         # 02XXXXXXX (fijo)
                r'^\+595(9[6-9])\d{7}$',       # +5959XXXXXXXX (móvil internacional)
                r'^\+595(2[1-9])\d{6,7}$',     # +59521XXXXXXX (fijo internacional)
                r'^595(9[6-9])\d{7}$',         # 5959XXXXXXXX (móvil sin +)
                r'^595(2[1-9])\d{6,7}$'        # 59521XXXXXXX (fijo sin +)
            ]
            
            if not any(re.match(patron, telefono_limpio) for patron in patrones):
                raise ValidationError(
                    'Formato de teléfono inválido. Use: 0981123456 (móvil), '
                    '021123456 (fijo), +595981123456 (internacional)'
                )
        
        return telefono

    def clean_docCliente(self):
        """
        Valida el número de documento según el tipo seleccionado.
        CI: Solo números, 1-8 dígitos
        RUC: Formato específico paraguayo
        """
        doc_cliente = self.cleaned_data.get('docCliente')
        tipo_doc = self.cleaned_data.get('tipoDocCliente')
        
        if doc_cliente and tipo_doc:
            # Remover espacios, puntos y guiones
            doc_limpio = re.sub(r'[\s\.\-]', '', doc_cliente)
            
            if tipo_doc == 'CI':
                # Cédula de Identidad: solo números, 1-8 dígitos
                if not re.match(r'^\d{1,8}$', doc_limpio):
                    raise ValidationError(
                        'La Cédula de Identidad debe contener solo números (1-8 dígitos)'
                    )
                    
            elif tipo_doc == 'RUC':
                # RUC: formato XXXXXXXX-D (8 dígitos + guión + dígito verificador)
                if not re.match(r'^\d{8}\d{1}$', doc_limpio):
                    raise ValidationError(
                        'El RUC debe tener el formato: 12345678-9 (8 dígitos + dígito verificador)'
                    )
                
                # Validar dígito verificador del RUC
                if not self._validar_digito_verificador_ruc(doc_limpio):
                    raise ValidationError('El dígito verificador del RUC es incorrecto')
        
        return doc_cliente

    def _validar_digito_verificador_ruc(self, ruc_limpio):
        """
        Valida el dígito verificador del RUC paraguayo.
        Algoritmo: módulo 11 con pesos 2-8
        """
        if len(ruc_limpio) != 9:
            return False
            
        # Extraer los primeros 8 dígitos y el dígito verificador
        base = ruc_limpio[:8]
        digito_verificador = int(ruc_limpio[8])
        
        # Calcular dígito verificador
        pesos = [2, 3, 4, 5, 6, 7, 8, 9]
        suma = sum(int(digito) * peso for digito, peso in zip(reversed(base), pesos))
        
        resto = suma % 11
        if resto < 2:
            digito_calculado = 0
        else:
            digito_calculado = 11 - resto
            
        return digito_verificador == digito_calculado

    def clean(self):
        """
        Validaciones adicionales que requieren múltiples campos
        """
        cleaned_data = super().clean()
        tipo_cliente = cleaned_data.get('tipoCliente')
        tipo_doc = cleaned_data.get('tipoDocCliente')
        
        # Validar coherencia entre tipo de cliente y tipo de documento
        if tipo_cliente and tipo_doc:
            if tipo_cliente == 'F' and tipo_doc != 'CI':
                raise ValidationError(
                    'Las personas físicas deben usar Cédula de Identidad'
                )
            elif tipo_cliente == 'J' and tipo_doc != 'RUC':
                raise ValidationError(
                    'Las personas jurídicas deben usar RUC'
                )
        
        return cleaned_data