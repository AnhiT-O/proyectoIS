### al usuario administrador que yo cree que tiene el id 3 en la tabla de auth_group, tambien debe poder visualizar en el inicio la cotizacion, que pueda selccionar cual de los tres tipos de cptizacion quiere ver segun el segmento 

Entiendo que quieres añadir una funcionalidad para que el administrador pueda ver las cotizaciones en la página de inicio y seleccionar qué segmento quiere visualizar. Vamos a hacer los siguientes cambios:

1. Primero, veamos la vista actual de inicio: Ahora necesitamos:

1. Verificar si el usuario pertenece al grupo de administradores
2. Añadir una forma de seleccionar el segmento
3. Mostrar las cotizaciones según el segmento seleccionado

Primero, vamos a modificar la vista de inicio: 
```


Se realizaron cambios.


```
Ahora necesitamos modificar la plantilla de inicio para mostrar el selector de segmentos para los administradores: Voy a modificar la plantilla para incluir el selector de segmentos para administradores: 
```


Se realizaron cambios.


```
He realizado los siguientes cambios:

1. En la vista `inicio`:
   - Añadí la detección de administradores (grupo con id=3)
   - Agregué la carga de todas las segmentaciones disponibles
   - Implementé la lógica para mostrar precios según el segmento seleccionado
   - Mantuve la funcionalidad existente para clientes normales

2. En la plantilla inicio.html:
   - Agregué un selector de segmento que solo se muestra para administradores
   - El selector muestra todas las segmentaciones disponibles con sus porcentajes de beneficio
   - El formulario se envía automáticamente cuando se cambia la selección

Ahora, cuando un administrador acceda a la página de inicio:
1. Verá un selector desplegable con todos los segmentos disponibles
2. Podrá seleccionar cualquier segmento para ver las cotizaciones como las vería un cliente de ese segmento
3. Si no selecciona ningún segmento, verá los precios base sin beneficios aplicados

Para estilizar el selector, puedes agregar este CSS a tu archivo `inicio.css`: Lo siento por el error con el archivo CSS. Como el archivo ya existe, deberías agregar estos estilos manualmente al archivo `inicio.css` existente.

¿Necesitas que realice algún ajuste adicional o que explique alguna parte del código en más detalle?


### #file:cotizacion_form.html en esta seccion el boton desplegable tambien puede tener el mismo formato que el de los segmentos

Sí, vamos a aplicar el mismo estilo del selector de segmentos al selector de monedas en el formulario de cotización. Primero, vamos a incluir el archivo CSS de estilos del selector en el formulario: 
```


Se realizaron cambios.


```
He realizado los siguientes cambios:

1. Incluí el archivo CSS del selector de segmentos
2. Agregué estilos específicos para el formulario de cotización que:
   - Aplican el mismo formato del selector de segmentos al campo de selección de moneda
   - Mejoran el diseño del contenedor del campo (form-campo)
   - Mejoran el estilo de la etiqueta
   - Mantienen la consistencia visual con el selector de segmentos

Los cambios incluyen:
- Selector más grande y más visible
- Mismo estilo de borde y sombras
- Misma flecha desplegable personalizada
- Mismo tamaño de fuente y padding
- Mismo comportamiento en hover y focus
- Fondo gris claro para el contenedor del campo
- Etiqueta más grande y visible

¿Te gustaría que ajuste algún aspecto específico del estilo?