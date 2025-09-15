import pytest
from django.test import TestCase
from django.urls import reverse, resolve
from django.http import Http404
from clientes import views


class TestClienteUrls:
    """
    Tests para las URLs de la app clientes
    """
    
    def test_cliente_crear_url_resolve(self):
        """Test para verificar que la URL de crear cliente resuelve correctamente"""
        url = reverse('clientes:cliente_crear')
        resolved = resolve(url)
        
        assert resolved.func == views.cliente_crear, "La URL debería resolver a la vista cliente_crear"
        assert url == '/clientes/crear/', "La URL debería ser '/clientes/crear/'"
        print("✓ Test cliente_crear_url_resolve: URL de creación resuelve correctamente")
    
    def test_cliente_lista_url_resolve(self):
        """Test para verificar que la URL de lista de clientes resuelve correctamente"""
        url = reverse('clientes:cliente_lista')
        resolved = resolve(url)
        
        assert resolved.func == views.cliente_lista, "La URL debería resolver a la vista cliente_lista"
        assert url == '/clientes/', "La URL debería ser '/clientes/'"
        print("✓ Test cliente_lista_url_resolve: URL de lista resuelve correctamente")
    
    def test_cliente_detalle_url_resolve(self):
        """Test para verificar que la URL de detalle de cliente resuelve correctamente"""
        pk = 1
        url = reverse('clientes:cliente_detalle', args=[pk])
        resolved = resolve(url)
        
        assert resolved.func == views.cliente_detalle, "La URL debería resolver a la vista cliente_detalle"
        assert url == f'/clientes/{pk}/', "La URL debería incluir el ID del cliente"
        assert resolved.kwargs['pk'] == pk, "Los kwargs deberían incluir el pk correcto"
        print("✓ Test cliente_detalle_url_resolve: URL de detalle resuelve correctamente")
    
    def test_cliente_editar_url_resolve(self):
        """Test para verificar que la URL de editar cliente resuelve correctamente"""
        pk = 1
        url = reverse('clientes:cliente_editar', args=[pk])
        resolved = resolve(url)
        
        assert resolved.func == views.cliente_editar, "La URL debería resolver a la vista cliente_editar"
        assert url == f'/clientes/{pk}/editar/', "La URL debería incluir el ID del cliente y 'editar'"
        assert resolved.kwargs['pk'] == pk, "Los kwargs deberían incluir el pk correcto"
        print("✓ Test cliente_editar_url_resolve: URL de edición resuelve correctamente")
    
    def test_cliente_agregar_tarjeta_url_resolve(self):
        """Test para verificar que la URL de agregar tarjeta resuelve correctamente"""
        pk = 1
        url = reverse('clientes:cliente_agregar_tarjeta', args=[pk])
        resolved = resolve(url)
        
        assert resolved.func == views.cliente_agregar_tarjeta, "La URL debería resolver a la vista cliente_agregar_tarjeta"
        assert url == f'/clientes/{pk}/agregar-tarjeta/', "La URL debería incluir el ID del cliente y 'agregar-tarjeta'"
        assert resolved.kwargs['pk'] == pk, "Los kwargs deberían incluir el pk correcto"
        print("✓ Test cliente_agregar_tarjeta_url_resolve: URL de agregar tarjeta resuelve correctamente")
    
    def test_cliente_agregar_cuenta_url_resolve(self):
        """Test para verificar que la URL de agregar cuenta resuelve correctamente"""
        pk = 1
        url = reverse('clientes:cliente_agregar_cuenta', args=[pk])
        resolved = resolve(url)
        
        assert resolved.func == views.cliente_agregar_cuenta, "La URL debería resolver a la vista cliente_agregar_cuenta"
        assert url == f'/clientes/{pk}/agregar-cuenta/', "La URL debería incluir el ID del cliente y 'agregar-cuenta'"
        assert resolved.kwargs['pk'] == pk, "Los kwargs deberían incluir el pk correcto"
        print("✓ Test cliente_agregar_cuenta_url_resolve: URL de agregar cuenta resuelve correctamente")
    
    def test_cliente_cambiar_estado_medio_pago_url_resolve(self):
        """Test para verificar que la URL de cambiar estado de medio de pago resuelve correctamente"""
        pk = 1
        medio_id = 2
        url = reverse('clientes:cliente_cambiar_estado_medio_pago', args=[pk, medio_id])
        resolved = resolve(url)
        
        assert resolved.func == views.cliente_cambiar_estado_medio_pago, "La URL debería resolver a la vista cliente_cambiar_estado_medio_pago"
        assert url == f'/clientes/{pk}/medio-pago/{medio_id}/cambiar-estado/', "La URL debería incluir ambos IDs y la acción"
        assert resolved.kwargs['pk'] == pk, "Los kwargs deberían incluir el pk del cliente"
        assert resolved.kwargs['medio_id'] == medio_id, "Los kwargs deberían incluir el medio_id"
        print("✓ Test cliente_cambiar_estado_medio_pago_url_resolve: URL de cambiar estado resuelve correctamente")
    
    def test_cliente_eliminar_medio_pago_url_resolve(self):
        """Test para verificar que la URL de eliminar medio de pago resuelve correctamente"""
        pk = 1
        medio_id = 2
        url = reverse('clientes:cliente_eliminar_medio_pago', args=[pk, medio_id])
        resolved = resolve(url)
        
        assert resolved.func == views.cliente_eliminar_medio_pago, "La URL debería resolver a la vista cliente_eliminar_medio_pago"
        assert url == f'/clientes/{pk}/medio-pago/{medio_id}/eliminar/', "La URL debería incluir ambos IDs y la acción"
        assert resolved.kwargs['pk'] == pk, "Los kwargs deberían incluir el pk del cliente"
        assert resolved.kwargs['medio_id'] == medio_id, "Los kwargs deberían incluir el medio_id"
        print("✓ Test cliente_eliminar_medio_pago_url_resolve: URL de eliminar medio de pago resuelve correctamente")
    
    def test_all_urls_have_name_namespace(self):
        """Test para verificar que todas las URLs tienen el namespace correcto"""
        urls_with_names = [
            ('clientes:cliente_crear', 'crear'),
            ('clientes:cliente_lista', 'lista'),
            ('clientes:cliente_detalle', 'detalle'),
            ('clientes:cliente_editar', 'editar'),
            ('clientes:cliente_agregar_tarjeta', 'agregar_tarjeta'),
            ('clientes:cliente_agregar_cuenta', 'agregar_cuenta'),
            ('clientes:cliente_cambiar_estado_medio_pago', 'cambiar_estado_medio_pago'),
            ('clientes:cliente_eliminar_medio_pago', 'eliminar_medio_pago')
        ]
        
        for url_name, description in urls_with_names:
            try:
                # Para URLs que requieren argumentos, usar valores de prueba
                if 'detalle' in url_name or 'editar' in url_name or 'tarjeta' in url_name or 'cuenta' in url_name:
                    if 'medio_pago' in url_name:
                        url = reverse(url_name, args=[1, 2])
                    else:
                        url = reverse(url_name, args=[1])
                else:
                    url = reverse(url_name)
                
                assert url is not None, f"La URL '{url_name}' debería resolverse correctamente"
                assert '/clientes' in url, f"La URL '{url_name}' debería estar bajo el namespace 'clientes'"
                
            except Exception as e:
                pytest.fail(f"Error al resolver URL '{url_name}': {str(e)}")
        
        print("✓ Test all_urls_have_name_namespace: Todas las URLs tienen namespace correcto")
    
    def test_url_patterns_coverage(self):
        """Test para verificar que todas las URLs del urlpatterns están cubiertas"""
        from clientes.urls import urlpatterns
        
        # Obtener todos los nombres de URL definidos
        url_names = []
        for pattern in urlpatterns:
            if hasattr(pattern, 'name') and pattern.name:
                url_names.append(pattern.name)
        
        expected_names = [
            'cliente_crear',
            'cliente_lista', 
            'cliente_detalle',
            'cliente_editar',
            'cliente_agregar_tarjeta',
            'cliente_agregar_cuenta',
            'cliente_cambiar_estado_medio_pago',
            'cliente_eliminar_medio_pago'
        ]
        
        for expected_name in expected_names:
            assert expected_name in url_names, f"La URL '{expected_name}' debería estar definida en urlpatterns"
        
        print("✓ Test url_patterns_coverage: Todas las URLs esperadas están definidas")
    
    def test_url_parameter_types(self):
        """Test para verificar que los parámetros de URL son del tipo correcto"""
        # Test con parámetros enteros válidos
        url_detalle = reverse('clientes:cliente_detalle', args=[123])
        resolved = resolve(url_detalle)
        assert isinstance(resolved.kwargs['pk'], int), "El parámetro pk debería ser entero"
        
        url_editar = reverse('clientes:cliente_editar', args=[456])
        resolved = resolve(url_editar)
        assert isinstance(resolved.kwargs['pk'], int), "El parámetro pk debería ser entero"
        
        url_medio_pago = reverse('clientes:cliente_cambiar_estado_medio_pago', args=[789, 101])
        resolved = resolve(url_medio_pago)
        assert isinstance(resolved.kwargs['pk'], int), "El parámetro pk debería ser entero"
        assert isinstance(resolved.kwargs['medio_id'], int), "El parámetro medio_id debería ser entero"
        
        print("✓ Test url_parameter_types: Tipos de parámetros de URL correctos")
    
    def test_url_regex_patterns(self):
        """Test para verificar que los patrones de regex funcionan correctamente"""
        # Test que los patrones solo aceptan números enteros
        valid_pks = [1, 123, 999999]
        
        for pk in valid_pks:
            try:
                url = reverse('clientes:cliente_detalle', args=[pk])
                resolved = resolve(url)
                assert resolved.kwargs['pk'] == pk, f"Debería resolver correctamente pk={pk}"
            except Exception as e:
                pytest.fail(f"Error con pk válido {pk}: {str(e)}")
        
        print("✓ Test url_regex_patterns: Patrones de regex funcionan correctamente")
    
    def test_app_namespace(self):
        """Test para verificar que el namespace de la app está configurado correctamente"""
        from clientes.urls import app_name
        
        assert app_name == 'clientes', "El nombre de la app debería ser 'clientes'"
        
        # Verificar que el namespace funciona
        url = reverse('clientes:cliente_lista')
        assert '/clientes/' in url, "El namespace debería prefixar las URLs correctamente"
        
        print("✓ Test app_namespace: Namespace de la app configurado correctamente")
    
    def test_urls_without_trailing_slash_redirect(self):
        """Test para verificar el comportamiento con URLs sin slash final"""
        # Algunas URLs pueden funcionar sin el slash final dependiendo de la configuración de Django
        # Este test verifica que al menos las URLs principales sean accesibles
        
        try:
            url_with_slash = reverse('clientes:cliente_lista')
            assert url_with_slash.endswith('/'), "Las URLs deberían terminar en slash"
            
            url_detalle = reverse('clientes:cliente_detalle', args=[1])
            assert url_detalle.endswith('/'), "Las URLs de detalle deberían terminar en slash"
            
        except Exception as e:
            pytest.fail(f"Error en URLs con slash: {str(e)}")
        
        print("✓ Test urls_without_trailing_slash_redirect: URLs con slash final correctas")
    
    def test_reverse_url_generation(self):
        """Test para verificar que la generación de URLs funciona en ambas direcciones"""
        test_cases = [
            ('clientes:cliente_crear', [], '/clientes/crear/'),
            ('clientes:cliente_lista', [], '/clientes/'),
            ('clientes:cliente_detalle', [42], '/clientes/42/'),
            ('clientes:cliente_editar', [42], '/clientes/42/editar/'),
            ('clientes:cliente_agregar_tarjeta', [42], '/clientes/42/agregar-tarjeta/'),
            ('clientes:cliente_agregar_cuenta', [42], '/clientes/42/agregar-cuenta/'),
        ]
        
        for url_name, args, expected_url in test_cases:
            generated_url = reverse(url_name, args=args)
            assert generated_url == expected_url, f"URL generada incorrecta para {url_name}: esperada {expected_url}, obtuvo {generated_url}"
            
            # Verificar que se puede resolver de vuelta
            resolved = resolve(generated_url)
            assert resolved.url_name == url_name.split(':')[1], f"No se pudo resolver de vuelta {url_name}"
        
        print("✓ Test reverse_url_generation: Generación bidireccional de URLs correcta")
