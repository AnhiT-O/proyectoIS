### quiero que en #file:cotizacion_form.html  aprezca al opcion de editar moneda cuando selecciona una moneda, como aparece en #file:moneda_lista.html 

Vamos a modificar el formulario de cotización para agregar un botón de editar moneda que aparezca cuando se selecciona una moneda. Primero necesitamos hacer algunos cambios en el formulario y agregar JavaScript para manejar el comportamiento dinámico. 
```


Se realizaron cambios.


```
También necesitamos agregar algunos estilos específicos para el botón de editar: 
```


Se realizaron cambios.


```
He realizado los siguientes cambios:

1. Modifiqué el contenedor del campo de moneda para incluir un layout flexible que permite mostrar el botón de editar al lado del selector.

2. Agregué el botón de editar que:
   - Solo aparece cuando hay una moneda seleccionada
   - Solo es visible para usuarios con los permisos necesarios
   - Tiene el mismo estilo que en la lista de monedas
   - Se actualiza dinámicamente cuando se cambia la selección

3. Agregué JavaScript para:
   - Detectar cambios en la selección de moneda
   - Mostrar/ocultar el botón de editar según corresponda
   - Actualizar el enlace del botón con el ID de la moneda seleccionada
   - Manejar el estado inicial si hay una moneda preseleccionada

4. Agregué estilos CSS para:
   - El botón de editar con el mismo aspecto visual que en la lista de monedas
   - El layout flexible del contenedor
   - Efectos hover y transiciones suaves

Ahora, cuando selecciones una moneda en el formulario de cotización:
1. Aparecerá el botón "Editar" a la derecha del selector
2. Al hacer clic en "Editar" te llevará a la página de edición de esa moneda específica
3. El botón solo será visible si tienes los permisos necesarios
4. El diseño mantiene la consistencia visual con la lista de monedas

¿Necesitas que ajuste algo más en la implementación?

