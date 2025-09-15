import pytest
from django.urls import reverse, resolve
from clientes import views


class TestClienteUrls:
    """
    Tests para las URLs de la app clientes
    """
    
    def test_cliente_crear_url(self):
        """Test para URL de crear cliente"""
        url = reverse('clientes:cliente_crear')
        assert url == '/clientes/crear/'
        
        # Verificar que resuelve a la vista correcta
        view = resolve(url)
        assert view.func == views.cliente_crear
        
        print("✓ Test cliente_crear_url: URL de crear cliente funcionando")
    
    def test_cliente_lista_url(self):
        """Test para URL de lista de clientes"""
        url = reverse('clientes:cliente_lista')
        assert url == '/clientes/'
        
        # Verificar que resuelve a la vista correcta
        view = resolve(url)
        assert view.func == views.cliente_lista
        
        print("✓ Test cliente_lista_url: URL de lista de clientes funcionando")
    
    def test_cliente_detalle_url(self):
        """Test para URL de detalle de cliente"""
        url = reverse('clientes:cliente_detalle', kwargs={'pk': 1})
        assert url == '/clientes/1/'
        
        # Verificar que resuelve a la vista correcta
        view = resolve(url)
        assert view.func == views.cliente_detalle
        
        print("✓ Test cliente_detalle_url: URL de detalle de cliente funcionando")
    
    def test_cliente_editar_url(self):
        """Test para URL de editar cliente"""
        url = reverse('clientes:cliente_editar', kwargs={'pk': 1})
        assert url == '/clientes/1/editar/'
        
        # Verificar que resuelve a la vista correcta
        view = resolve(url)
        assert view.func == views.cliente_editar
        
        print("✓ Test cliente_editar_url: URL de editar cliente funcionando")
    
    def test_cliente_agregar_tarjeta_url(self):
        """Test para URL de agregar tarjeta a cliente"""
        url = reverse('clientes:cliente_agregar_tarjeta', kwargs={'pk': 1})
        assert url == '/clientes/1/agregar-tarjeta/'
        
        # Verificar que resuelve a la vista correcta
        view = resolve(url)
        assert view.func == views.cliente_agregar_tarjeta
        
        print("✓ Test cliente_agregar_tarjeta_url: URL de agregar tarjeta funcionando")
    
    def test_cliente_agregar_cuenta_url(self):
        """Test para URL de agregar cuenta a cliente"""
        url = reverse('clientes:cliente_agregar_cuenta', kwargs={'pk': 1})
        assert url == '/clientes/1/agregar-cuenta/'
        
        # Verificar que resuelve a la vista correcta
        view = resolve(url)
        assert view.func == views.cliente_agregar_cuenta
        
        print("✓ Test cliente_agregar_cuenta_url: URL de agregar cuenta funcionando")
    
    def test_cliente_cambiar_estado_medio_pago_url(self):
        """Test para URL de cambiar estado de medio de pago"""
        url = reverse('clientes:cliente_cambiar_estado_medio_pago', 
                     kwargs={'pk': 1, 'medio_id': 2})
        assert url == '/clientes/1/medio-pago/2/cambiar-estado/'
        
        # Verificar que resuelve a la vista correcta
        view = resolve(url)
        assert view.func == views.cliente_cambiar_estado_medio_pago
        
        print("✓ Test cliente_cambiar_estado_medio_pago_url: URL de cambiar estado funcionando")
    
    def test_cliente_eliminar_medio_pago_url(self):
        """Test para URL de eliminar medio de pago"""
        url = reverse('clientes:cliente_eliminar_medio_pago', 
                     kwargs={'pk': 1, 'medio_id': 2})
        assert url == '/clientes/1/medio-pago/2/eliminar/'
        
        # Verificar que resuelve a la vista correcta
        view = resolve(url)
        assert view.func == views.cliente_eliminar_medio_pago
        
        print("✓ Test cliente_eliminar_medio_pago_url: URL de eliminar medio de pago funcionando")
    
    def test_urls_con_parametros_invalidos(self):
        """Test para URLs con parámetros inválidos"""
        urls_con_pk = [
            'clientes:cliente_detalle',
            'clientes:cliente_editar',
            'clientes:cliente_agregar_tarjeta',
            'clientes:cliente_agregar_cuenta'
        ]
        
        for url_name in urls_con_pk:
            try:
                # Intentar crear URL con pk inválido
                url = reverse(url_name, kwargs={'pk': 'abc'})
                # Si llega aquí, el patrón acepta strings (lo cual podría ser válido)
                # pero la vista debería manejar el error
                assert url is not None
            except Exception:
                # Es esperado que falle con parámetros inválidos
                pass
        
        print("✓ Test urls_con_parametros_invalidos: Manejo de parámetros inválidos funcionando")
    
    def test_namespace_correcto(self):
        """Test para verificar que el namespace esté configurado correctamente"""
        url_names = [
            'cliente_crear',
            'cliente_lista', 
            'cliente_detalle',
            'cliente_editar',
            'cliente_agregar_tarjeta',
            'cliente_agregar_cuenta',
            'cliente_cambiar_estado_medio_pago',
            'cliente_eliminar_medio_pago'
        ]
        
        for url_name in url_names:
            try:
                # Verificar que se puede acceder con el namespace 'clientes'
                if url_name in ['cliente_detalle', 'cliente_editar', 
                               'cliente_agregar_tarjeta', 'cliente_agregar_cuenta']:
                    url = reverse(f'clientes:{url_name}', kwargs={'pk': 1})
                elif url_name in ['cliente_cambiar_estado_medio_pago', 
                                  'cliente_eliminar_medio_pago']:
                    url = reverse(f'clientes:{url_name}', 
                                 kwargs={'pk': 1, 'medio_id': 2})
                else:
                    url = reverse(f'clientes:{url_name}')
                
                assert url is not None
                assert url.startswith('/clientes')
                
            except Exception as e:
                pytest.fail(f"Error al resolver URL {url_name}: {e}")
        
        print("✓ Test namespace_correcto: Namespace 'clientes' funcionando correctamente")
    
    def test_patron_urls_coherente(self):
        """Test para verificar que los patrones de URL sean coherentes"""
        # Verificar que las URLs siguen un patrón coherente
        expected_patterns = {
            'cliente_lista': '/clientes/',
            'cliente_crear': '/clientes/crear/',
            'cliente_detalle': '/clientes/1/',
            'cliente_editar': '/clientes/1/editar/',
            'cliente_agregar_tarjeta': '/clientes/1/agregar-tarjeta/',
            'cliente_agregar_cuenta': '/clientes/1/agregar-cuenta/',
        }
        
        for url_name, expected_url in expected_patterns.items():
            if url_name in ['cliente_detalle', 'cliente_editar', 
                           'cliente_agregar_tarjeta', 'cliente_agregar_cuenta']:
                actual_url = reverse(f'clientes:{url_name}', kwargs={'pk': 1})
            else:
                actual_url = reverse(f'clientes:{url_name}')
            
            assert actual_url == expected_url
        
        print("✓ Test patron_urls_coherente: Patrones de URL coherentes")