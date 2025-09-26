import pytest
from django.test import TestCase
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from usuarios.forms import RegistroUsuarioForm, RecuperarPasswordForm, EstablecerPasswordForm, AsignarRolForm, AsignarClienteForm
from usuarios.models import Usuario
from clientes.models import Cliente


class TestRegistroUsuarioForm:
    """Pruebas para el formulario de registro de usuario"""
    
    @pytest.fixture
    def datos_validos(self):
        """Datos válidos para el formulario de registro"""
        return {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'tipo_cedula': 'CI',
            'cedula_identidad': '12345678',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
    
    @pytest.fixture
    def usuario_existente(self, db):
        """Usuario existente para probar duplicados"""
        return Usuario.objects.create(
            username='existing',
            email='existing@example.com',
            first_name='Existing',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='87654321'
        )
    
    @pytest.mark.django_db
    def test_registro_exitoso_con_datos_validos(self, datos_validos):
        """Prueba 1: Registro exitoso con datos válidos"""
        form = RegistroUsuarioForm(data=datos_validos)
        
        assert form.is_valid()
        usuario = form.save()
        
        assert usuario.username == datos_validos['username']
        assert usuario.email == datos_validos['email']
        assert usuario.cedula_identidad == datos_validos['cedula_identidad']
        assert usuario.first_name == datos_validos['first_name']
        assert usuario.last_name == datos_validos['last_name']
        assert usuario.tipo_cedula == datos_validos['tipo_cedula']
    
    @pytest.mark.django_db
    def test_error_cedula_no_numerica(self, datos_validos):
        """Prueba 2a: Error si la cédula no es numérica"""
        datos_validos['cedula_identidad'] = 'abc123'
        form = RegistroUsuarioForm(data=datos_validos)
        
        assert not form.is_valid()
        assert 'cedula_identidad' in form.errors
        assert 'La cédula de identidad debe ser numérica.' in str(form.errors['cedula_identidad'])
    
    @pytest.mark.django_db
    def test_error_cedula_muy_corta(self, datos_validos):
        """Prueba 2b: Error si la cédula es muy corta"""
        datos_validos['cedula_identidad'] = '123'
        form = RegistroUsuarioForm(data=datos_validos)
        
        assert not form.is_valid()
        assert 'cedula_identidad' in form.errors
        assert 'La cédula de identidad debe tener al menos 4 dígitos.' in str(form.errors['cedula_identidad'])
    
    @pytest.mark.django_db
    def test_error_cedula_ya_existe(self, datos_validos, usuario_existente):
        """Prueba 2c: Error si la cédula ya existe"""
        datos_validos['cedula_identidad'] = usuario_existente.cedula_identidad
        form = RegistroUsuarioForm(data=datos_validos)
        
        assert not form.is_valid()
        assert 'cedula_identidad' in form.errors
    
    @pytest.mark.django_db
    def test_error_email_ya_registrado(self, datos_validos, usuario_existente):
        """Prueba 3a: Error si el email ya está registrado"""
        datos_validos['email'] = usuario_existente.email
        form = RegistroUsuarioForm(data=datos_validos)
        
        assert not form.is_valid()
        assert 'email' in form.errors
    
    @pytest.mark.django_db
    def test_error_email_invalido(self, datos_validos):
        """Prueba 3b: Error si el email es inválido"""
        datos_validos['email'] = 'email_invalido'
        form = RegistroUsuarioForm(data=datos_validos)
        
        assert not form.is_valid()
        assert 'email' in form.errors
    
    @pytest.mark.django_db
    def test_error_contrasenas_no_coinciden(self, datos_validos):
        """Prueba 4a: Error si las contraseñas no coinciden"""
        datos_validos['password2'] = 'DiferentePass123!'
        form = RegistroUsuarioForm(data=datos_validos)
        
        assert not form.is_valid()
        assert 'password2' in form.errors
        assert 'Las contraseñas no coinciden.' in str(form.errors['password2'])
    
    @pytest.mark.django_db
    def test_error_contrasena_muy_corta(self, datos_validos):
        """Prueba 4b: Error si contraseña no tiene más de 8 caracteres"""
        datos_validos['password1'] = 'Short1!'
        datos_validos['password2'] = 'Short1!'
        form = RegistroUsuarioForm(data=datos_validos)
        
        assert not form.is_valid()
        assert 'password1' in form.errors
        assert 'La contraseña debe tener más de 8 caracteres.' in str(form.errors['password1'])
    
    @pytest.mark.django_db
    def test_error_contrasena_sin_numero(self, datos_validos):
        """Prueba 4c: Error si contraseña no tiene número"""
        datos_validos['password1'] = 'ComplexPass!'
        datos_validos['password2'] = 'ComplexPass!'
        form = RegistroUsuarioForm(data=datos_validos)
        
        assert not form.is_valid()
        assert 'password1' in form.errors
        assert 'La contraseña debe contener al menos un número.' in str(form.errors['password1'])
    
    @pytest.mark.django_db
    def test_error_contrasena_sin_caracter_especial(self, datos_validos):
        """Prueba 4d: Error si contraseña no tiene carácter especial"""
        datos_validos['password1'] = 'ComplexPass123'
        datos_validos['password2'] = 'ComplexPass123'
        form = RegistroUsuarioForm(data=datos_validos)
        
        assert not form.is_valid()
        assert 'password1' in form.errors
        assert 'La contraseña debe contener al menos un caracter especial.' in str(form.errors['password1'])


class TestRecuperarPasswordForm:
    """Pruebas para el formulario de recuperación de contraseña"""
    
    @pytest.fixture
    def usuario_activo(self, db):
        """Usuario activo para pruebas"""
        return Usuario.objects.create(
            username='activo',
            email='activo@example.com',
            first_name='Usuario',
            last_name='Activo',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            is_active=True
        )
    
    @pytest.fixture
    def usuario_inactivo(self, db):
        """Usuario inactivo para pruebas"""
        return Usuario.objects.create(
            username='inactivo',
            email='inactivo@example.com',
            first_name='Usuario',
            last_name='Inactivo',
            tipo_cedula='CI',
            cedula_identidad='87654321',
            is_active=False
        )
    
    @pytest.mark.django_db
    def test_error_email_no_existe(self):
        """Prueba 5a: Error si el email no existe"""
        form = RecuperarPasswordForm(data={'email': 'noexiste@example.com'})
        
        assert not form.is_valid()
        assert 'email' in form.errors
        assert 'No existe una cuenta activa asociada a este correo electrónico.' in str(form.errors['email'])
    
    @pytest.mark.django_db
    def test_error_usuario_inactivo(self, usuario_inactivo):
        """Prueba 5b: Error si el usuario está inactivo"""
        form = RecuperarPasswordForm(data={'email': usuario_inactivo.email})
        
        assert not form.is_valid()
        assert 'email' in form.errors
        assert 'No existe una cuenta activa asociada a este correo electrónico.' in str(form.errors['email'])
    
    @pytest.mark.django_db
    def test_formulario_valido_usuario_activo(self, usuario_activo):
        """Prueba 5c: Formulario válido si el usuario existe y está activo"""
        form = RecuperarPasswordForm(data={'email': usuario_activo.email})
        
        assert form.is_valid()


class TestEstablecerPasswordForm:
    """Pruebas para el formulario de establecer nueva contraseña"""
    
    @pytest.fixture
    def usuario(self, db):
        """Usuario para las pruebas"""
        return Usuario.objects.create(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='12345678'
        )
    
    @pytest.mark.django_db
    def test_error_contrasena_muy_corta(self, usuario):
        """Prueba 6a: Error si la nueva contraseña es muy corta"""
        form = EstablecerPasswordForm(
            user=usuario,
            data={
                'new_password1': 'Short1!',
                'new_password2': 'Short1!'
            }
        )
        
        assert not form.is_valid()
        assert 'new_password1' in form.errors
        assert 'La contraseña debe tener más de 8 caracteres.' in str(form.errors['new_password1'])
    
    @pytest.mark.django_db
    def test_error_contrasena_sin_numero(self, usuario):
        """Prueba 6b: Error si la nueva contraseña no tiene número"""
        form = EstablecerPasswordForm(
            user=usuario,
            data={
                'new_password1': 'ComplexPass!',
                'new_password2': 'ComplexPass!'
            }
        )
        
        assert not form.is_valid()
        assert 'new_password1' in form.errors
        assert 'La contraseña debe contener al menos un número.' in str(form.errors['new_password1'])
    
    @pytest.mark.django_db
    def test_error_contrasena_sin_caracter_especial(self, usuario):
        """Prueba 6c: Error si la nueva contraseña no tiene carácter especial"""
        form = EstablecerPasswordForm(
            user=usuario,
            data={
                'new_password1': 'ComplexPass123',
                'new_password2': 'ComplexPass123'
            }
        )
        
        assert not form.is_valid()
        assert 'new_password1' in form.errors
        assert 'La contraseña debe contener al menos un caracter especial.' in str(form.errors['new_password1'])
    
    @pytest.mark.django_db
    def test_contrasena_valida(self, usuario):
        """Prueba 6d: Contraseña válida cumple todos los requisitos"""
        form = EstablecerPasswordForm(
            user=usuario,
            data={
                'new_password1': 'ComplexPass123!',
                'new_password2': 'ComplexPass123!'
            }
        )
        
        assert form.is_valid()


class TestAsignarRolForm:
    """Pruebas para el formulario de asignación de roles"""
    
    @pytest.fixture
    def grupos(self, db):
        """Crear grupos para las pruebas"""
        admin, _ = Group.objects.get_or_create(name='Administrador')
        operador, _ = Group.objects.get_or_create(name='Operador')
        supervisor, _ = Group.objects.get_or_create(name='Supervisor')
        return {'admin': admin, 'operador': operador, 'supervisor': supervisor}
    
    @pytest.fixture
    def usuario_con_rol(self, db, grupos):
        """Usuario con rol asignado"""
        usuario = Usuario.objects.create(
            username='test',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='12345678'
        )
        usuario.groups.add(grupos['operador'])
        return usuario
    
    @pytest.mark.django_db
    def test_no_muestra_rol_administrador(self, grupos):
        """Prueba 7a: No permite asignar rol Administrador"""
        form = AsignarRolForm()
        
        # Verificar que el queryset no incluye el grupo Administrador
        assert not form.fields['rol'].queryset.filter(name='Administrador').exists()
    
    @pytest.mark.django_db
    def test_solo_muestra_roles_no_asignados(self, grupos, usuario_con_rol):
        """Prueba 7b: Solo muestra roles no asignados al usuario"""
        form = AsignarRolForm(usuario=usuario_con_rol)
        
        # El formulario no debe mostrar el rol 'Operador' que ya tiene el usuario
        queryset_names = list(form.fields['rol'].queryset.values_list('name', flat=True))
        assert 'Operador' not in queryset_names
        assert 'Supervisor' in queryset_names
        assert 'Administrador' not in queryset_names
    
    @pytest.mark.django_db
    def test_formulario_valido_con_roles_disponibles(self, grupos, usuario_con_rol):
        """Prueba 7c: Formulario válido con roles disponibles"""
        form = AsignarRolForm(
            data={'rol': [grupos['supervisor'].id]},
            usuario=usuario_con_rol
        )
        
        assert form.is_valid()


class TestAsignarClienteForm:
    """Pruebas para el formulario de asignación de clientes"""
    
    @pytest.fixture
    def clientes(self, db):
        """Crear clientes para las pruebas"""
        cliente1 = Cliente.objects.create(
            nombre='Cliente 1',
            tipoDocCliente='CI',
            docCliente='12345678',
            correoElecCliente='cliente1@example.com',
            telefono='+595981123456',
            tipoCliente='F',
            direccion='Dirección 1',
            ocupacion='Ocupación 1'
        )
        cliente2 = Cliente.objects.create(
            nombre='Cliente 2',
            tipoDocCliente='RUC',
            docCliente='87654321',
            correoElecCliente='cliente2@example.com',
            telefono='+595981654321',
            tipoCliente='J',
            direccion='Dirección 2',
            ocupacion='Ocupación 2'
        )
        return [cliente1, cliente2]
    
    @pytest.fixture
    def usuario_con_cliente(self, db, clientes):
        """Usuario con cliente asignado"""
        from clientes.models import UsuarioCliente
        usuario = Usuario.objects.create(
            username='test',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            tipo_cedula='CI',
            cedula_identidad='12345678'
        )
        UsuarioCliente.objects.create(usuario=usuario, cliente=clientes[0])
        return usuario
    
    @pytest.mark.django_db
    def test_solo_muestra_clientes_no_asignados(self, clientes, usuario_con_cliente):
        """Prueba 8a: Solo muestra clientes no asignados al usuario"""
        form = AsignarClienteForm(usuario=usuario_con_cliente)
        
        queryset_ids = list(form.fields['clientes'].queryset.values_list('id', flat=True))
        # No debe mostrar el cliente ya asignado
        assert clientes[0].id not in queryset_ids
        # Debe mostrar el cliente no asignado
        assert clientes[1].id in queryset_ids
    
    @pytest.mark.django_db
    def test_etiqueta_personalizada(self, clientes, usuario_con_cliente):
        """Prueba 8b: Etiqueta personalizada muestra nombre y documento"""
        form = AsignarClienteForm(usuario=usuario_con_cliente)
        
        # Verificar que la función label_from_instance existe y funciona correctamente
        label_func = form.fields['clientes'].label_from_instance
        label = label_func(clientes[1])
        expected_label = f"{clientes[1].nombre} ({clientes[1].docCliente})"
        
        assert label == expected_label
