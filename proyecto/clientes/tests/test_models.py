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


@pytest.mark.django_db
class TestUsuarioClienteModel:
    """
    Tests para el modelo UsuarioCliente (relación many-to-many)
    """
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Configuración inicial para los tests"""
        self.cliente = Cliente.objects.create(
            nombre='Juan Pérez',
            tipoDocCliente='CI',
            docCliente='1234567890',
            correoElecCliente='juan@example.com',
            telefono='0981123456',
            tipoCliente='F',
            direccion='Asunción, Paraguay',
            ocupacion='Ingeniero',
            declaracion_jurada=True,
            segmento='minorista'
        )
        
        self.usuario = Usuario.objects.create_user(
            username='operador1',
            email='operador@example.com',
            password='test123',
            first_name='Carlos',
            last_name='López',
            tipo_cedula='CI',
            cedula_identidad='9876543210'
        )
    
    def test_crear_relacion_usuario_cliente(self):
        """Test para crear una relación usuario-cliente"""
        relacion = UsuarioCliente.objects.create(
            usuario=self.usuario,
            cliente=self.cliente
        )
        
        assert relacion.usuario == self.usuario, "El usuario de la relación no es el esperado"
        assert relacion.cliente == self.cliente, "El cliente de la relación no es el esperado"
        assert relacion.created_at is not None, "La fecha de creación de la relación no fue asignada"
        assert relacion.pk is not None, "La relación no fue guardada correctamente (pk es None)"
        print("✓ Test crear_relacion_usuario_cliente: Relación creada correctamente")
    
    def test_str_representation(self):
        """Test para la representación string de la relación"""
        relacion = UsuarioCliente.objects.create(
            usuario=self.usuario,
            cliente=self.cliente
        )
        
        expected_str = f"{self.usuario.email} - {self.cliente.nombre}"
        assert str(relacion) == expected_str, f"La representación string debe ser '{expected_str}'"
        print("✓ Test str_representation: Representación string de relación correcta")
    
    def test_unique_together_constraint(self):
        """Test para verificar que la relación usuario-cliente sea única"""
        # Crear primera relación
        UsuarioCliente.objects.create(
            usuario=self.usuario,
            cliente=self.cliente
        )
        
        # Intentar crear segunda relación igual
        with pytest.raises(IntegrityError) as exc_info:
            UsuarioCliente.objects.create(
                usuario=self.usuario,
                cliente=self.cliente
            )
        
        assert 'UNIQUE constraint failed' in str(exc_info.value), "No se detectó la violación de constraint unique_together"
        print("✓ Test unique_together_constraint: Constraint de unicidad funcionando")
    
    def test_relacion_many_to_many_funcionando(self):
        """Test para verificar que la relación many-to-many funcione"""
        # Asociar cliente con usuario
        self.cliente.usuarios.add(self.usuario)
        
        # Verificar que la relación existe
        assert self.usuario in self.cliente.usuarios.all(), "El usuario no está asociado al cliente"
        assert self.cliente in self.usuario.clientes_operados.all(), "El cliente no está asociado al usuario"
        
        # Verificar que se creó el objeto intermedio
        relacion_existe = UsuarioCliente.objects.filter(
            usuario=self.usuario, 
            cliente=self.cliente
        ).exists()
        assert relacion_existe, "No se creó el objeto intermedio UsuarioCliente"
        
        print("✓ Test relacion_many_to_many_funcionando: Relación M2M funcionando correctamente")
    
    def test_cascade_delete_usuario(self):
        """Test para verificar que se elimine la relación al eliminar usuario"""
        relacion = UsuarioCliente.objects.create(
            usuario=self.usuario,
            cliente=self.cliente
        )
        
        relacion_id = relacion.id
        self.usuario.delete()
        
        # La relación debe haberse eliminado
        assert not UsuarioCliente.objects.filter(id=relacion_id).exists(), "La relación no fue eliminada tras borrar el usuario"
        print("✓ Test cascade_delete_usuario: Cascade delete funcionando")
    
    def test_cascade_delete_cliente(self):
        """Test para verificar que se elimine la relación al eliminar cliente"""
        relacion = UsuarioCliente.objects.create(
            usuario=self.usuario,
            cliente=self.cliente
        )
        
        relacion_id = relacion.id
        self.cliente.delete()
        
        # La relación debe haberse eliminado
        assert not UsuarioCliente.objects.filter(id=relacion_id).exists(), "La relación no fue eliminada tras borrar el cliente"
        print("✓ Test cascade_delete_cliente: Cascade delete funcionando")
    
    def test_multiple_usuarios_por_cliente(self):
        """Test para verificar que un cliente puede tener múltiples usuarios"""
        # Crear segundo usuario
        usuario2 = Usuario.objects.create_user(
            username='operador2',
            email='operador2@example.com',
            password='test123',
            first_name='María',
            last_name='García',
            tipo_cedula='CI',
            cedula_identidad='1111111111'
        )
        
        # Asociar ambos usuarios al cliente
        self.cliente.usuarios.add(self.usuario)
        self.cliente.usuarios.add(usuario2)
        
        assert self.cliente.usuarios.count() == 2, "El cliente debe tener 2 usuarios asociados"
        assert self.usuario in self.cliente.usuarios.all(), "El primer usuario debe estar asociado"
        assert usuario2 in self.cliente.usuarios.all(), "El segundo usuario debe estar asociado"
        print("✓ Test multiple_usuarios_por_cliente: Múltiples usuarios por cliente funcionando")
    
    def test_multiple_clientes_por_usuario(self):
        """Test para verificar que un usuario puede operar múltiples clientes"""
        # Crear segundo cliente
        cliente2 = Cliente.objects.create(
            nombre='María García',
            tipoDocCliente='CI',
            docCliente='0987654321',
            correoElecCliente='maria@example.com',
            telefono='0985555555',
            tipoCliente='F',
            direccion='Luque, Paraguay',
            ocupacion='Doctora',
            declaracion_jurada=True,
            segmento='vip'
        )
        
        # Asociar ambos clientes al usuario
        self.usuario.clientes_operados.add(self.cliente)
        self.usuario.clientes_operados.add(cliente2)
        
        assert self.usuario.clientes_operados.count() == 2, "El usuario debe operar 2 clientes"
        assert self.cliente in self.usuario.clientes_operados.all(), "El primer cliente debe estar asociado"
        assert cliente2 in self.usuario.clientes_operados.all(), "El segundo cliente debe estar asociado"
        print("✓ Test multiple_clientes_por_usuario: Múltiples clientes por usuario funcionando")
    
    def test_meta_configuracion(self):
        """Test para verificar la configuración de Meta del modelo UsuarioCliente"""
        assert UsuarioCliente._meta.db_table == 'usuarios_clientes', "El nombre de la tabla debe ser 'usuarios_clientes'"
        assert UsuarioCliente._meta.verbose_name == 'Relación Usuario-Cliente', "El verbose_name incorrecto"
        assert UsuarioCliente._meta.verbose_name_plural == 'Relaciones Usuario-Cliente', "El verbose_name_plural incorrecto"
        
        # Verificar unique_together
        unique_together = UsuarioCliente._meta.unique_together
        assert ('usuario', 'cliente') in unique_together, "Debe existir unique_together para usuario y cliente"
        print("✓ Test meta_configuracion: Configuración de Meta de UsuarioCliente correcta")