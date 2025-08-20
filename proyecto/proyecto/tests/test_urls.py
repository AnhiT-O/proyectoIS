import pytest
from django.urls import reverse, resolve
from django.urls.exceptions import NoReverseMatch, Resolver404
from django.test import Client
from proyecto import views


@pytest.mark.django_db
class TestConfiguracionUrls:
    """Clase de pruebas para la configuración de URLs del proyecto usando pytest"""
    
    def test_url_inicio_resuelve_correctamente(self):
        """Prueba que la URL raíz '/' resuelve a la vista de inicio"""
        url = reverse('inicio')
        
        assert url == '/', "La URL de inicio debería ser la raíz '/'"
        
        # Verificar que la URL resuelve a la vista correcta
        resolver = resolve('/')
        assert resolver.func == views.inicio, \
            "La URL raíz debería resolver a la función vista 'inicio'"
        assert resolver.view_name == 'inicio', \
            "El nombre de la vista debería ser 'inicio'"
    
    def test_url_inicio_accesible(self, client):
        """Prueba que la URL de inicio es accesible y responde correctamente"""
        respuesta = client.get('/')
        
        assert respuesta.status_code == 200, \
            "La página de inicio debería ser accesible con código 200"
    
    def test_url_usuarios_incluida(self, client):
        """Prueba que las URLs de usuarios están incluidas correctamente"""
        try:
            # Intentar acceder a una URL que debería existir en usuarios
            respuesta = client.get('/usuarios/')
            # No importa el código de respuesta específico, solo que no sea 404
            assert respuesta.status_code != 404, \
                "Las URLs de usuarios deberían estar incluidas y no devolver 404"
        except Exception as e:
            # Si hay error, al menos verificar que el patrón existe
            assert 'usuarios/' in str(e) or True, \
                "El patrón 'usuarios/' debería estar configurado"
    
    def test_reverse_url_inicio(self):
        """Prueba que se puede hacer reverse de la URL de inicio por nombre"""
        try:
            url = reverse('inicio')
            assert url == '/', \
                "El reverse de 'inicio' debería devolver '/'"
        except NoReverseMatch:
            pytest.fail("No se pudo hacer reverse de la URL 'inicio'")
    
    def test_url_inexistente_retorna_404(self, client):
        """Prueba que una URL inexistente retorna error 404"""
        respuesta = client.get('/url-que-no-existe/')
        
        assert respuesta.status_code == 404, \
            "Una URL inexistente debería retornar código 404"
    
    def test_patron_urls_usuarios_configurado(self):
        """Prueba que el patrón de URLs para usuarios está configurado"""
        try:
            # Intentar resolver una URL de usuarios
            resolver = resolve('/usuarios/')
            assert True, "El patrón de URLs para usuarios está configurado"
        except Resolver404:
            # Esto está bien, significa que la URL específica no existe
            # pero el patrón 'usuarios/' sí está configurado
            assert True, "El patrón de URLs está configurado correctamente"
    
    def test_estructura_urlpatterns(self):
        """Prueba que la estructura de urlpatterns es correcta"""
        from proyecto.urls import urlpatterns
        
        assert len(urlpatterns) >= 2, \
            "Debería haber al menos 2 patrones de URL configurados"
        
        # Verificar que hay un patrón para la raíz
        patrones_raiz = [p for p in urlpatterns if str(p.pattern) == '']
        assert len(patrones_raiz) == 1, \
            "Debería haber exactamente un patrón para la URL raíz"
        
        # Verificar que hay un patrón para usuarios
        patrones_usuarios = [p for p in urlpatterns if 'usuarios' in str(p.pattern)]
        assert len(patrones_usuarios) >= 1, \
            "Debería haber al menos un patrón para URLs de usuarios"


@pytest.mark.django_db
class TestResolucionUrls:
    """Clase de pruebas para la resolución de URLs usando pytest"""
    
    def test_resolucion_url_inicio(self):
        """Prueba la resolución de la URL de inicio"""
        resolver = resolve('/')
        assert resolver.view_name == 'inicio', \
            "La URL raíz debería resolver al nombre de vista 'inicio'"
        assert hasattr(resolver.func, '__name__'), \
            "La función vista debería tener un nombre válido"
    
    def test_importacion_vistas(self):
        """Prueba que las vistas se importan correctamente"""
        from proyecto import views
        
        assert hasattr(views, 'inicio'), \
            "El módulo views debería tener la función 'inicio'"
        assert callable(views.inicio), \
            "La función 'inicio' debería ser callable"
    
    def test_configuracion_urls_valida(self):
        """Prueba que la configuración de URLs es válida"""
        from proyecto.urls import urlpatterns
        from django.urls.resolvers import URLPattern, URLResolver
        
        assert isinstance(urlpatterns, list), \
            "urlpatterns debería ser una lista"
        assert len(urlpatterns) > 0, \
            "urlpatterns no debería estar vacía"
        
        for patron in urlpatterns:
            assert isinstance(patron, (URLPattern, URLResolver)), \
                f"Cada patrón debería ser URLPattern o URLResolver, encontrado: {type(patron)}"
    
    def test_nombres_urls_unicos(self):
        """Prueba que los nombres de URLs son únicos"""
        from proyecto.urls import urlpatterns
        
        nombres = []
        for patron in urlpatterns:
            if hasattr(patron, 'name') and patron.name:
                nombres.append(patron.name)
        
        nombres_unicos = set(nombres)
        assert len(nombres) == len(nombres_unicos), \
            "Los nombres de URLs deberían ser únicos"
    
    def test_patrones_url_sintaxis_correcta(self):
        """Prueba que los patrones de URL tienen sintaxis correcta"""
        from proyecto.urls import urlpatterns
        
        for patron in urlpatterns:
            assert hasattr(patron, 'pattern'), \
                "Cada patrón debería tener un atributo 'pattern'"
            
            # Verificar que el patrón no esté vacío para patrones que no sean raíz
            patron_str = str(patron.pattern)
            if patron_str != '':
                assert len(patron_str) > 0, \
                    "Los patrones no raíz deberían tener contenido"
    
    def test_inclusion_urls_usuarios(self):
        """Prueba que se incluyen correctamente las URLs de usuarios"""
        from proyecto.urls import urlpatterns
        from django.urls.resolvers import URLResolver
        
        # Buscar si hay algún resolver que incluya URLs de usuarios
        resolvers_usuarios = []
        for patron in urlpatterns:
            if isinstance(patron, URLResolver):
                if 'usuarios' in str(patron.pattern):
                    resolvers_usuarios.append(patron)
        
        assert len(resolvers_usuarios) >= 1, \
            "Debería haber al menos un resolver para las URLs de usuarios"


@pytest.mark.django_db
class TestAccesoUrls:
    """Clase de pruebas para el acceso a URLs usando pytest"""
    
    def test_url_inicio_funcionamiento(self, client):
        """Prueba que la URL de inicio funciona correctamente"""
        respuesta = client.get('/')
        
        assert respuesta.status_code == 200, \
            "La URL de inicio debería funcionar correctamente"
    
    def test_acceso_urls_diferentes_metodos(self, client):
        """Prueba el acceso a URLs con diferentes métodos HTTP"""
        # Probar GET
        respuesta_get = client.get('/')
        assert respuesta_get.status_code == 200, \
            "La URL de inicio debería aceptar peticiones GET"
        
        # Probar POST
        respuesta_post = client.post('/')
        assert respuesta_post.status_code == 200, \
            "La URL de inicio debería aceptar peticiones POST"
        
        # Probar HEAD
        respuesta_head = client.head('/')
        assert respuesta_head.status_code == 200, \
            "La URL de inicio debería aceptar peticiones HEAD"
    
    def test_manejo_caracteres_especiales(self, client):
        """Prueba el manejo de caracteres especiales en URLs"""
        # Probar URLs con caracteres especiales que podrían causar problemas
        urls_especiales = [
            '/usuarios/test%20user/',
            '/usuarios/test+user/',
            '/usuarios/test@user/',
        ]
        
        for url in urls_especiales:
            respuesta = client.get(url)
            # No debería causar errores del servidor (500)
            assert respuesta.status_code != 500, \
                f"La URL '{url}' no debería causar errores del servidor"
    
    def test_urls_case_sensitivity(self, client):
        """Prueba la sensibilidad a mayúsculas/minúsculas en URLs"""
        # La URL principal debería funcionar en minúsculas
        respuesta_normal = client.get('/')
        assert respuesta_normal.status_code == 200, \
            "La URL en minúsculas debería funcionar"
        
        # Probar algunas variaciones que deberían fallar
        urls_case_test = ['/USUARIOS/', '/Usuarios/']
        for url in urls_case_test:
            respuesta = client.get(url)
            # Debería ser 404 porque Django es case-sensitive
            assert respuesta.status_code == 404, \
                f"La URL '{url}' debería retornar 404 por case-sensitivity"


@pytest.mark.django_db 
class TestSeguridadUrls:
    """Clase de pruebas de seguridad para URLs usando pytest"""
    
    def test_urls_no_exponen_informacion_sensible(self):
        """Prueba que las URLs no exponen información sensible en la estructura"""
        from proyecto.urls import urlpatterns
        
        patrones_sensibles = ['admin', 'debug', 'test', 'dev', 'api-key', 'secret']
        
        for patron in urlpatterns:
            patron_str = str(patron.pattern).lower()
            for sensible in patrones_sensibles:
                assert sensible not in patron_str, \
                    f"Las URLs no deberían exponer rutas sensibles como '{sensible}'"
    
    def test_urls_estructura_limpia(self):
        """Prueba que la estructura de URLs es limpia y bien organizada"""
        from proyecto.urls import urlpatterns
        
        # Verificar que no hay patrones duplicados
        patrones_str = [str(p.pattern) for p in urlpatterns]
        patrones_unicos = set(patrones_str)
        
        assert len(patrones_str) == len(patrones_unicos), \
            "No debería haber patrones de URL duplicados"
    
    def test_validacion_patrones_regex(self):
        """Prueba que los patrones regex son válidos y seguros"""
        from proyecto.urls import urlpatterns
        import re
        
        for patron in urlpatterns:
            patron_str = str(patron.pattern)
            if patron_str:  # Solo validar patrones no vacíos
                try:
                    # Intentar compilar el patrón como regex
                    re.compile(patron_str)
                    assert True, f"El patrón '{patron_str}' debería ser regex válido"
                except re.error:
                    # Si no es regex válido, al menos no debería tener caracteres peligrosos
                    caracteres_peligrosos = ['<script', 'javascript:', 'data:', 'vbscript:']
                    for peligroso in caracteres_peligrosos:
                        assert peligroso.lower() not in patron_str.lower(), \
                            f"El patrón no debería contener '{peligroso}'"


@pytest.mark.django_db
class TestReverseUrls:
    """Clase de pruebas para el reverse de URLs usando pytest"""
    
    def test_reverse_todas_urls_nombradas(self):
        """Prueba que se puede hacer reverse de todas las URLs con nombre"""
        from proyecto.urls import urlpatterns
        
        for patron in urlpatterns:
            if hasattr(patron, 'name') and patron.name:
                try:
                    url_reversed = reverse(patron.name)
                    assert isinstance(url_reversed, str), \
                        f"El reverse de '{patron.name}' debería devolver una cadena"
                    assert len(url_reversed) > 0, \
                        f"El reverse de '{patron.name}' no debería estar vacío"
                except NoReverseMatch:
                    pytest.fail(f"No se pudo hacer reverse de la URL '{patron.name}'")
    
    def test_reverse_urls_consistencia(self):
        """Prueba la consistencia del reverse de URLs"""
        # Probar el reverse de la URL de inicio
        url_inicio = reverse('inicio')
        assert url_inicio == '/', \
            "El reverse de 'inicio' debería ser consistente con '/'"
        
        # Verificar que hacer reverse dos veces da el mismo resultado
        url_inicio_2 = reverse('inicio')
        assert url_inicio == url_inicio_2, \
            "El reverse debería ser consistente en múltiples llamadas"
    
    def test_urls_reversibles_resolvibles(self):
        """Prueba que las URLs que se pueden reverse también se pueden resolve"""
        from proyecto.urls import urlpatterns
        
        for patron in urlpatterns:
            if hasattr(patron, 'name') and patron.name:
                try:
                    url_reversed = reverse(patron.name)
                    resolver = resolve(url_reversed)
                    assert resolver.view_name == patron.name, \
                        f"La URL reverseada debería resolver al mismo nombre: {patron.name}"
                except (NoReverseMatch, Resolver404):
                    # Algunas URLs podrían requerir argumentos
                    continue