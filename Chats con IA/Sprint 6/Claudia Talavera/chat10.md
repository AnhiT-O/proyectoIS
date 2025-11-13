AnhiT-O:disminuye la cantidad de decimales de las comisiones con 2 ya es suficiente y en descuento muestra el beneficio_segmento de `#file:transacciones_reportes.html`


GitHub Copilot:Actualizaré views.py para incluir el campo 'beneficio_segmento' en cada fila (tomándolo del segmento si existe) y actualizaré la plantilla para reducir comisiones a 2 decimales y mostrar 'beneficio_segmento' en la columna de descuento cuando exista. Ahora edito ambos archivos.

<views.py+6-0>
<transacciones_reportes.html+16-4>
He reducido las comisiones a 2 decimales y añadí la lógica para mostrar beneficio_segmento en la columna de descuento cuando exista. También pasé 'beneficio_segmento' desde la vista.

Verifica con clientes que tengan un atributo beneficio en su segmento y dime si quieres mostrar el beneficio como porcentaje o texto.