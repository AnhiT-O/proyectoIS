AnhiT-O: (dvenv) claudia@claudia-VM:~/Escritorio/ProyectoIS2/proyectoIS/proyecto$ python manage.py test tasa.tests -v 2
Found 10 test(s).
Creating test database for alias 'default' ('test_bd_desarrollo')...
Operations to perform:
  Synchronize unmigrated apps: messages, staticfiles
  Apply all migrations: auth, clientes, contenttypes, monedas, roles, sessions, tasa, usuarios
Synchronizing apps without migrations:
  Creating tables...
    Running deferred SQL...
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0001_initial... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying clientes.0001_initial... OK
  Applying usuarios.0001_initial... OK
  Applying clientes.0002_initial... OK
  Applying monedas.0001_initial... OK
  Applying roles.0001_initial... OK
  Applying sessions.0001_initial... OK
  Applying tasa.0001_initial... OK
Rol 'operador' creado exitosamente.
Rol 'analista cambiario' creado exitosamente.
Rol 'administrador' creado exitosamente.
Al grupo 'administrador' se le han asignado todos los permisos después de migrar django.contrib.auth.
Al grupo 'administrador' se le han asignado todos los permisos después de migrar django.contrib.contenttypes.
Al grupo 'administrador' se le han asignado todos los permisos después de migrar django.contrib.sessions.
Al grupo 'administrador' se le han asignado todos los permisos después de migrar usuarios.
Al grupo 'administrador' se le han asignado todos los permisos después de migrar clientes.
Al grupo 'administrador' se le han asignado todos los permisos después de migrar roles.
Al grupo 'administrador' se le han asignado todos los permisos después de migrar monedas.
Al grupo 'administrador' se le han asignado todos los permisos después de migrar tasa.
✅ Permisos de tasas asignados al grupo administrador
✅ Permisos de tasas asignados al grupo analista cambiario
System check identified no issues (0 silenced).
test_formulario_comision_invalida (tasa.tests.test_forms.TasaCambioFormTest.test_formulario_comision_invalida)
Verifica que el formulario rechace comisiones inválidas ... ok
test_formulario_precio_base_invalido (tasa.tests.test_forms.TasaCambioFormTest.test_formulario_precio_base_invalido)
Verifica que el formulario rechace precios base inválidos ... ok
test_formulario_valido (tasa.tests.test_forms.TasaCambioFormTest.test_formulario_valido)
Verifica que el formulario acepte datos válidos ... ok
test_creacion_tasa (tasa.tests.test_models.TasaCambioModelTest.test_creacion_tasa)
Verifica que se pueda crear una tasa de cambio correctamente ... ERROR
test_str_representation (tasa.tests.test_models.TasaCambioModelTest.test_str_representation)
Verifica la representación en cadena del modelo ... ERROR
test_validacion_comisiones (tasa.tests.test_models.TasaCambioModelTest.test_validacion_comisiones)
Verifica que las comisiones no puedan ser mayores a 1 (100%) ... ERROR
test_crear_tasa_valida (tasa.tests.test_views.TasaCambioViewTest.test_crear_tasa_valida)
Verifica que se pueda crear una tasa válida ... ERROR
test_editar_tasa (tasa.tests.test_views.TasaCambioViewTest.test_editar_tasa)
Verifica que se pueda editar una tasa existente ... ERROR
test_lista_tasas_autenticado (tasa.tests.test_views.TasaCambioViewTest.test_lista_tasas_autenticado)
Verifica que usuarios autenticados puedan ver la lista ... ERROR
test_lista_tasas_sin_autenticar (tasa.tests.test_views.TasaCambioViewTest.test_lista_tasas_sin_autenticar)
Verifica que usuarios no autenticados sean redirigidos ... ERROR

======================================================================
ERROR: test_creacion_tasa (tasa.tests.test_models.TasaCambioModelTest.test_creacion_tasa)
Verifica que se pueda crear una tasa de cambio correctamente
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/tasa/tests/test_models.py", line 23, in setUp
    self.usuario = get_user_model().objects.create_user(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 175, in create_user
    return self._create_user(username, email, password, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 162, in _create_user
    user = self._create_user_object(username, email, password, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 154, in _create_user_object
    user = self.model(username=username, email=email, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/db/models/base.py", line 569, in __init__
    raise TypeError(
TypeError: Usuario() got unexpected keyword arguments: 'is_staff'

======================================================================
ERROR: test_str_representation (tasa.tests.test_models.TasaCambioModelTest.test_str_representation)
Verifica la representación en cadena del modelo
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/tasa/tests/test_models.py", line 23, in setUp
    self.usuario = get_user_model().objects.create_user(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 175, in create_user
    return self._create_user(username, email, password, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 162, in _create_user
    user = self._create_user_object(username, email, password, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 154, in _create_user_object
    user = self.model(username=username, email=email, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/db/models/base.py", line 569, in __init__
    raise TypeError(
TypeError: Usuario() got unexpected keyword arguments: 'is_staff'

======================================================================
ERROR: test_validacion_comisiones (tasa.tests.test_models.TasaCambioModelTest.test_validacion_comisiones)
Verifica que las comisiones no puedan ser mayores a 1 (100%)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/tasa/tests/test_models.py", line 23, in setUp
    self.usuario = get_user_model().objects.create_user(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 175, in create_user
    return self._create_user(username, email, password, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 162, in _create_user
    user = self._create_user_object(username, email, password, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 154, in _create_user_object
    user = self.model(username=username, email=email, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/db/models/base.py", line 569, in __init__
    raise TypeError(
TypeError: Usuario() got unexpected keyword arguments: 'is_staff'

======================================================================
ERROR: test_crear_tasa_valida (tasa.tests.test_views.TasaCambioViewTest.test_crear_tasa_valida)
Verifica que se pueda crear una tasa válida
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/tasa/tests/test_views.py", line 25, in setUp
    self.usuario = get_user_model().objects.create_user(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 175, in create_user
    return self._create_user(username, email, password, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 162, in _create_user
    user = self._create_user_object(username, email, password, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 154, in _create_user_object
    user = self.model(username=username, email=email, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/db/models/base.py", line 569, in __init__
    raise TypeError(
TypeError: Usuario() got unexpected keyword arguments: 'is_staff'

======================================================================
ERROR: test_editar_tasa (tasa.tests.test_views.TasaCambioViewTest.test_editar_tasa)
Verifica que se pueda editar una tasa existente
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/tasa/tests/test_views.py", line 25, in setUp
    self.usuario = get_user_model().objects.create_user(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 175, in create_user
    return self._create_user(username, email, password, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 162, in _create_user
    user = self._create_user_object(username, email, password, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 154, in _create_user_object
    user = self.model(username=username, email=email, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/db/models/base.py", line 569, in __init__
    raise TypeError(
TypeError: Usuario() got unexpected keyword arguments: 'is_staff'

======================================================================
ERROR: test_lista_tasas_autenticado (tasa.tests.test_views.TasaCambioViewTest.test_lista_tasas_autenticado)
Verifica que usuarios autenticados puedan ver la lista
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/tasa/tests/test_views.py", line 25, in setUp
    self.usuario = get_user_model().objects.create_user(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 175, in create_user
    return self._create_user(username, email, password, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 162, in _create_user
    user = self._create_user_object(username, email, password, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 154, in _create_user_object
    user = self.model(username=username, email=email, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/db/models/base.py", line 569, in __init__
    raise TypeError(
TypeError: Usuario() got unexpected keyword arguments: 'is_staff'

======================================================================
ERROR: test_lista_tasas_sin_autenticar (tasa.tests.test_views.TasaCambioViewTest.test_lista_tasas_sin_autenticar)
Verifica que usuarios no autenticados sean redirigidos
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/tasa/tests/test_views.py", line 25, in setUp
    self.usuario = get_user_model().objects.create_user(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 175, in create_user
    return self._create_user(username, email, password, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 162, in _create_user
    user = self._create_user_object(username, email, password, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 154, in _create_user_object
    user = self.model(username=username, email=email, **extra_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/db/models/base.py", line 569, in __init__
    raise TypeError(
TypeError: Usuario() got unexpected keyword arguments: 'is_staff'

----------------------------------------------------------------------
Ran 10 tests in 0.329s

FAILED (errors=7)
Destroying test database for alias 'default' ('test_bd_desarrollo')...

GitHub Copilot: Ahora veo que el error está en la creación del usuario de prueba. El modelo de Usuario personalizado que estamos usando no acepta el campo `is_staff`. Voy a revisar los archivos de prueba y ajustar la creación del usuario: Ahora veo que nuestro modelo `Usuario` personalizado no usa `is_staff`. Voy a actualizar los archivos de prueba para que usen solo los campos necesarios: 
```


Se realizaron cambios.


```

```


Se realizaron cambios.


```
He actualizado los archivos de prueba para que incluyan todos los campos requeridos por nuestro modelo `Usuario` personalizado:

1. Campos requeridos agregados:
   - first_name
   - last_name
   - email
   - tipo_cedula
   - cedula_identidad

2. Eliminé el campo `is_staff` que estaba causando el error ya que nuestro modelo no lo utiliza.

Ahora puedes volver a ejecutar las pruebas con:

```bash
python manage.py test tasa.tests -v 2
```

Los errores deberían desaparecer ya que ahora estamos creando el usuario de prueba con todos los campos requeridos por nuestro modelo personalizado. Las pruebas probarán:
- Validación de formularios
- Creación y edición de tasas
- Permisos y autenticación
- Validación de comisiones
- Representación en cadena del modelo

AnhiT-O: python manage.py test tasa.tests -v 2

GitHub Copilot: Ejecutaré el comando de pruebas en el terminal: 