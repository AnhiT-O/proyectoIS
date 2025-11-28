irismendoza03: quiero que si no se encuentran transacciones con los filtros aplicados tampoco se muestre resumen de ganancias por monedas.
#file:transacciones_reportes.html 

GitHub Copilot: Voy a modificar el archivo para que el resumen de ganancias por monedas solo se muestre cuando hay transacciones encontradas. 

Usando "Reemplazar cadena en archivo"


```

```
Perfecto! He modificado el archivo para que el resumen de ganancias por monedas solo se muestre cuando hay transacciones encontradas. 

Los cambios realizados:

1. **Cambié la estructura condicional**: Ahora uso `{% if not filas %}...{% else %}...{% endif %}` en lugar de tener dos bloques separados.

2. **Condición para mostrar el resumen**: El "Resumen de Ganancias por Moneda" ahora está dentro del bloque `{% else %}`, lo que significa que solo se mostrará cuando `filas` no esté vacío (es decir, cuando haya transacciones encontradas).

3. **Mensaje cuando no hay transacciones**: El mensaje "No se encontraron transacciones con los filtros aplicados" se mantiene igual y se muestra cuando no hay resultados.

Ahora, cuando no se encuentren transacciones con los filtros aplicados, solo se mostrará el mensaje indicando que no hay resultados, sin mostrar el resumen de ganancias por monedas.

Se realizaron cambios.