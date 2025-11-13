
AnhiT-O: nueva app para los reporte de las transacciones y ganancias y que ulitices los datos de #file:transacciones y #file:transacciones con los siguientes campos:
- fecha
- tipo_transaccion (compra o venta)
- moneda
- monto_origen
- monto_destino
- comision_compra
- comision_venta
- comision_comp_origen
- comision_vta_destino
- porcentaje_descuento (PORDES)

Necesito que generes el cálculo de la ganancia por transacción usando EXCLUSIVAMENTE las siguientes fórmulas:

Ganancia de casa de cambio en venta de moneda extranjera:
GANANCIA_VTA = DESTINO x (COMISION_VTA_DESTINO - (COMISION_VTA_DESTINO x PORDES / 100))

Ganancia de casa de cambio en compra de moneda extranjera:
GANANCIA_COMP = ORIGEN x (COMISION_COMP_ORIGEN - (COMISION_COMP_ORIGEN x PORDES / 100))

Ganancia Total:
GANANCIA_TOTAL = GANANCIA_COMP + GANANCIA_VTA

Instrucciones:
- No inventes nuevas fórmulas.
- No modifiques los cálculos.
- No agregues campos que no estén mencionados.
- Solo genera el cálculo de ganancia para cada transacción y un total general.
- Si un campo no aplica (ej: en compra no hay ganancia de venta), colocar 0. el rol que puede ver esto es el administrador del sistema no usamos l admin por defecto de django ten en cuenta la #file:base.html y #file:static para el diseño de los templates

GitHub Copilot: Crearé una nueva app 'reportes' dentro de tauser con vistas, URLs y plantilla. También añadiré 'reportes' a INSTALLED_APPS en tauser/settings.py y registraré las URLs en tauser/urls.py.

Archivos a crear/modificar:
1. /home/claudia/Escritorio/ProyectoIS2/proyectoIS/tauser/reportes/views.py — vista para calcular ganancias por transacción y total.
2. /home/claudia/Escritorio/ProyectoIS2/proyectoIS/tauser/reportes/urls.py — rutas de la app.
3. /home/claudia/Escritorio/ProyectoIS2/proyectoIS/tauser/reportes/__init__.py — archivo vacío.
4. /home/claudia/Escritorio/ProyectoIS2/proyectoIS/tauser/reportes/templates/reportes/reportes_transacciones.html — plantilla basada en proyecto/templates/base.html.
5. Editar settings.py — añadir 'reportes' a INSTALLED_APPS.
6. Editar urls.py — incluir rutas de reportes.

Ahora aplico los cambios. 
````

````


Se realizaron cambios.


````

````
