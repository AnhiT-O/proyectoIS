AnhiT-O: Realiza estos cambios En una transacción de venta, solo mostrás la comisión y ganancia de venta. y el descuento corresponde al segmento del tipo de cliente ya sea vip, corporativo o minorista en #file:clientes

En una transacción de compra, solo mostrás la comisión y ganancia de compra.

La ganancia total se coloca en un resumen (por moneda), no en cada fila.
Es la suma global de todas las ganancias parciales (compra + venta) en el período

GitHub Copilot:
## views.py
Modificaré dos archivos:
1. reportes/views.py — calcular comisiones/ganancias según tipo (solo mostrar la correspondiente), obtener descuento desde cliente.segmento, y generar resumen_por_moneda con suma de ganancias en el período.

2. transacciones_reportes.html — mantener tabla y añadir sección de resumen por moneda debajo de la tabla.

Ahora edito los archivos.

## views.py+48-48
## transacciones_reportes.html+23-1

He aplicado los cambios solicitados:

- En ventas se muestran solo comisión y ganancia de venta.
- En compras se muestran solo comisión y ganancia de compra.
- El porcentaje de descuento se toma del segmento del cliente (si existe); si no, usa el campo en la transacción.
- La ganancia total aparece solo en el resumen por moneda.
- Si necesitas formateo numérico en tabla y resumen, lo ajusto.