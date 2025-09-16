AnhiT-O: los usuarios con rol de analista cambiario tambien pueden modificar la tasa

GitHub Copilot: Voy a revisar la estructura de roles y permisos primero: Veo que existe un rol predefinido de "analista cambiario". Para permitir que este rol pueda modificar tasas de cambio, debemos asegurarnos de que tenga los permisos necesarios. Voy a revisar si hay un script o vista que asigne los permisos a los roles: Voy a crear un nuevo archivo `signals.py` en la app `tasa` para asignar automáticamente los permisos al rol de analista cambiario: 

Se realizaron cambios.

Ahora necesitamos asegurarnos de que los signals se carguen cuando se inicia la aplicación. Para esto, voy a modificar el archivo `apps.py` de la app `tasa`: 
```


Se realizaron cambios.


```
Con estos cambios:

1. He creado un nuevo archivo `signals.py` que asigna automáticamente los permisos necesarios (`ver_tasa` y `editar_tasa`) al rol de analista cambiario.
2. He modificado apps.py para cargar los signals cuando se inicia la aplicación.

Ahora los usuarios con el rol de analista cambiario podrán:
- Ver las tasas de cambio (`ver_tasa`)
- Modificar las tasas existentes (`editar_tasa`)

Pero no podrán:
- Crear nuevas tasas
- Activar/desactivar tasas

Estas últimas acciones seguirán siendo exclusivas del rol de administrador.

Para aplicar estos cambios, necesitarás:

1. Hacer las migraciones de la base de datos:
```bash
python manage.py makemigrations
python manage.py migrate
```

2. Reiniciar el servidor Django para que los cambios en los signals tomen efecto.

Los analistas cambiarios ahora podrán ver y modificar las tasas de cambio desde el panel de administración, pero las opciones de crear y activar/desactivar solo serán visibles para los administradores.