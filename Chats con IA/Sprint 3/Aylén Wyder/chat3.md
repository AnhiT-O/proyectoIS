### AttributeError at /
'Moneda' object has no attribute 'calcular_precio_compra'
Request Method:	GET
Request URL:	http://127.0.0.1:8000/
Django Version:	5.2.6
Exception Type:	AttributeError
Exception Value:	
'Moneda' object has no attribute 'calcular_precio_compra'
Exception Location:	/home/aylen/Documentos/IS2/proyectoIS/proyecto/proyecto/views.py, line 56, in inicio
Raised during:	proyecto.views.inicio
Python Executable:	/home/aylen/Documentos/IS2/proyectoIS/dvenv/bin/python
Python Version:	3.12.3
Python Path:	
['/home/aylen/Documentos/IS2/proyectoIS/proyecto',
 '/usr/lib/python312.zip',
 '/usr/lib/python3.12',
 '/usr/lib/python3.12/lib-dynload',
 '/home/aylen/Documentos/IS2/proyectoIS/dvenv/lib/python3.12/site-packages']
Server time:	Sat, 20 Sep 2025 15:58:22 -0300

El error indica que falta el método `calcular_precio_compra` en el modelo `Moneda`. Voy a revisar el archivo completo para ver qué métodos están faltando: 

Leer [](file:///home/aylen/Documentos/IS2/proyectoIS/proyecto/monedas/models.py#70-70), líneas 70 a 152

Veo que hay métodos duplicados y el archivo está mal estructurado. Voy a ver el archivo completo para identificar el problema: 

Leer [](file:///home/aylen/Documentos/IS2/proyectoIS/proyecto/monedas/models.py)

Veo el problema. El archivo tiene contenido duplicado y los métodos `calcular_precio_compra` y `calcular_precio_venta` están en la clase `Limitacion` en lugar de estar en la clase `Moneda`. Voy a corregir esto: 

Usando "Reemplazar cadena en archivo"


```

```
Ahora voy a limpiar la clase Limitacion para eliminar los métodos duplicados: 

Usando "Reemplazar cadena en archivo"


```

```
Ahora voy a verificar que el archivo esté bien estructurado: 

Leer [](file:///home/aylen/Documentos/IS2/proyectoIS/proyecto/monedas/models.py#100-100), líneas 100 a 150

Perfecto. Ahora voy a reiniciar el servidor para que tome los cambios: 

Ran terminal command: pkill -f "python manage.py runserver"

Ran terminal command: cd /home/aylen/Documentos/IS2/proyectoIS && source dvenv/bin/activate && cd proyecto && python manage.py runserver

Se comprobó la salida del terminal en segundo plano

¡Excelente! El servidor está funcionando correctamente. Ahora voy a probar que los métodos estén funcionando bien: 

Ran terminal command: source dvenv/bin/activate && python proyecto/test_limitaciones.py

Voy a crear un nuevo test para verificar que los métodos de precio funcionen: 

Se ha creado [](file:///home/aylen/Documentos/IS2/proyectoIS/proyecto/test_precios.py)

Ran terminal command: cd /home/aylen/Documentos/IS2/proyectoIS && source dvenv/bin/activate && python proyecto/test_precios.py

¡Perfecto! El error ha sido corregido. Los métodos `calcular_precio_compra` y `calcular_precio_venta` ahora están correctamente ubicados en la clase `Moneda` y funcionan como se esperaba.

## ✅ **Problema resuelto:**

**Error:** `'Moneda' object has no attribute 'calcular_precio_compra'`

**Causa:** Los métodos estaban duplicados y mal ubicados en la clase `Limitacion` en lugar de la clase `Moneda`.

**Solución aplicada:**
1. ✅ Movidos los métodos `calcular_precio_compra()` y `calcular_precio_venta()` a la clase `Moneda`
2. ✅ Eliminado contenido duplicado del archivo
3. ✅ Agregado método `get_precios_cliente()` para obtener ambos precios con beneficio
4. ✅ Verificado que todos los métodos funcionen correctamente

**Métodos disponibles en la clase Moneda:**
- `calcular_precio_compra(porcentaje_beneficio=0)`
- `calcular_precio_venta(porcentaje_beneficio=0)`
- `get_precios_cliente(cliente)`
- `get_limite_por_segmentacion(segmentacion)`
- `get_cantidad_maxima_por_segmentacion(segmentacion)`
- `tiene_stock_disponible(cantidad_solicitada, segmentacion)`

El servidor debería funcionar correctamente ahora. Puedes acceder a http://127.0.0.1:8000/ sin errores.

Se realizaron cambios.




