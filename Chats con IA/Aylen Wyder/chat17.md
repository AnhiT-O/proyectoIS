### hace que sea mas grande el contenedor de #file:cotizacion_form.html  y tambien que cuando le de en editar y si ya estando en esa pestania al darle en cancelar me lleve otra vez a #file:cotizacion_form.html 

Voy a hacer dos cambios: aumentar el tamaño del contenedor en el formulario de cotización y modificar el botón cancelar en el formulario de edición de moneda para que regrese al formulario de cotización.

Primero, voy a modificar los estilos del contenedor en `cotizacion_form.html`: 
```


Se realizaron cambios.


```
Ahora, necesito acceder al formulario de edición de monedas para modificar el botón cancelar: Voy a modificar el formulario de edición de monedas para que el botón cancelar tenga un comportamiento diferente cuando viene desde el formulario de cotización: 
```


Se realizaron cambios.


```
Ahora voy a modificar el formulario de cotización para incluir el parámetro en la URL cuando se redirecciona a editar: 
```


Se realizaron cambios.


```
Finalmente, voy a modificar el botón cancelar en el formulario de moneda: 
```


Se realizaron cambios.


```
He realizado los siguientes cambios:

1. En el formulario de cotización (`cotizacion_form.html`):
   - Aumenté el tamaño del contenedor principal (max-width: 1000px)
   - Aumenté el padding y los márgenes
   - Mejoré las sombras y el aspecto visual
   - Centré mejor los elementos
   - Añadí más espacio entre los elementos
   - Aumenté el tamaño del título
   - Agregué el parámetro `from=cotizacion` a la URL de edición

2. En el formulario de edición de moneda (moneda_form.html):
   - Agregué detección del origen de la navegación (desde el formulario de cotización)
   - Modifiqué el comportamiento del botón cancelar para que:
     * Si viene desde el formulario de cotización, regrese a él
     * Si viene desde otro lugar, regrese a la lista de monedas

Ahora:
1. El formulario de cotización tiene un aspecto más amplio y espacioso
2. Al hacer clic en "Editar" en el formulario de cotización, se abre el formulario de edición de moneda
3. Al hacer clic en "Cancelar" en el formulario de edición de moneda, te devuelve al formulario de cotización si viniste desde allí

¿Necesitas algún ajuste adicional en el diseño o la funcionalidad?