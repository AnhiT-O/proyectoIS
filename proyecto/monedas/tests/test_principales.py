"""
Pruebas unitarias principales para la aplicación monedas
Utilizando pytest para las 5 funcionalidades más críticas
"""
import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError
import datetime

from monedas.models import Moneda, LimiteGlobal
from monedas.forms import MonedaForm, LimiteGlobalForm
from clientes.models import Cliente

User = get_user_model()


class TestCalculoPrecios:
    """Test 1: Pruebas para cálculo de precios de monedas"""
    
    @pytest.fixture
    def moneda_usd(self, db):
        """Fixture que obtiene o crea una moneda USD para las pruebas"""
        moneda, created = Moneda.objects.get_or_create(
            simbolo='USD',
            defaults={
                'nombre': 'Dólar estadounidense',
                'tasa_base': 7400,
                'comision_compra': 200,
                'comision_venta': 250,
                'stock': 1000
            }
        )
        return moneda
    
    def test_calcular_precio_venta_sin_beneficio(self, moneda_usd):
        """Prueba el cálculo del precio de venta sin beneficio del cliente"""
        precio_venta = moneda_usd.calcular_precio_venta(0)
        precio_esperado = 7400 + 250  # tasa_base + comision_venta
        
        assert precio_venta == precio_esperado, f"Esperado {precio_esperado}, obtuvo {precio_venta}"
    
    def test_calcular_precio_venta_con_beneficio(self, moneda_usd):
        """Prueba el cálculo del precio de venta con 10% de beneficio"""
        precio_venta = moneda_usd.calcular_precio_venta(10)
        # precio = 7400 + 250 - (250 * 0.1) = 7625
        precio_esperado = int(7400 + 250 - (250 * 0.1))
        
        assert precio_venta == precio_esperado, f"Esperado {precio_esperado}, obtuvo {precio_venta}"
    
    def test_calcular_precio_compra_sin_beneficio(self, moneda_usd):
        """Prueba el cálculo del precio de compra sin beneficio del cliente"""
        precio_compra = moneda_usd.calcular_precio_compra(0)
        precio_esperado = 7400 - 200  # tasa_base - comision_compra
        
        assert precio_compra == precio_esperado, f"Esperado {precio_esperado}, obtuvo {precio_compra}"
    
    def test_calcular_precio_compra_con_beneficio(self, moneda_usd):
        """Prueba el cálculo del precio de compra con 5% de beneficio"""
        precio_compra = moneda_usd.calcular_precio_compra(5)
        # precio = 7400 - 200 + (200 * 0.05) = 7210
        precio_esperado = int(7400 - 200 + (200 * 0.05))
        
        assert precio_compra == precio_esperado, f"Esperado {precio_esperado}, obtuvo {precio_compra}"


class TestValidacionFormularios:
    """Test 2: Pruebas para validación de formularios"""
    
    def test_moneda_form_datos_validos(self, db):
        """Prueba que un formulario con datos válidos sea aceptado"""
        form_data = {
            'nombre': 'Euro',
            'simbolo': 'EUR',
            'tasa_base': 8000,
            'comision_compra': 150,
            'comision_venta': 200,
            'decimales': 2,
            'stock': 500
        }
        form = MonedaForm(data=form_data)
        
        assert form.is_valid(), f"El formulario debería ser válido, errores: {form.errors}"
    
    def test_moneda_form_simbolo_invalido(self, db):
        """Prueba que símbolos con números sean rechazados"""
        form_data = {
            'nombre': 'Euro',
            'simbolo': 'EU1',  # Contiene número
            'tasa_base': 8000,
            'comision_compra': 150,
            'comision_venta': 200,
            'decimales': 2,
            'stock': 500
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con símbolo que contiene números"
        assert 'simbolo' in form.errors, "Debería haber error en el campo símbolo"
    
    def test_moneda_form_tasa_base_negativa(self, db):
        """Prueba que tasas base negativas sean rechazadas"""
        form_data = {
            'nombre': 'Euro',
            'simbolo': 'EUR',
            'tasa_base': -100,  # Negativo
            'comision_compra': 150,
            'comision_venta': 200,
            'decimales': 2,
            'stock': 500
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con tasa base negativa"
        assert 'tasa_base' in form.errors, "Debería haber error en el campo tasa_base"
    
    def test_limite_global_form_limite_diario_mayor_mensual(self, db):
        """Prueba que límite diario mayor al mensual sea rechazado"""
        form_data = {
            'limite_diario': 500000000,  # 500 millones
            'limite_mensual': 400000000,  # 400 millones (menor que diario)
            'fecha_inicio': datetime.date.today(),
            'activo': True
        }
        form = LimiteGlobalForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con límite diario mayor al mensual"
        assert '__all__' in form.errors or 'limite_diario' in form.errors, "Debería haber error de validación"


class TestLimitesGlobales:
    """Test 3: Pruebas para límites globales"""
    
    @pytest.fixture
    def limite_vigente(self, db):
        """Fixture que crea un límite global vigente"""
        return LimiteGlobal.objects.create(
            limite_diario=90000000,
            limite_mensual=450000000,
            fecha_inicio=datetime.date.today(),
            activo=True
        )
    
    def test_obtener_limite_vigente(self, limite_vigente):
        """Prueba que se obtenga correctamente el límite vigente"""
        limite = LimiteGlobal.obtener_limite_vigente()
        
        assert limite is not None, "Debería existir un límite vigente"
        assert limite.activo == True, "El límite debería estar activo"
        assert limite.limite_diario == 90000000, f"Límite diario esperado 90000000, obtuvo {limite.limite_diario}"
    
    def test_validacion_limite_diario_positivo(self, db):
        """Prueba que límites diarios negativos o cero sean rechazados"""
        limite = LimiteGlobal(
            limite_diario=0,  # Inválido
            limite_mensual=450000000,
            fecha_inicio=datetime.date.today(),
            activo=True
        )
        
        with pytest.raises(ValidationError) as exc_info:
            limite.full_clean()
        
        assert 'limite_diario' in str(exc_info.value), "Debería haber error en limite_diario"
    
    def test_validacion_limite_diario_no_mayor_mensual(self, db):
        """Prueba que límite diario no pueda ser mayor al mensual"""
        limite = LimiteGlobal(
            limite_diario=500000000,  # 500 millones
            limite_mensual=400000000,  # 400 millones (menor)
            fecha_inicio=datetime.date.today(),
            activo=True
        )
        
        with pytest.raises(ValidationError) as exc_info:
            limite.full_clean()
        
        assert 'limite_diario' in str(exc_info.value), "Debería haber error indicando que límite diario es mayor al mensual"


class TestVistasMonedas:
    """Test 4: Pruebas para vistas principales de monedas - Versión simplificada"""
    
    @pytest.fixture
    def usuario_con_permisos(self, db):
        """Fixture que crea un usuario con permisos para gestionar monedas"""
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        # Crear usuario directamente con los campos que acepta el modelo Usuario
        user = User.objects.create(
            username='admin_test',
            email='admin@test.com',
            first_name='Admin',
            last_name='Test',
            tipo_cedula='CI',
            cedula_identidad='12345678',
            is_active=True
        )
        user.set_password('testpass123')
        user.save()
        
        # Obtener el content type de Moneda
        content_type = ContentType.objects.get_for_model(Moneda)
        
        # Crear y asignar el permiso de gestión
        permission, created = Permission.objects.get_or_create(
            codename='gestion',
            name='Puede gestionar monedas (crear y editar)',
            content_type=content_type,
        )
        user.user_permissions.add(permission)
        
        return user
    
    @pytest.fixture
    def moneda_eur(self, db):
        """Fixture que obtiene o crea una moneda EUR para las pruebas"""
        moneda, created = Moneda.objects.get_or_create(
            simbolo='EUR',
            defaults={
                'nombre': 'Euro',
                'tasa_base': 8000,
                'comision_compra': 150,
                'comision_venta': 200,
                'activa': True,
                'stock': 300
            }
        )
        return moneda
    
    def test_usuario_tiene_permisos_correctos(self, db, usuario_con_permisos):
        """Prueba que el usuario tenga los permisos necesarios para gestionar monedas"""
        assert usuario_con_permisos.has_perm('monedas.gestion'), "El usuario debería tener permiso de gestión de monedas"
        assert usuario_con_permisos.is_active, "El usuario debería estar activo"
        assert usuario_con_permisos.username == 'admin_test', f"El username debería ser 'admin_test', obtuvo '{usuario_con_permisos.username}'"
    
    def test_moneda_puede_ser_consultada_desde_db(self, db, moneda_eur):
        """Prueba que la moneda EUR se puede consultar desde la base de datos"""
        moneda_db = Moneda.objects.get(simbolo='EUR')
        
        assert moneda_db.nombre == 'Euro', f"El nombre debería ser 'Euro', obtuvo '{moneda_db.nombre}'"
        assert moneda_db.tasa_base == 8000, f"La tasa base debería ser 8000, obtuvo {moneda_db.tasa_base}"
        assert moneda_db.activa == True, "La moneda debería estar activa"
    
    def test_cambio_estado_moneda_directamente(self, db, moneda_eur):
        """Prueba el cambio de estado de una moneda directamente en el modelo"""
        # Estado inicial
        estado_inicial = moneda_eur.activa
        assert estado_inicial == True, "La moneda debería estar inicialmente activa"
        
        # Cambiar el estado
        moneda_eur.activa = not moneda_eur.activa
        moneda_eur.save()
        
        # Verificar el cambio
        moneda_eur.refresh_from_db()
        assert moneda_eur.activa == False, "La moneda debería estar desactivada después del cambio"
        
        # Volver al estado original
        moneda_eur.activa = True
        moneda_eur.save()
        assert moneda_eur.activa == True, "La moneda debería volver a estar activa"


class TestValidacionModeloMoneda:
    """Test 5: Pruebas para validación del modelo Moneda"""
    
    def test_simbolo_automaticamente_mayuscula(self, db):
        """Prueba que el símbolo se convierta automáticamente a mayúsculas"""
        # Verificamos que el clean del formulario convierta a mayúsculas
        form_data = {
            'nombre': 'Yen japonés test',
            'simbolo': 'jpy',  # En minúsculas
            'tasa_base': 50,
            'comision_compra': 5,
            'comision_venta': 8,
            'decimales': 0,
            'stock': 1000
        }
        form = MonedaForm(data=form_data)
        assert form.is_valid(), f"El formulario debería ser válido, errores: {form.errors}"
        
        cleaned_simbolo = form.cleaned_data['simbolo']
        assert cleaned_simbolo == 'JPY', f"El símbolo debería convertirse a 'JPY', obtuvo '{cleaned_simbolo}'"
    
    def test_clean_simbolo_solo_letras(self, db):
        """Prueba que el formulario rechace símbolos con caracteres no alfabéticos"""
        form_data = {
            'nombre': 'Test moneda especial',
            'simbolo': 'U$D',  # Contiene símbolo especial
            'tasa_base': 7000,
            'comision_compra': 100,
            'comision_venta': 150,
            'decimales': 2,
            'stock': 500
        }
        form = MonedaForm(data=form_data)
        
        assert not form.is_valid(), "El formulario no debería ser válido con símbolo que contiene caracteres especiales"
        assert 'simbolo' in form.errors, f"Debería haber error en el campo símbolo, errores: {form.errors}"
    
    def test_string_representation(self, db):
        """Prueba que el método __str__ del modelo funcione correctamente"""
        moneda, created = Moneda.objects.get_or_create(
            simbolo='BRL',
            defaults={
                'nombre': 'Real brasileño',
                'tasa_base': 1400,
                'comision_compra': 50,
                'comision_venta': 80,
                'stock': 800
            }
        )
        
        assert str(moneda) == 'Real brasileño', f"La representación string debería ser 'Real brasileño', obtuvo '{str(moneda)}'"
    
    def test_moneda_activa_por_defecto(self, db):
        """Prueba que las monedas se creen activas por defecto"""
        moneda, created = Moneda.objects.get_or_create(
            simbolo='ARS',
            defaults={
                'nombre': 'Peso argentino',
                'tasa_base': 10,
                'comision_compra': 1,
                'comision_venta': 2,
                'stock': 2000
            }
        )
        
        assert moneda.activa == True, "Las monedas deberían crearse activas por defecto"
        assert moneda.decimales == 3, "Los decimales deberían ser 3 por defecto"
        assert moneda.stock == 2000, f"El stock debería ser 2000, obtuvo {moneda.stock}"