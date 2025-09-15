import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from clientes.models import Cliente, UsuarioCliente
from usuarios.models import Usuario


@pytest.mark.django_db
class TestClienteModel:
    """
    Tests para el modelo Cliente
    """
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Configuración inicial para los tests"""
        self.datos_cliente_validos = {
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
    
    def test_crear_cliente_valido(self):
        """Test para crear un cliente con datos válidos"""
        cliente = Cliente(**self.datos_cliente_validos)
        cliente.save()
        
        assert cliente.nombre == 'Juan Pérez', "El nombre del cliente no coincide con el esperado"
        assert cliente.beneficio_segmento == 0, "El beneficio del segmento debería ser 0 para minorista"
        assert cliente.pk is not None, "El cliente no fue guardado correctamente (pk es None)"
        assert cliente.created_at is not None, "La fecha de creación no fue asignada"
        assert cliente.updated_at is not None, "La fecha de actualización no fue asignada"
        print("✓ Test crear_cliente_valido: Cliente creado correctamente")
    
    def test_str_representation(self):
        """Test para la representación string del cliente"""
        cliente = Cliente(**self.datos_cliente_validos)
        cliente.save()
        
        assert str(cliente) == 'Juan Pérez', "La representación string del cliente no es la esperada"
        print("✓ Test str_representation: Representación string correcta")
    
    def test_beneficio_segmento_se_actualiza_automaticamente(self):
        """Test para verificar que el beneficio se actualiza según el segmento"""
        # Test segmento minorista
        cliente = Cliente(**self.datos_cliente_validos)
        cliente.save()
        assert cliente.beneficio_segmento == 0, "El beneficio para segmento minorista debe ser 0"
        
        # Test segmento corporativo
        cliente.segmento = 'corporativo'
        cliente.save()
        assert cliente.beneficio_segmento == 5, "El beneficio para segmento corporativo debe ser 5"
        
        # Test segmento VIP
        cliente.segmento = 'vip'
        cliente.save()
        assert cliente.beneficio_segmento == 10, "El beneficio para segmento VIP debe ser 10"
        
        print("✓ Test beneficio_segmento_se_actualiza_automaticamente: Beneficios actualizados correctamente")
    
    def test_validacion_persona_juridica_con_ruc(self):
        """Test para validar que personas jurídicas usen RUC"""
        datos = self.datos_cliente_validos.copy()
        datos['tipoCliente'] = 'J'
        datos['tipoDocCliente'] = 'RUC'
        
        cliente = Cliente(**datos)
        cliente.save()  # No debe lanzar excepción
        
        assert cliente.tipoCliente == 'J', "El tipo de cliente debe ser 'J' (jurídica)"
        assert cliente.tipoDocCliente == 'RUC', "El tipo de documento para persona jurídica debe ser 'RUC'"
        print("✓ Test validacion_persona_juridica_con_ruc: Validación exitosa")
    
    def test_validacion_error_persona_juridica_sin_ruc(self):
        """Test para verificar error cuando persona jurídica no usa RUC"""
        datos = self.datos_cliente_validos.copy()
        datos['tipoCliente'] = 'J'
        datos['tipoDocCliente'] = 'CI'
        
        cliente = Cliente(**datos)
        
        with pytest.raises(ValidationError) as exc_info:
            cliente.save()
        
        assert 'tipoDocCliente' in exc_info.value.message_dict, "No se encontró el campo 'tipoDocCliente' en los errores"
        assert exc_info.value.message_dict['tipoDocCliente'][0] == 'Las personas jurídicas deben usar RUC', "El mensaje de error para tipoDocCliente no es el esperado"
        print("✓ Test validacion_error_persona_juridica_sin_ruc: Error de validación capturado correctamente")
    
    def test_campos_requeridos(self):
        """Test para verificar que los campos requeridos estén presentes"""
        cliente = Cliente()
        
        with pytest.raises(ValidationError) as exc_info:
            cliente.full_clean()
        
        campos_requeridos = ['nombre', 'tipoDocCliente', 'docCliente', 
                           'correoElecCliente', 'telefono', 'tipoCliente', 
                           'direccion', 'ocupacion']
        
        for campo in campos_requeridos:
            assert campo in exc_info.value.message_dict, f"El campo requerido '{campo}' no fue validado como obligatorio"
        
        print("✓ Test campos_requeridos: Validación de campos requeridos funcionando")
    
    def test_longitud_maxima_campos(self):
        """Test para verificar la longitud máxima de los campos"""
        datos = self.datos_cliente_validos.copy()
        
        # Test nombre muy largo
        datos['nombre'] = 'a' * 101  # Máximo es 100
        cliente = Cliente(**datos)
        
        with pytest.raises(ValidationError) as exc_info:
            cliente.full_clean()
        
        assert 'nombre' in exc_info.value.message_dict, "No se detectó el error de longitud máxima en el campo 'nombre'"
        
        # Test documento muy largo
        datos = self.datos_cliente_validos.copy()
        datos['docCliente'] = '1' * 21  # Máximo es 20
        cliente = Cliente(**datos)
        
        with pytest.raises(ValidationError) as exc_info:
            cliente.full_clean()
        
        assert 'docCliente' in exc_info.value.message_dict, "No se detectó el error de longitud máxima en el campo 'docCliente'"
        
        print("✓ Test longitud_maxima_campos: Validación de longitud máxima funcionando")
    
    def test_choices_validos(self):
        """Test para verificar que los choices sean válidos"""
        datos = self.datos_cliente_validos.copy()
        
        # Test tipo de cliente inválido
        datos['tipoCliente'] = 'X'
        cliente = Cliente(**datos)
        
        with pytest.raises(ValidationError) as exc_info:
            cliente.full_clean()
        
        assert 'tipoCliente' in exc_info.value.message_dict, "No se detectó el error de choice inválido en 'tipoCliente'"
        
        # Test tipo de documento inválido
        datos['tipoCliente'] = 'F'
        datos['tipoDocCliente'] = 'XX'
        cliente = Cliente(**datos)
        
        with pytest.raises(ValidationError) as exc_info:
            cliente.full_clean()
        
        assert 'tipoDocCliente' in exc_info.value.message_dict, "No se detectó el error de choice inválido en 'tipoDocCliente'"
        
        # Test segmento inválido
        datos = self.datos_cliente_validos.copy()
        datos['segmento'] = 'premium'
        cliente = Cliente(**datos)
        
        with pytest.raises(ValidationError) as exc_info:
            cliente.full_clean()
        
        assert 'segmento' in exc_info.value.message_dict, "No se detectó el error de choice inválido en 'segmento'"
        
        print("✓ Test choices_validos: Validación de choices funcionando")
    
    def test_email_formato_valido(self):
        """Test para verificar que el email tenga formato válido"""
        datos = self.datos_cliente_validos.copy()
        datos['correoElecCliente'] = 'email_invalido'
        
        cliente = Cliente(**datos)
        
        with pytest.raises(ValidationError) as exc_info:
            cliente.full_clean()
        
        assert 'correoElecCliente' in exc_info.value.message_dict, "No se detectó el error de formato inválido en email"
        print("✓ Test email_formato_valido: Validación de formato de email funcionando")
    
    def test_valores_por_defecto(self):
        """Test para verificar valores por defecto del modelo"""
        datos = self.datos_cliente_validos.copy()
        del datos['declaracion_jurada']  # Usar valor por defecto
        del datos['segmento']  # Usar valor por defecto
        
        cliente = Cliente(**datos)
        cliente.save()
        
        assert cliente.declaracion_jurada == False, "El valor por defecto de declaracion_jurada debe ser False"
        assert cliente.segmento == 'minorista', "El valor por defecto de segmento debe ser 'minorista'"
        assert cliente.beneficio_segmento == 0, "El valor por defecto de beneficio_segmento debe ser 0"
        print("✓ Test valores_por_defecto: Valores por defecto asignados correctamente")
    
    def test_meta_configuracion(self):
        """Test para verificar la configuración de Meta del modelo"""
        assert Cliente._meta.db_table == 'clientes', "El nombre de la tabla debe ser 'clientes'"
        assert Cliente._meta.verbose_name == 'Cliente', "El verbose_name debe ser 'Cliente'"
        assert Cliente._meta.verbose_name_plural == 'Clientes', "El verbose_name_plural debe ser 'Clientes'"
        
        # Verificar permisos personalizados
        permisos = [perm[0] for perm in Cliente._meta.permissions]
        assert 'gestion' in permisos, "Debe existir el permiso 'gestion'"
        print("✓ Test meta_configuracion: Configuración de Meta correcta")
