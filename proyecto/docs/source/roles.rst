Roles
======

Modelo de Roles personalizado que extiende auth.Group de Django.
Incluye la creación automática de roles predefinidos y gestión de permisos.

Roles predefinidos:

- Operador
- Analista cambiario
- Administrador

.. automodule:: roles.models
    :members:
    :exclude-members: DoesNotExist, MultipleObjectsReturned
    :show-inheritance:

.. automodule:: roles.views
    :members:
    :show-inheritance:
    
.. automodule:: roles.forms
    :members:
    :exclude-members: media
    :show-inheritance:

.. automodule:: roles.signals
    :members:
    :show-inheritance:
