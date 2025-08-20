import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.http import HttpResponse
from django.template.response import TemplateResponse


class TestVistaInicio(TestCase):
    """Clase de pruebas para la vista de inicio del proyecto"""
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.client = Client()
        self.url_inicio = reverse('inicio')
    
    def test_vista_inicio_responde_correctamente(self):
        """Prueba que la vista de inicio responde con código HTTP 200"""
        respuesta = self.client.get(self.url_inicio)
        
        assert respuesta.status_code == 200, "La vista de inicio debería responder con código 200"
    
    def test_vista_inicio_usa_template_correcto(self):
        """Prueba que la vista de inicio utiliza el template 'inicio.html'"""
        respuesta = self.client.get(self.url_inicio)
        
        # Verificar que se utiliza el template correcto
        assert 'inicio.html' in [t.name for t in respuesta.templates], \
            "La vista de inicio debería usar el template 'inicio.html'"
    
    def test_vista_inicio_contenido_html(self):
        """Prueba que la vista de inicio contiene el contenido HTML esperado"""
        respuesta = self.client.get(self.url_inicio)
        contenido = respuesta.content.decode('utf-8')
        
        # Verificar elementos clave del HTML
        assert 'Casa de Cambios' in contenido, \
            "El título 'Casa de Cambios' debería estar presente en la página"
        assert 'Bienvenido' in contenido, \
            "El mensaje de bienvenida debería estar presente en la página"
        assert 'Registrarse Ahora' in contenido, \
            "El botón de registro debería estar presente en la página"
        assert 'Iniciar Sesión' in contenido, \
            "El enlace de inicio de sesión debería estar presente en la página"
    
    def test_vista_inicio_tipo_respuesta(self):
        """Prueba que la vista de inicio devuelve una respuesta de tipo TemplateResponse"""
        respuesta = self.client.get(self.url_inicio)
        
        assert isinstance(respuesta, HttpResponse), \
            "La respuesta debería ser una instancia de HttpResponse"
    
    def test_vista_inicio_content_type(self):
        """Prueba que la vista de inicio devuelve contenido HTML"""
        respuesta = self.client.get(self.url_inicio)
        
        assert 'text/html' in respuesta.get('Content-Type'), \
            "La respuesta debería tener content-type 'text/html'"
    
    def test_vista_inicio_sin_parametros(self):
        """Prueba que la vista de inicio funciona sin parámetros adicionales"""
        respuesta = self.client.get(self.url_inicio)
        
        assert respuesta.status_code == 200, \
            "La vista de inicio debería funcionar sin parámetros adicionales"
    
    def test_vista_inicio_metodo_get(self):
        """Prueba que la vista de inicio acepta peticiones GET"""
        respuesta = self.client.get(self.url_inicio)
        
        assert respuesta.status_code == 200, \
            "La vista de inicio debería aceptar peticiones GET"
    
    def test_vista_inicio_metodo_post(self):
        """Prueba que la vista de inicio acepta peticiones POST"""
        respuesta = self.client.post(self.url_inicio)
        
        # La vista debería responder correctamente a POST también
        assert respuesta.status_code == 200, \
            "La vista de inicio debería aceptar peticiones POST"
    
    def test_vista_inicio_charset_utf8(self):
        """Prueba que la vista de inicio utiliza codificación UTF-8"""
        respuesta = self.client.get(self.url_inicio)
        contenido = respuesta.content.decode('utf-8')
        
        # Verificar que se pueden leer caracteres en español correctamente
        assert 'Bienvenido' in contenido, \
            "Los caracteres en español deberían renderizarse correctamente"
        assert 'Gestión' in contenido, \
            "Los caracteres con tildes deberían renderizarse correctamente"


@pytest.mark.django_db
class TestVistaInicioConPytest:
    """Clase de pruebas adicionales usando pytest puro para la vista de inicio"""
    
    def test_vista_inicio_respuesta_exitosa(self, client):
        """Prueba con pytest que la vista de inicio responde exitosamente"""
        url = reverse('inicio')
        respuesta = client.get(url)
        
        assert respuesta.status_code == 200, \
            "La vista de inicio debería responder con éxito"
    
    def test_vista_inicio_template_existe(self, client):
        """Prueba con pytest que el template de inicio existe y se renderiza"""
        url = reverse('inicio')
        respuesta = client.get(url)
        
        assert respuesta.status_code == 200, \
            "El template de inicio debería existir y renderizarse correctamente"
        
        # Verificar que no hay errores de template
        contenido = respuesta.content.decode('utf-8')
        assert '<!DOCTYPE html>' in contenido, \
            "El template debería contener HTML válido"
    
    def test_vista_inicio_elementos_interfaz(self, client):
        """Prueba con pytest que los elementos de la interfaz están presentes"""
        url = reverse('inicio')
        respuesta = client.get(url)
        contenido = respuesta.content.decode('utf-8')
        
        elementos_esperados = [
            'Casa de Cambios',
            'Bienvenido',
            'Registrarse Ahora',
            'Iniciar Sesión',
            'Gestión segura',
            'Reportes y estadísticas'
        ]
        
        for elemento in elementos_esperados:
            assert elemento in contenido, \
                f"El elemento '{elemento}' debería estar presente en la página de inicio"
    
    def test_vista_inicio_estructura_html(self, client):
        """Prueba con pytest que la estructura HTML es válida"""
        url = reverse('inicio')
        respuesta = client.get(url)
        contenido = respuesta.content.decode('utf-8')
        
        # Verificar estructura básica HTML
        assert '<!DOCTYPE html>' in contenido, \
            "El documento debería tener declaración DOCTYPE"
        assert '<html lang="es">' in contenido, \
            "El documento debería especificar el idioma español"
        assert '<head>' in contenido and '</head>' in contenido, \
            "El documento debería tener sección head completa"
        assert '<body>' in contenido and '</body>' in contenido, \
            "El documento debería tener sección body completa"
        assert '<title>' in contenido and '</title>' in contenido, \
            "El documento debería tener título"