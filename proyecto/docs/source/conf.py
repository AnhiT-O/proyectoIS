# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Global Exchange'
copyright = '2025, Grupo 1'
author = 'Grupo 1'
release = 'Versión 2'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon'
]

templates_path = ['_templates']
exclude_patterns = []

language = 'es'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

napoleon_google_docstring = True

import os
import sys
sys.path.insert(0, os.path.abspath('../../../'))
sys.path.insert(0, os.path.abspath('../../'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
import django
django.setup()

html_context = {
    'display_github': False,
    'last_updated': True,
    'commit': False,
    'show_source': False  # Oculta "Show source"
}

# Hook para omitir miembros internos de Django
def skip_member_handler(app, what, name, obj, skip, options):
    # Omitir todo lo interno (empieza con _) y descriptores
    if name.startswith('_') or 'Descriptor' in name or name in ['objects', 'DoesNotExist', 'MultipleObjectsReturned']:
        return True  # se omite

    # Omitir atributos de tipo DeferredAttribute (campos de Django)
    from django.db.models.fields import Field
    from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor, ReverseManyToOneDescriptor

    if hasattr(obj, '__class__'):
        cls = obj.__class__.__name__
        if cls == 'DeferredAttribute':
            return True
        if isinstance(obj, (ForwardManyToOneDescriptor, ReverseManyToOneDescriptor)):
            return True

    return None  # Sphinx decide por defecto para los demás

def setup(app):
    app.connect("autodoc-skip-member", skip_member_handler)