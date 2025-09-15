import pytest
from django.core.exceptions import ValidationError
from clientes.forms import ClienteForm
from clientes.models import Cliente


@pytest.mark.django_db
class TestClienteForm:
    """
    Tests para el formulario ClienteForm
    """
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Configuración inicial para los tests"""
        self.datos_validos = {
            'nombre': 'Juan Pérez',
            'tipoDocCliente': 'CI',
            'docCliente': '1234567890',
            'correoElecCliente': 'juan@example.com',
            'telefono': '0981123456',
            'tipoCliente': 'F',
            'direccion': 'Asunción, Paraguay',
            'ocupacion': 'Ingeniero',
            'declaracion_jurada': True,
            'segmento': 'minorista'
        }
    
    def test_formulario_valido(self):
        """Test para formulario con datos válidos"""
        form = ClienteForm(data=self.datos_validos)
        
        assert form.is_valid()
        cliente = form.save()
        assert cliente.nombre == 'Juan Pérez'
        print("✓ Test formulario_valido: Formulario válido y cliente guardado correctamente")
    
    def test_campos_requeridos(self):
        """Test para verificar validación de campos requeridos"""
        form = ClienteForm(data={})
        
        assert not form.is_valid()
        
        campos_requeridos = ['nombre', 'tipoDocCliente', 'docCliente', 
                           'correoElecCliente', 'telefono', 'tipoCliente', 
                           'direccion', 'ocupacion', 'segmento']
        
        for campo in campos_requeridos:
            assert campo in form.errors
        
        print("✓ Test campos_requeridos: Validación de campos requeridos funcionando")
    
    def test_mensajes_error_personalizados_nombre(self):
        """Test para verificar mensajes de error personalizados del nombre"""
        # Test campo vacío
        datos = self.datos_validos.copy()
        datos['nombre'] = ''
        form = ClienteForm(data=datos)
        
        assert not form.is_valid()
        assert form.errors['nombre'][0] == 'Debes ingresar el nombre.'
        
        # Test campo muy largo
        datos['nombre'] = 'a' * 101
        form = ClienteForm(data=datos)
        
        assert not form.is_valid()
        assert form.errors['nombre'][0] == 'El nombre no puede exceder los 100 caracteres.'
        
        print("✓ Test mensajes_error_personalizados_nombre: Mensajes de error correctos")
    
    def test_mensajes_error_personalizados_documento(self):
        """Test para verificar mensajes de error personalizados del documento"""
        # Test campo vacío
        datos = self.datos_validos.copy()
        datos['docCliente'] = ''
        form = ClienteForm(data=datos)
        
        assert not form.is_valid()
        assert form.errors['docCliente'][0] == 'Debes ingresar el número de documento.'
        
        # Test campo muy largo
        datos['docCliente'] = '1' * 21
        form = ClienteForm(data=datos)
        
        assert not form.is_valid()
        assert form.errors['docCliente'][0] == 'El documento no puede exceder los 20 caracteres.'
        
        print("✓ Test mensajes_error_personalizados_documento: Mensajes de error correctos")
    
    def test_mensajes_error_personalizados_correo(self):
        """Test para verificar mensajes de error personalizados del correo"""
        # Test campo vacío
        datos = self.datos_validos.copy()
        datos['correoElecCliente'] = ''
        form = ClienteForm(data=datos)
        
        assert not form.is_valid()
        assert form.errors['correoElecCliente'][0] == 'Debes ingresar un correo electrónico.'
        
        # Test correo inválido
        datos['correoElecCliente'] = 'correo_invalido'
        form = ClienteForm(data=datos)
        
        assert not form.is_valid()
        assert form.errors['correoElecCliente'][0] == 'Debes ingresar un correo electrónico válido.'
        
        print("✓ Test mensajes_error_personalizados_correo: Mensajes de error correctos")
    
    def test_validacion_telefono_solo_numeros(self):
        """Test para validar que el teléfono contenga solo números"""
        # Test teléfono con letras
        datos = self.datos_validos.copy()
        datos['telefono'] = '098abc123'
        form = ClienteForm(data=datos)
        
        assert not form.is_valid()
        assert form.errors['telefono'][0] == 'El teléfono debe contener solo números'
        
        # Test teléfono con caracteres especiales
        datos['telefono'] = '0981-123-456'
        form = ClienteForm(data=datos)
        
        assert not form.is_valid()
        assert form.errors['telefono'][0] == 'El teléfono debe contener solo números'
        
        # Test teléfono válido
        datos['telefono'] = '0981123456'
        form = ClienteForm(data=datos)
        
        assert form.is_valid()
        
        print("✓ Test validacion_telefono_solo_numeros: Validación de teléfono funcionando")
    
    def test_validacion_documento_solo_numeros(self):
        """Test para validar que el documento contenga solo números"""
        # Test documento con letras
        datos = self.datos_validos.copy()
        datos['docCliente'] = '123abc456'
        form = ClienteForm(data=datos)
        
        assert not form.is_valid()
        assert form.errors['docCliente'][0] == 'El documento debe contener solo números'
        
        # Test documento con caracteres especiales
        datos['docCliente'] = '123-456-789'
        form = ClienteForm(data=datos)
        
        assert not form.is_valid()
        assert form.errors['docCliente'][0] == 'El documento debe contener solo números'
        
        # Test documento válido
        datos['docCliente'] = '1234567890'
        form = ClienteForm(data=datos)
        
        assert form.is_valid()
        
        print("✓ Test validacion_documento_solo_numeros: Validación de documento funcionando")
    
    def test_choices_tipo_cliente(self):
        """Test para verificar choices de tipo de cliente"""
        # Test tipo cliente inválido
        datos = self.datos_validos.copy()
        datos['tipoCliente'] = 'X'
        form = ClienteForm(data=datos)
        
        assert not form.is_valid()
        assert 'tipoCliente' in form.errors
        
        # Test tipos cliente válidos
        for tipo, _ in Cliente.TIPO_CLIENTE_CHOICES:
            datos['tipoCliente'] = tipo
            form = ClienteForm(data=datos)
            assert form.is_valid()
        
        print("✓ Test choices_tipo_cliente: Validación de choices funcionando")
    
    def test_choices_tipo_documento(self):
        """Test para verificar choices de tipo de documento"""
        # Test tipo documento inválido
        datos = self.datos_validos.copy()
        datos['tipoDocCliente'] = 'XX'
        form = ClienteForm(data=datos)
        
        assert not form.is_valid()
        assert 'tipoDocCliente' in form.errors
        
        # Test tipos documento válidos
        for tipo, _ in Cliente.TIPO_DOCUMENTO_CHOICES:
            datos['tipoDocCliente'] = tipo
            form = ClienteForm(data=datos)
            assert form.is_valid()
        
        print("✓ Test choices_tipo_documento: Validación de choices funcionando")
    
    def test_choices_segmento(self):
        """Test para verificar choices de segmento"""
        # Test segmento inválido
        datos = self.datos_validos.copy()
        datos['segmento'] = 'invalido'
        form = ClienteForm(data=datos)
        
        assert not form.is_valid()
        assert 'segmento' in form.errors
        
        # Test segmentos válidos
        for segmento, _ in Cliente.SEGMENTO_CHOICES:
            datos['segmento'] = segmento
            form = ClienteForm(data=datos)
            assert form.is_valid()
        
        print("✓ Test choices_segmento: Validación de choices funcionando")
    
    def test_declaracion_jurada_opcional(self):
        """Test para verificar que declaración jurada es opcional"""
        # Sin declaración jurada
        datos = self.datos_validos.copy()
        del datos['declaracion_jurada']
        form = ClienteForm(data=datos)
        
        assert form.is_valid()
        cliente = form.save()
        assert not cliente.declaracion_jurada
        
        # Con declaración jurada False
        datos['declaracion_jurada'] = False
        form = ClienteForm(data=datos)
        
        assert form.is_valid()
        
        # Con declaración jurada True
        datos['declaracion_jurada'] = True
        form = ClienteForm(data=datos)
        
        assert form.is_valid()
        
        print("✓ Test declaracion_jurada_opcional: Campo opcional funcionando correctamente")
    
    def test_longitudes_maximas(self):
        """Test para verificar longitudes máximas de los campos"""
        casos = [
            ('telefono', '1' * 21, 'El teléfono no puede exceder los 20 caracteres.'),
            ('direccion', 'a' * 101, 'La dirección no puede exceder los 100 caracteres.'),
            ('ocupacion', 'a' * 31, 'La ocupación no puede exceder los 30 caracteres.'),
        ]
        
        for campo, valor_largo, mensaje_esperado in casos:
            datos = self.datos_validos.copy()
            datos[campo] = valor_largo
            form = ClienteForm(data=datos)
            
            assert not form.is_valid()
            assert form.errors[campo][0] == mensaje_esperado
        
        print("✓ Test longitudes_maximas: Validación de longitudes máximas funcionando")
    
    def test_unicidad_documento_en_edicion(self):
        """Test para verificar manejo de unicidad en edición"""
        # Crear cliente inicial
        cliente1 = Cliente.objects.create(**self.datos_validos)
        
        # Crear segundo cliente
        datos2 = self.datos_validos.copy()
        datos2['docCliente'] = '0987654321'
        datos2['correoElecCliente'] = 'otro@example.com'
        cliente2 = Cliente.objects.create(**datos2)
        
        # Intentar editar cliente2 con documento de cliente1
        form = ClienteForm(data=self.datos_validos, instance=cliente2)
        
        assert not form.is_valid()
        # El error puede variar según la implementación de Django
        # pero debe indicar que el documento ya existe
        
        print("✓ Test unicidad_documento_en_edicion: Validación de unicidad en edición funcionando")