import pytest
from django.core.exceptions import ValidationError
from django.forms import Form
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
            'segmento': 'minorista',
            'declaracion_jurada': True
        }
    
    def test_formulario_valido(self):
        """Test para verificar que el formulario acepta datos válidos"""
        form = ClienteForm(data=self.datos_validos)
        
        assert form.is_valid(), f"El formulario debería ser válido, pero tiene errores: {form.errors}"
        
        # Verificar que se puede guardar
        cliente = form.save()
        assert cliente.pk is not None, "El cliente debería haberse guardado correctamente"
        assert cliente.nombre == 'Juan Pérez', "El nombre del cliente no coincide"
        print("✓ Test formulario_valido: Formulario con datos válidos funciona correctamente")
    
    def test_campos_requeridos(self):
        """Test para verificar validación de campos requeridos"""
        # Datos vacíos
        form = ClienteForm(data={})
        
        assert not form.is_valid(), "El formulario no debería ser válido con datos vacíos"
        
        campos_requeridos = [
            'nombre', 'tipoDocCliente', 'docCliente', 'correoElecCliente',
            'telefono', 'tipoCliente', 'direccion', 'ocupacion', 'segmento'
        ]
        
        for campo in campos_requeridos:
            assert campo in form.errors, f"El campo '{campo}' debería ser requerido y mostrar error"
        
        print("✓ Test campos_requeridos: Validación de campos requeridos funcionando")
    
    def test_validacion_telefono_solo_numeros(self):
        """Test para verificar que el teléfono solo acepta números"""
        datos = self.datos_validos.copy()
        datos['telefono'] = '098-112-3456'  # Con guiones
        
        form = ClienteForm(data=datos)
        
        assert not form.is_valid(), "El formulario no debería ser válido con teléfono que contiene caracteres especiales"
        assert 'telefono' in form.errors, "Debería haber error en el campo teléfono"
        assert 'El teléfono debe contener solo números' in str(form.errors['telefono']), "El mensaje de error no es el esperado"
        
        # Test con letras
        datos['telefono'] = '098abc1234'
        form = ClienteForm(data=datos)
        
        assert not form.is_valid(), "El formulario no debería ser válido con teléfono que contiene letras"
        assert 'telefono' in form.errors, "Debería haber error en el campo teléfono con letras"
        
        print("✓ Test validacion_telefono_solo_numeros: Validación de teléfono funcionando")
    
    def test_validacion_documento_solo_numeros(self):
        """Test para verificar que el documento solo acepta números"""
        datos = self.datos_validos.copy()
        datos['docCliente'] = '123-456-789'  # Con guiones
        
        form = ClienteForm(data=datos)
        
        assert not form.is_valid(), "El formulario no debería ser válido con documento que contiene caracteres especiales"
        assert 'docCliente' in form.errors, "Debería haber error en el campo documento"
        assert 'El documento debe contener solo números' in str(form.errors['docCliente']), "El mensaje de error no es el esperado"
        
        # Test con letras
        datos['docCliente'] = '123abc456'
        form = ClienteForm(data=datos)
        
        assert not form.is_valid(), "El formulario no debería ser válido con documento que contiene letras"
        assert 'docCliente' in form.errors, "Debería haber error en el campo documento con letras"
        
        print("✓ Test validacion_documento_solo_numeros: Validación de documento funcionando")
    
    def test_validacion_email_formato(self):
        """Test para verificar validación de formato de email"""
        datos = self.datos_validos.copy()
        
        # Email sin @
        datos['correoElecCliente'] = 'email_invalido'
        form = ClienteForm(data=datos)
        
        assert not form.is_valid(), "El formulario no debería ser válido con email sin @"
        assert 'correoElecCliente' in form.errors, "Debería haber error en el campo email"
        
        # Email sin dominio
        datos['correoElecCliente'] = 'usuario@'
        form = ClienteForm(data=datos)
        
        assert not form.is_valid(), "El formulario no debería ser válido con email sin dominio"
        assert 'correoElecCliente' in form.errors, "Debería haber error en el campo email sin dominio"
        
        print("✓ Test validacion_email_formato: Validación de formato de email funcionando")
    
    def test_choices_tipo_cliente(self):
        """Test para verificar validación de choices de tipo de cliente"""
        datos = self.datos_validos.copy()
        datos['tipoCliente'] = 'X'  # Valor inválido
        
        form = ClienteForm(data=datos)
        
        assert not form.is_valid(), "El formulario no debería ser válido con tipo de cliente inválido"
        assert 'tipoCliente' in form.errors, "Debería haber error en el campo tipo de cliente"
        
        # Test con valores válidos
        for tipo_valido in ['F', 'J']:
            datos['tipoCliente'] = tipo_valido
            form = ClienteForm(data=datos)
            
            # No debería haber error en tipoCliente (puede haber otros errores)
            if not form.is_valid():
                assert 'tipoCliente' not in form.errors, f"No debería haber error con tipo '{tipo_valido}'"
        
        print("✓ Test choices_tipo_cliente: Validación de choices de tipo de cliente funcionando")
    
    def test_choices_tipo_documento(self):
        """Test para verificar validación de choices de tipo de documento"""
        datos = self.datos_validos.copy()
        datos['tipoDocCliente'] = 'XX'  # Valor inválido
        
        form = ClienteForm(data=datos)
        
        assert not form.is_valid(), "El formulario no debería ser válido con tipo de documento inválido"
        assert 'tipoDocCliente' in form.errors, "Debería haber error en el campo tipo de documento"
        
        # Test con valores válidos
        for tipo_valido in ['CI', 'RUC']:
            datos['tipoDocCliente'] = tipo_valido
            form = ClienteForm(data=datos)
            
            # No debería haber error en tipoDocCliente (puede haber otros errores)
            if not form.is_valid():
                assert 'tipoDocCliente' not in form.errors, f"No debería haber error con tipo '{tipo_valido}'"
        
        print("✓ Test choices_tipo_documento: Validación de choices de tipo de documento funcionando")
    
    def test_choices_segmento(self):
        """Test para verificar validación de choices de segmento"""
        datos = self.datos_validos.copy()
        datos['segmento'] = 'premium'  # Valor inválido
        
        form = ClienteForm(data=datos)
        
        assert not form.is_valid(), "El formulario no debería ser válido con segmento inválido"
        assert 'segmento' in form.errors, "Debería haber error en el campo segmento"
        
        # Test con valores válidos
        for segmento_valido in ['minorista', 'corporativo', 'vip']:
            datos['segmento'] = segmento_valido
            form = ClienteForm(data=datos)
            
            # No debería haber error en segmento (puede haber otros errores)
            if not form.is_valid():
                assert 'segmento' not in form.errors, f"No debería haber error con segmento '{segmento_valido}'"
        
        print("✓ Test choices_segmento: Validación de choices de segmento funcionando")
    
    def test_longitud_maxima_campos(self):
        """Test para verificar longitud máxima de campos"""
        datos = self.datos_validos.copy()
        
        # Nombre muy largo (máximo 100)
        datos['nombre'] = 'a' * 101
        form = ClienteForm(data=datos)

        assert 'nombre' in form.errors, "Debería haber error en el campo nombre"
        
        # Documento muy largo (máximo 20)
        datos = self.datos_validos.copy()
        datos['docCliente'] = '1' * 21
        form = ClienteForm(data=datos)
        
        assert not form.is_valid(), "El formulario no debería ser válido con documento muy largo"
        assert 'docCliente' in form.errors, "Debería haber error en el campo documento"
        
        # Teléfono muy largo (máximo 20)
        datos = self.datos_validos.copy()
        datos['telefono'] = '1' * 21
        form = ClienteForm(data=datos)
        
        assert not form.is_valid(), "El formulario no debería ser válido con teléfono muy largo"
        assert 'telefono' in form.errors, "Debería haber error en el campo teléfono"
        
        # Ocupación muy larga (máximo 30)
        datos = self.datos_validos.copy()
        datos['ocupacion'] = 'a' * 31
        form = ClienteForm(data=datos)
        
        assert not form.is_valid(), "El formulario no debería ser válido con ocupación muy larga"
        assert 'ocupacion' in form.errors, "Debería haber error en el campo ocupación"
        
        print("✓ Test longitud_maxima_campos: Validación de longitud máxima funcionando")
    
    def test_campo_declaracion_jurada_opcional(self):
        """Test para verificar que declaracion_jurada es opcional"""
        datos = self.datos_validos.copy()
        del datos['declaracion_jurada']  # Omitir campo opcional
        
        form = ClienteForm(data=datos)
        
        assert form.is_valid(), f"El formulario debería ser válido sin declaracion_jurada, errores: {form.errors}"
        
        cliente = form.save()
        assert cliente.declaracion_jurada == False, "El valor por defecto de declaracion_jurada debe ser False"
        
        print("✓ Test campo_declaracion_jurada_opcional: Campo opcional funcionando correctamente")
    
    def test_formulario_incluye_todos_los_campos_necesarios(self):
        """Test para verificar que el formulario incluye todos los campos del modelo"""
        form = ClienteForm()
        
        campos_esperados = [
            'nombre', 'tipoDocCliente', 'docCliente', 'correoElecCliente',
            'telefono', 'tipoCliente', 'direccion', 'ocupacion', 'segmento',
            'declaracion_jurada'
        ]
        
        for campo in campos_esperados:
            assert campo in form.fields, f"El campo '{campo}' debería estar en el formulario"
        
        # Verificar que no incluye campos que no deberían estar
        campos_no_esperados = ['beneficio_segmento', 'created_at', 'updated_at', 'usuarios']
        
        for campo in campos_no_esperados:
            assert campo not in form.fields, f"El campo '{campo}' no debería estar en el formulario"
        
        print("✓ Test formulario_incluye_todos_los_campos_necesarios: Campos del formulario correctos")
    
    def test_widgets_css_classes(self):
        """Test para verificar que los widgets tienen las clases CSS correctas"""
        form = ClienteForm()
        
        # Verificar que la mayoría de campos tienen la clase 'form-control'
        campos_con_form_control = [
            'nombre', 'docCliente', 'tipoDocCliente', 'correoElecCliente',
            'telefono', 'tipoCliente', 'direccion', 'ocupacion', 'segmento'
        ]
        
        for campo in campos_con_form_control:
            widget_attrs = form.fields[campo].widget.attrs
            assert 'class' in widget_attrs, f"El campo '{campo}' debería tener atributo class"
            assert 'form-control' in widget_attrs['class'], f"El campo '{campo}' debería tener clase 'form-control'"
        
        # Verificar que declaracion_jurada tiene clase específica
        widget_attrs = form.fields['declaracion_jurada'].widget.attrs
        assert 'form-check-input' in widget_attrs.get('class', ''), "declaracion_jurada debería tener clase 'form-check-input'"
        
        print("✓ Test widgets_css_classes: Clases CSS de widgets correctas")
    
    def test_mensajes_error_personalizados(self):
        """Test para verificar que los mensajes de error son personalizados"""
        # Test mensaje de error personalizado para nombre
        datos = self.datos_validos.copy()
        datos['nombre'] = ''
        form = ClienteForm(data=datos)
        
        assert not form.is_valid(), "El formulario no debería ser válido"
        assert 'nombre' in form.errors, "Debería haber error en nombre"
        assert 'Debes ingresar el nombre.' in str(form.errors['nombre']), "El mensaje de error personalizado no se muestra"
        
        # Test mensaje de error personalizado para documento
        datos = self.datos_validos.copy()
        datos['docCliente'] = ''
        form = ClienteForm(data=datos)
        
        assert not form.is_valid(), "El formulario no debería ser válido"
        assert 'docCliente' in form.errors, "Debería haber error en docCliente"
        assert 'Debes ingresar el número de documento.' in str(form.errors['docCliente']), "El mensaje de error personalizado no se muestra"
        
        print("✓ Test mensajes_error_personalizados: Mensajes de error personalizados funcionando")
    
    def test_edicion_cliente_existente(self):
        """Test para verificar que el formulario funciona para editar clientes existentes"""
        # Crear cliente primero
        cliente = Cliente.objects.create(**self.datos_validos)
        
        # Datos para edición
        datos_editados = self.datos_validos.copy()
        datos_editados['nombre'] = 'Juan Carlos Pérez'
        datos_editados['telefono'] = '0985999888'
        
        # Crear formulario con instancia existente
        form = ClienteForm(data=datos_editados, instance=cliente)
        
        assert form.is_valid(), f"El formulario de edición debería ser válido, errores: {form.errors}"
        
        cliente_editado = form.save()
        assert cliente_editado.pk == cliente.pk, "Debería ser el mismo cliente (no crear uno nuevo)"
        assert cliente_editado.nombre == 'Juan Carlos Pérez', "El nombre debería haberse actualizado"
        assert cliente_editado.telefono == '0985999888', "El teléfono debería haberse actualizado"
        
        print("✓ Test edicion_cliente_existente: Edición de cliente funcionando")
