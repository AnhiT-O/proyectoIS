import pytest
from django.test import TestCase
from django.urls import reverse, resolve
from django.urls.exceptions import NoReverseMatch
from medios_pago import urls


@pytest.mark.django_db
class TestMediosPagoUrls:
    """Pruebas unitarias para las URLs de la app medios_pago"""

    def test_app_name_configurado_correctamente(self):
        """Test que verifica que el app_name está configurado correctamente"""
        assert hasattr(urls, 'app_name'), "El módulo urls debe tener definido app_name"
        assert urls.app_name == 'medios_pago', f"El app_name debe ser 'medios_pago' pero se obtuvo '{urls.app_name}'"

    def test_urlpatterns_existe_y_es_lista(self):
        """Test que verifica que urlpatterns existe y es una lista"""
        assert hasattr(urls, 'urlpatterns'), "El módulo urls debe tener definido urlpatterns"
        assert isinstance(urls.urlpatterns, list), "urlpatterns debe ser una lista"

    def test_urlpatterns_esta_vacio_actualmente(self):
        """Test que verifica que urlpatterns está vacío actualmente (según el comentario en urls.py)"""
        # Según el archivo urls.py, actualmente está vacío porque las vistas están en clientes/views.py
        assert len(urls.urlpatterns) == 0, "urlpatterns debe estar vacío actualmente según la implementación actual"

    def test_namespace_medios_pago_no_genera_errores(self):
        """Test que verifica que el namespace medios_pago puede ser importado sin errores"""
        try:
            # Intentar acceder al namespace no debe generar errores
            from django.urls import include
            from medios_pago.urls import urlpatterns, app_name
            
            # Verificar que se puede importar correctamente
            assert app_name is not None, "El app_name debe estar definido"
            assert urlpatterns is not None, "urlpatterns debe estar definido"
            
        except Exception as e:
            pytest.fail(f"No se pudo importar correctamente las URLs de medios_pago: {e}")

    def test_urls_module_importa_views_correctamente(self):
        """Test que verifica que el módulo urls importa views sin errores"""
        try:
            from medios_pago.urls import views
            # Si no hay error, la importación fue exitosa
            assert True, "La importación de views debe ser exitosa"
        except ImportError as e:
            pytest.fail(f"Error al importar views en urls.py: {e}")

    def test_configuracion_urls_preparada_para_futuras_rutas(self):
        """Test que verifica que la configuración está preparada para futuras rutas"""
        # Verificar que la estructura básica está en su lugar
        assert hasattr(urls, 'path'), "El módulo debe importar path de django.urls"
        assert hasattr(urls, 'views'), "El módulo debe importar views"
        
        # Verificar que la estructura permite agregar rutas fácilmente
        from django.urls import path
        from medios_pago import views
        
        # Esto no debe generar errores
        ejemplo_ruta = path('test/', lambda request: None, name='test')
        assert ejemplo_ruta is not None, "Debe ser posible crear rutas con la configuración actual"

    def test_no_hay_conflictos_de_nombres_en_urls(self):
        """Test que verifica que no hay conflictos potenciales en los nombres de URLs"""
        # Como actualmente no hay URLs definidas, verificamos que la estructura es válida
        # y no hay conflictos en las importaciones
        
        try:
            from medios_pago.urls import urlpatterns, app_name
            from django.urls import path
            
            # Verificar que no hay errores de configuración
            assert isinstance(urlpatterns, list), "urlpatterns debe ser una lista válida"
            assert isinstance(app_name, str), "app_name debe ser una cadena válida"
            
        except Exception as e:
            pytest.fail(f"Conflicto detectado en la configuración de URLs: {e}")

    def test_estructura_urls_cumple_convencion_django(self):
        """Test que verifica que la estructura de URLs cumple con las convenciones de Django"""
        from medios_pago import urls
        
        # Verificar que tiene los atributos esperados
        assert hasattr(urls, 'app_name'), "Debe tener app_name definido"
        assert hasattr(urls, 'urlpatterns'), "Debe tener urlpatterns definido"
        
        # Verificar tipos correctos
        assert isinstance(urls.app_name, str), "app_name debe ser string"
        assert isinstance(urls.urlpatterns, list), "urlpatterns debe ser lista"
        
        # Verificar que app_name no está vacío
        assert len(urls.app_name) > 0, "app_name no debe estar vacío"
        assert urls.app_name.strip() == urls.app_name, "app_name no debe tener espacios al inicio o final"

    def test_urls_puede_ser_incluido_en_proyecto_principal(self):
        """Test que verifica que las URLs pueden ser incluidas en el proyecto principal"""
        try:
            from django.urls import include
            from medios_pago.urls import urlpatterns, app_name
            
            # Simular la inclusión como se haría en el urls.py principal
            # path('medios-pago/', include('medios_pago.urls'))
            
            # Verificar que la estructura es compatible
            assert callable(include), "include debe estar disponible"
            assert urlpatterns is not None, "urlpatterns debe estar definido para include"
            
        except Exception as e:
            pytest.fail(f"Error al verificar compatibilidad con include: {e}")

    def test_urls_preparado_para_vistas_futuras(self):
        """Test que verifica que el archivo está preparado para agregar vistas futuras"""
        from medios_pago.urls import views
        
        # Verificar que views está disponible para usar
        assert views is not None, "views debe estar importado y disponible"
        
        # Verificar que se pueden crear patrones de URL con views
        from django.urls import path
        
        try:
            # Esto simula cómo se agregarían rutas futuras
            ejemplo_patron = path('ejemplo/', getattr(views, 'ejemplo_view', lambda r: None), name='ejemplo')
            assert ejemplo_patron is not None, "Debe ser posible crear patrones de URL con views"
        except Exception as e:
            pytest.fail(f"Error al crear patrón de ejemplo: {e}")

    def test_comentarios_en_urls_son_descriptivos(self):
        """Test que verifica que los comentarios en urls.py son descriptivos y útiles"""
        import inspect
        import os
        
        # Leer el archivo urls.py para verificar comentarios
        urls_file_path = os.path.join(os.path.dirname(urls.__file__), 'urls.py')
        
        try:
            with open(urls_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Verificar que hay comentarios descriptivos
            assert '# URLs para gestión específica de medios de pago del cliente' in content, "Debe tener comentario descriptivo sobre el propósito"
            assert '# Las vistas están en clientes/views.py' in content, "Debe explicar dónde están las vistas actualmente"
            
        except FileNotFoundError:
            pytest.fail("No se pudo encontrar el archivo urls.py para verificar comentarios")
        except Exception as e:
            pytest.fail(f"Error al verificar comentarios en urls.py: {e}")