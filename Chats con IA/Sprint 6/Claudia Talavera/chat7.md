AnhiT-O: Agrega un nuevo filtro en #file:transacciones_reportes.html para tipo de transaccion ya sea compra o venta

GitHub Copilot:Agregaré el filtro GET "tipo" en la vista para filtrar por compra/venta y pasaré su valor al contexto; además añadiré el select de tipo en el formulario de filtros de la plantilla.

Ahora edito los archivos `views.py` y `transacciones_reportes.html`.

## views.py+4-0
## transacciones_reportes.html+8-0
He añadido el filtro "Tipo" (compra/venta) al formulario y lo integré en la vista. Ahora puedes filtrar por tipo y ver solo la tabla correspondiente en el informe.

¿Quieres que el filtro "Tipo" también oculte automáticamente la tabla vacía y seleccione columnas dinámicamente?