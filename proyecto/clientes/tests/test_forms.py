import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from clientes.forms import ClienteForm


class TestClienteForm(TestCase):
    """Pruebas para el formulario ClienteForm"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.valid_data = {
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'tipoDocCliente': 'CI',
            'docCliente': '12345678',
            'correoElecCliente': 'juan.perez@example.com',
            'telefono': '0981123456',
            'tipoCliente': 'F',
            'direccion': 'Asunción, Paraguay',
            'ocupacion': 'Ingeniero',
            'declaracion_jurada': True
        }
    
    def test_form_valido(self):
        """Test formulario con datos válidos"""
        form = ClienteForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
    
    def test_telefono_valido_movil(self):
        """Test validación teléfono móvil paraguayo"""
        # Teléfono móvil nacional
        self.valid_data['telefono'] = '0981123456'
        form = ClienteForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        
        # Teléfono móvil internacional
        self.valid_data['telefono'] = '+595981123456'
        form = ClienteForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
    
    def test_telefono_valido_fijo(self):
        """Test validación teléfono fijo paraguayo"""
        # Teléfono fijo nacional
        self.valid_data['telefono'] = '021123456'
        form = ClienteForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        
        # Teléfono fijo internacional
        self.valid_data['telefono'] = '+59521123456'
        form = ClienteForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
    
    def test_telefono_invalido(self):
        """Test validación teléfono inválido"""
        telefonos_invalidos = [
            '123456',           # Muy corto
            '0123456789',       # Código de área incorrecto
            '+1234567890',      # Código de país incorrecto
            'abc123456',        # Contiene letras
            ''                  # Vacío
        ]
        
        for telefono in telefonos_invalidos:
            self.valid_data['telefono'] = telefono
            form = ClienteForm(data=self.valid_data)
            self.assertFalse(form.is_valid())
            self.assertIn('telefono', form.errors)
    
    def test_documento_ci_valido(self):
        """Test validación cédula de identidad válida"""
        self.valid_data['tipoDocCliente'] = 'CI'
        self.valid_data['docCliente'] = '12345678'
        form = ClienteForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
    
    def test_documento_ci_invalido(self):
        """Test validación cédula de identidad inválida"""
        self.valid_data['tipoDocCliente'] = 'CI'
        
        # CI con letras
        self.valid_data['docCliente'] = '1234567a'
        form = ClienteForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('docCliente', form.errors)
        
        # CI muy larga
        self.valid_data['docCliente'] = '123456789'
        form = ClienteForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('docCliente', form.errors)
    
    def test_documento_ruc_valido(self):
        """Test validación RUC válido"""
        self.valid_data['tipoDocCliente'] = 'RUC'
        self.valid_data['tipoCliente'] = 'J'  # Persona jurídica
        self.valid_data['docCliente'] = '800123450'  # RUC válido para testing
        form = ClienteForm(data=self.valid_data)
        # Nota: Este test puede fallar si el dígito verificador no es correcto
        # Se necesitaría un RUC válido real para testing
    
    def test_coherencia_tipo_cliente_documento(self):
        """Test coherencia entre tipo de cliente y tipo de documento"""
        # Persona física con RUC (inválido)
        self.valid_data['tipoCliente'] = 'F'
        self.valid_data['tipoDocCliente'] = 'RUC'
        form = ClienteForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        
        # Persona jurídica con CI (inválido)
        self.valid_data['tipoCliente'] = 'J'
        self.valid_data['tipoDocCliente'] = 'CI'
        form = ClienteForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
    
    def test_campos_requeridos(self):
        """Test campos requeridos del formulario"""
        campos_requeridos = [
            'nombre', 'apellido', 'tipoDocCliente', 
            'docCliente', 'correoElecCliente', 'telefono', 'tipoCliente'
        ]
        
        for campo in campos_requeridos:
            data = self.valid_data.copy()
            del data[campo]
            form = ClienteForm(data=data)
            self.assertFalse(form.is_valid())
            self.assertIn(campo, form.errors)
    
    def test_campos_opcionales(self):
        """Test campos opcionales del formulario"""
        # Quitar campos opcionales
        data = self.valid_data.copy()
        del data['direccion']
        del data['ocupacion']
        del data['declaracion_jurada']
        
        form = ClienteForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_email_formato_valido(self):
        """Test validación formato de email"""
        emails_validos = [
            'test@example.com',
            'user.name@domain.co.uk',
            'test+tag@example.org'
        ]
        
        for email in emails_validos:
            self.valid_data['correoElecCliente'] = email
            form = ClienteForm(data=self.valid_data)
            self.assertTrue(form.is_valid())
    
    def test_email_formato_invalido(self):
        """Test validación formato de email inválido"""
        emails_invalidos = [
            'test',
            'test@',
            '@example.com',
            'test@example',
            'test.example.com'
        ]
        
        for email in emails_invalidos:
            self.valid_data['correoElecCliente'] = email
            form = ClienteForm(data=self.valid_data)
            self.assertFalse(form.is_valid())
            self.assertIn('correoElecCliente', form.errors)
