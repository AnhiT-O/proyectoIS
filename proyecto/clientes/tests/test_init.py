from django.test import TestCase

class InitTest(TestCase):
    def test_import(self):
        """Test that the app can be imported"""
        import clientes
        self.assertIsNotNone(clientes)