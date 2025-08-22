from django.test import TestCase
from clientes.apps import ClientesConfig

class ClientesConfigTest(TestCase):
    def test_apps_config(self):
        """Test the app configuration"""
        self.assertEqual(ClientesConfig.name, 'clientes')
        self.assertEqual(ClientesConfig.default_auto_field, 'django.db.models.BigAutoField')