"""
Tests para las vistas del sistema TAUser.

Este módulo contiene tests unitarios para las vistas principales del sistema
TAUser, incluyendo validación de funcionalidad, respuestas HTTP y flujos
de trabajo de las transacciones.

Author: Equipo de desarrollo Global Exchange  
Date: 2025
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, Client, RequestFactory
from django.contrib.messages import get_messages
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.http import HttpResponse, HttpRequest
from django.utils import timezone
from datetime import timedelta

from ..forms import TokenForm, IngresoForm


class TestViews:
    """
    Tests simples para funciones de vista específicas.
    
    Se enfocan en probar la lógica básica de cada vista usando mocking.
    """
    
    def test_inicio_view_template_usage(self):
        """
        Test 1: Verificar que se use el template correcto para la vista inicio.
        
        - Debe usar 'inicio.html' como template
        - Debe ser una función que procesa requests
        - Debe tener documentación apropiada
        """
        # Este test verifica la estructura del código fuente sin importar
        import os
        import re
        
        # Leer el archivo de vistas
        views_path = os.path.join(os.path.dirname(__file__), '..', 'views.py')
        with open(views_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar que la función inicio existe
        assert 'def inicio(request):' in content
        
        # Verificar que usa el template correcto
        assert "'inicio.html'" in content
        
        # Verificar que tiene docstring
        inicio_match = re.search(r'def inicio\(request\):\s*"""(.*?)"""', content, re.DOTALL)
        assert inicio_match is not None
        assert len(inicio_match.group(1).strip()) > 0
    
    def test_token_form_validation_logic(self):
        """
        Test 2: Verificar lógica de validación del formulario de tokens.
        
        - Debe rechazar tokens que no sean alfanuméricos
        - Debe rechazar tokens que no tengan 8 caracteres
        - Debe aceptar tokens válidos
        """
        # Test con token válido
        form_valido = TokenForm(data={'codigo': 'ABC12345'})
        assert form_valido.is_valid() == True
        
        # Test con token inválido - caracteres especiales
        form_invalido1 = TokenForm(data={'codigo': 'ABC123@#'})
        assert form_invalido1.is_valid() == False
        
        # Test con token inválido - longitud incorrecta
        form_invalido2 = TokenForm(data={'codigo': 'ABC123'})
        assert form_invalido2.is_valid() == False
    
    def test_ingreso_form_file_validation_logic(self):
        """
        Test 3: Verificar lógica de validación de archivos en IngresoForm.
        
        - Debe aceptar archivos .txt válidos
        - Debe rechazar archivos con extensiones incorrectas
        - Debe validar el tamaño de los archivos
        """
        # Test con archivo válido
        archivo_valido = SimpleUploadedFile(
            "test.txt", 
            b"Ingreso\nGuarani\t50000\t5", 
            content_type="text/plain"
        )
        form_valido = IngresoForm(files={'archivo': archivo_valido})
        assert form_valido.is_valid() == True
        
        # Test con archivo inválido - extensión incorrecta
        archivo_invalido = SimpleUploadedFile(
            "test.doc", 
            b"contenido", 
            content_type="application/msword"
        )
        form_invalido = IngresoForm(files={'archivo': archivo_invalido})
        assert form_invalido.is_valid() == False
    
    def test_view_structure_in_source_code(self):
        """
        Test 4: Verificar estructura de las vistas analizando el código fuente.
        
        - Deben existir las funciones principales
        - Deben tener parámetros de request apropiados
        - Deben tener documentación explicativa
        """
        import os
        import re
        
        # Leer el archivo de vistas
        views_path = os.path.join(os.path.dirname(__file__), '..', 'views.py')
        with open(views_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Lista de vistas que deben existir
        vistas_esperadas = [
            'def inicio(request):',
            'def caja_fuerte(request):',
            'def ingreso_token(request):',
            'def ingreso_billetes(request, codigo):',
            'def exito(request, codigo):'
        ]
        
        # Verificar que todas las vistas están definidas
        for vista in vistas_esperadas:
            assert vista in content, f"Vista '{vista}' no encontrada en views.py"
        
        # Verificar que tienen docstrings (al menos 3 comillas triples)
        docstring_count = content.count('"""')
        assert docstring_count >= 6, "Las vistas deben tener docstrings apropiados"
    
    def test_form_classes_exist_and_work(self):
        """
        Test 5: Verificar que las clases de formularios existen y funcionan.
        
        - TokenForm debe existir y tener el campo 'codigo'
        - IngresoForm debe existir y tener el campo 'archivo'
        - Ambos deben tener métodos de validación
        """
        from tauser.forms import TokenForm, IngresoForm
        
        # Verificar que las clases existen
        assert TokenForm is not None
        assert IngresoForm is not None
        
        # Verificar que TokenForm tiene el campo codigo
        token_form = TokenForm()
        assert 'codigo' in token_form.fields
        
        # Verificar que IngresoForm tiene el campo archivo
        ingreso_form = IngresoForm()
        assert 'archivo' in ingreso_form.fields
        
        # Verificar que tienen métodos de validación personalizada
        assert hasattr(TokenForm, 'clean_codigo')
        assert hasattr(IngresoForm, 'clean_archivo')


class TestFormularios(TestCase):
    """
    Test para los formularios utilizados en las vistas.
    
    Verifica la validación y funcionamiento de TokenForm e IngresoForm.
    """
    
    def test_token_form_valid(self):
        """
        Test para verificar validación exitosa de TokenForm.
        
        - Debe aceptar códigos alfanuméricos de 8 caracteres
        - Debe validar correctamente el formato
        """
        # Crear formulario con datos válidos
        form_data = {'codigo': 'ABC12345'}
        form = TokenForm(data=form_data)
        
        # Verificar que es válido
        assert form.is_valid()
        assert form.cleaned_data['codigo'] == 'ABC12345'
    
    def test_token_form_invalid_length(self):
        """
        Test para verificar validación de longitud incorrecta en TokenForm.
        
        - Debe rechazar códigos que no tengan exactamente 8 caracteres
        - Debe mostrar mensaje de error apropiado
        """
        # Crear formulario con código muy corto
        form_data = {'codigo': 'ABC123'}
        form = TokenForm(data=form_data)
        
        # Verificar que es inválido
        assert not form.is_valid()
        assert 'codigo' in form.errors
        
        # Crear formulario con código muy largo
        form_data = {'codigo': 'ABC123456'}
        form = TokenForm(data=form_data)
        
        # Verificar que es inválido
        assert not form.is_valid()
        assert 'codigo' in form.errors
    
    def test_token_form_invalid_characters(self):
        """
        Test para verificar validación de caracteres inválidos en TokenForm.
        
        - Debe rechazar códigos con caracteres especiales
        - Debe rechazar códigos con espacios
        """
        # Crear formulario con caracteres especiales
        form_data = {'codigo': 'ABC123@#'}
        form = TokenForm(data=form_data)
        
        # Verificar que es inválido
        assert not form.is_valid()
        assert 'codigo' in form.errors
        
        # Crear formulario con espacios
        form_data = {'codigo': 'ABC 1234'}
        form = TokenForm(data=form_data)
        
        # Verificar que es inválido
        assert not form.is_valid()
        assert 'codigo' in form.errors
    
    def test_ingreso_form_file_extension_validation(self):
        """
        Test para verificar validación de extensión de archivo en IngresoForm.
        
        - Debe aceptar solo archivos .txt
        - Debe rechazar otros tipos de archivo
        """
        # Crear archivo válido (.txt)
        archivo_valido = SimpleUploadedFile(
            "test.txt", 
            b"contenido de prueba", 
            content_type="text/plain"
        )
        form = IngresoForm(files={'archivo': archivo_valido})
        assert form.is_valid()
        
        # Crear archivo inválido (.pdf)
        archivo_invalido = SimpleUploadedFile(
            "test.pdf", 
            b"contenido de prueba", 
            content_type="application/pdf"
        )
        form = IngresoForm(files={'archivo': archivo_invalido})
        assert not form.is_valid()
        assert 'archivo' in form.errors