### creame la tabla de base de datos que se llame limitaciones y que tenga los siguientes atributos: id_limitacion, id_moneda, segmentacion (vip, corporativo,  minorista),  porcentaje limite 

Voy a crear un nuevo modelo para la tabla de limitaciones. Primero, necesitamos determinar dónde crear este modelo. Como está relacionado con monedas, lo agregaremos en la aplicación `monedas`. 

Leer [](file:///home/aylen/Documentos/IS2/proyectoIS/proyecto/monedas/models.py#1-1), líneas 1 a 50

Voy a agregar el modelo `Limitacion` en el archivo models.py: 

Usando "Reemplazar cadena en archivo"


```

```


Usando "Reemplazar cadena en archivo"


```

```
He creado el modelo `Limitacion` con las siguientes características:

1. **Campos**:
   - `id`: Django lo crea automáticamente como clave primaria
   - `moneda`: Clave foránea a la tabla `Moneda`
   - `segmentacion`: Campo de texto con opciones predefinidas (VIP, CORPORATIVO, MINORISTA)
   - `porcentaje_limite`: Campo decimal con validación de 0 a 100%

2. **Características**:
   - La tabla se llamará `limitaciones`
   - Tiene una restricción única para que no pueda haber duplicados de moneda-segmentación
   - El porcentaje límite está validado para estar entre 0 y 100
   - Si se elimina una moneda, se eliminarán sus limitaciones (CASCADE)

Para crear la tabla en la base de datos, ejecuta:

```bash
python manage.py makemigrations monedas
python manage.py migrate
```

Esto creará la nueva tabla en la base de datos con todos los campos especificados.

Se realizaron cambios.


