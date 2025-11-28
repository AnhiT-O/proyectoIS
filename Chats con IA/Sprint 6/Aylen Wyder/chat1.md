DoesNotExist at /ingreso-billetes/2JTYK6OW/
Tauser matching query does not exist.
Request Method:	POST
Request URL:	http://127.0.0.1:8010/ingreso-billetes/2JTYK6OW/
Django Version:	5.2.6
Exception Type:	DoesNotExist
Exception Value:	
Tauser matching query does not exist.
Exception Location:	/home/aylen/Documentos/IS2/proyectoIS/dvenv/lib/python3.12/site-packages/django/db/models/query.py, line 633, in get
Raised during:	tauser.views.ingreso_billetes
Python Executable:	/home/aylen/Documentos/IS2/proyectoIS/dvenv/bin/python
Python Version:	3.12.3
Python Path:	
['/home/aylen/Documentos/IS2/proyectoIS/tauser',
 '/usr/lib/python312.zip',
 '/usr/lib/python3.12',
 '/usr/lib/python3.12/lib-dynload',
 '/home/aylen/Documentos/IS2/proyectoIS/dvenv/lib/python3.12/site-packages']
Server time:	Wed, 19 Nov 2025 22:18:21 -0300

El error indica que no existe un registro de `Tauser` con el puerto `8010`. Analizando el código en `ingreso_billetes` y `caja_fuerte`, veo que ambas funciones intentan obtener el TAUser por el puerto de la solicitud:

```python
tauser = Tauser.objects.get(puerto=int(request.get_port()))
```

## Solución

Necesitas crear el registro de TAUser en la base de datos para el puerto que estás usando. Aquí te muestro las opciones:

### Opción 1: Crear el TAUser mediante Django Admin o Shell

```python
# Ejecuta esto en el shell de Django
python manage.py shell
```

```python
from transacciones.models import Tauser

# Crear TAUser para el puerto 8010
tauser = Tauser.objects.create(
    puerto=8010,
    nombre='TAUser Principal',  # o el nombre que prefieras
    activo=True
)
print(f'TAUser creado: {tauser.nombre} en puerto {tauser.puerto}')
```

### Opción 2: Crear mediante migración o fixture

Crea un archivo de fixture:

````python
[
  {
    "model": "transacciones.tauser",
    "pk": 1,
    "fields": {
      "nombre": "TAUser Principal",
      "puerto": 8010,
      "activo": true
    }
  }
]
````

Luego carga el fixture:

```bash
python manage.py loaddata tauser_inicial
```

### Opción 3: Agregar al archivo backup_datos.sql

Si prefieres incluirlo en tu backup, agrega esta línea SQL:

```sql
INSERT INTO transacciones_tauser (id, nombre, puerto, activo) 
VALUES (1, 'TAUser Principal', 8010, true);
```

## Formato del archivo de billetes

Basándome en el código de `ingreso_billetes`, el archivo `.txt` debe tener este formato:

````txt
Guaraní	50000	5
Guaraní	20000	10
Guaraní	10000	15
````

````txt
Dólar	100	2
Dólar	50	4
Dólar	20	5
````

**Formato:**
- **Sin línea de encabezado** (diferente a caja_fuerte)
- **Columnas separadas por TAB** (no espacios)
- **Columna 1**: Nombre de la moneda (`"Guaraní"`, `"Dólar"`, `"Euro"`, etc.)
- **Columna 2**: Valor de la denominación (número entero)
- **Columna 3**: Cantidad de billetes (número entero)

**Para COMPRAS**: Solo billetes en Guaraní
**Para VENTAS**: Solo billetes de la moneda extranjera que se está vendiendo
