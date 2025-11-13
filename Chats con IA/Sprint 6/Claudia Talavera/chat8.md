AnhiT-O:Acuerdate solo se calculan las ganacias de las transacciones con estado completada si no es ese estado la ganancia ya sea de venta o compra es 0 

GitHub Copilot: Voy a hacer dos cambios en la vista: obtener el estado antes de calcular las ganancias y forzar ganancia_comp/ganancia_vta a 0 si el estado no es 'Completa' (comparación insensible a mayúsculas). Aplico la edición.

## views.py+10-2
He aplicado exactamente la regla que pediste: las ganancias por compra o venta solo se calculan si estado == 'Completa' (comparación insensible a mayúsculas). Si no, ganancia_comp y ganancia_vta se establecen en 0 antes de acumular el resumen por moneda.

Prueba con transacciones en distintos estados y confirma los resultados.

Restaurar punto de control
por que agregas decimales de mas por ejemplo se vendión 2 dolares y pusiste numero de mas 2000,0