
AnhiT-O: tambien quiero que se vea quien fue el ultimo en realiza el cambio a la tasa y tener en cuenta que Solo se puede hacer cambios de divisas si una moneda es el guaraní (ya sea origen o destino), por ejemplo  es decir yo vendo guaraní y cambio por dólares o compro guarani y lo cambio por reales la moneda base es el guaraní

GitHub Copilot: Entiendo. Necesitamos modificar el modelo para incluir el usuario que realizó el último cambio y agregar la validación para asegurar que una de las monedas sea guaraní. Primero, veamos el modelo actual: Voy a modificar el modelo para agregar el usuario que realizó el último cambio y la validación del guaraní: 
```


Se realizaron cambios.


```

```


Se realizaron cambios.


```
Ahora necesitamos actualizar las vistas para guardar el usuario que realiza los cambios: 
```


Se realizaron cambios.


```

```


Se realizaron cambios.


```

```


Se realizaron cambios.


```
Ahora necesitamos actualizar la plantilla para mostrar el último editor: 
```


Se realizaron cambios.


```

```


Se realizaron cambios.


```
He realizado los siguientes cambios:

1. En el modelo `TasaCambio`:
   - Agregado campo `ultimo_editor` que referencia al usuario que realizó el último cambio
   - Agregada validación para asegurar que al menos una de las monedas sea Guaraní (PYG)

2. En las vistas:
   - Modificadas `crear_tasa`, `editar_tasa` y `activar_tasa` para guardar el usuario que realiza el cambio
   - Se guarda el usuario en el campo `ultimo_editor` antes de cada save()

3. En la plantilla:
   - Agregada nueva columna que muestra el último editor
   - Se muestra el nombre completo del usuario o su username si no tiene nombre completo
   - Se muestra la fecha y hora de la última modificación

Para aplicar estos cambios, necesitas:

1. Hacer las migraciones para el nuevo campo:
```bash
python manage.py makemigrations
python manage.py migrate
```

2. Asegurarte de que exista una moneda Guaraní con el símbolo "PYG" en la base de datos

Ahora el sistema:
- Registra quién realizó el último cambio en cada tasa
- Solo permite tasas de cambio que involucren al Guaraní (PYG)
- Muestra esta información en la interfaz de usuario

¿Necesitas alguna modificación adicional o tienes alguna pregunta?