"""
Configuración compartida de pytest para ambos proyectos Django.
"""
import os
import sys
import django

# Agregar las rutas de ambos proyectos al PYTHONPATH
ROOT_DIR = os.path.dirname(__file__)
proyecto_path = os.path.join(ROOT_DIR, 'proyecto')
tauser_path = os.path.join(ROOT_DIR, 'tauser')

if proyecto_path not in sys.path:
    sys.path.insert(0, proyecto_path)
if tauser_path not in sys.path:
    sys.path.insert(0, tauser_path)

def pytest_configure(config):
    """Configurar Django para los tests."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
    
    try:
        django.setup()
    except RuntimeError:
        pass

def pytest_collection_modifyitems(config, items):
    """Agregar marcadores automáticos basados en la ruta."""
    import pytest
    for item in items:
        if 'proyecto' in str(item.fspath):
            item.add_marker(pytest.mark.proyecto)
        elif 'tauser' in str(item.fspath):
            item.add_marker(pytest.mark.tauser)