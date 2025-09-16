Josias-Esp: Cambia la clase CambiarCategoriaView en #file:views.py por una funcion y utiliza los permisos como las otras funciones para que solo el administrador acceda

GitHub Copilot: Voy a cambiar la clase `CambiarCategoriaView` por una función que use los mismos decoradores de permisos que las otras funciones: 
```


Se realizaron cambios.


```

```


Se realizaron cambios.


```
Ahora necesito actualizar las URLs para usar la función en lugar de la clase: 
```


Se realizaron cambios.


```
Perfecto. He cambiado la clase `CambiarCategoriaView` por una función `cambiar_categoria` que:

1. **Usa los mismos decoradores**: `@login_required` y `@permission_required('clientes.gestion', raise_exception=True)` como las otras funciones
2. **Mantiene la verificación de administrador**: Verifica que `request.user.is_staff` sea True
3. **Conserva la misma funcionalidad**: Maneja tanto GET como POST requests
4. **Actualicé las URLs**: Para usar la función en lugar de la clase

La función ahora tiene la misma estructura y permisos que las otras funciones del archivo, manteniendo la consistencia del código.