AnhiT-O: comision venta y Comision compra son las comisiones de las monedas que se venden o se compra elimina las columnas Comision vta Destino y comision comp origen


GitHub Copilot:

Actualizaré dos archivos:

1. views.py — usar comision_compra/comision_venta en las fórmulas y eliminar comision_comp_origen/comision_vta_destino del resultado.
2. transacciones_reportes.html — eliminar las columnas Comision Comp Origen y Comision Vta Destino del template y ajustar el footer.
Ahora aplico los cambios.

views.py+5-9
transacciones_reportes.html+1-5
He actualizado la lógica y la plantilla de reportes:

- Eliminé las columnas comision_comp_origen y comision_vta_destino.
- Ahora las ganancias se calculan exclusivamente con comision_compra y comision_venta usando las fórmulas solicitadas.
- La tabla y el total se ajustaron en la plantilla.
Regenera y prueba accesando /reportes/transacciones/ con un usuario del grupo 'Administrador'. Si necesitas formateo numérico o filtros, lo agrego.