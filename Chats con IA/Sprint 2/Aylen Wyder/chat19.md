 ### en #file:inicio.html al darle click en el boton de simular conversiones me tiene que dirgir a #file:simulador.html 

 Voy a modificar el template del simulador para que use los estilos de los archivos CSS globales: 
```


Se realizaron cambios.


```
También necesito actualizar el script JavaScript para que maneje las nuevas clases de botones: 
```


Se realizaron cambios.


```
He realizado los siguientes cambios:

1. **Estructura del Formulario**:
   - Usé las clases `.cuerpo` y `.contenido` de formularios.css para el contenedor principal
   - Implementé `.form-cabecera` con logo y subtítulo
   - Cambié `form-group` por `form-campo` para seguir el estilo global
   - Agregué la clase `form-control` para los inputs y selects

2. **Botones**:
   - Cambié las clases de los botones para usar los estilos globales:
     - `btn-primario` y `btn-secundario` para los botones de Compra/Venta
     - `btn-enviar` para el botón "Convertir"
     - `btn-atras` para el botón "Volver"
   - Implementé la `zona-botones` para el contenedor de botones

3. **Efectos Visuales**:
   - Los botones de operación ahora alternan entre estilos primario y secundario
   - El botón activo usa el estilo secundario para destacarse
   - Mantuve la funcionalidad de cambio de operación pero con los nuevos estilos

4. **Navegación**:
   - Cambié el botón "Volver" por un enlace que regresa a la página de inicio
   - Usé la URL nombrada para mantener la consistencia

Los estilos ahora coinciden con el resto de la aplicación y siguen el diseño establecido en `formularios.css` y `global.css`. ¿Necesitas que ajuste algo más del diseño?

### hay un error en la parte de los botones de compra y venta porque para seleccionar Compra debo seleccionar Venta y esta mal eso, cambia 

Entiendo, hay una confusión en la lógica de los botones. Voy a corregir el JavaScript para que funcione correctamente: 
```


Se realizaron cambios.


```
También voy a modificar el estado inicial de los botones en el HTML: 
```


Se realizaron cambios.


```
He realizado los siguientes cambios:

1. En el JavaScript:
   - Reescribí la función `toggleOperacion` para que maneje los estilos de forma más directa
   - Ahora cuando se selecciona un botón:
     - El botón seleccionado cambia a estilo secundario y se marca como activo
     - El otro botón cambia a estilo primario y se le quita la marca activo

2. En el HTML:
   - Ajusté las clases iniciales de los botones:
     - El botón "Compra" comienza como secundario y activo (seleccionado por defecto)
     - El botón "Venta" comienza como primario (no seleccionado)

Ahora cuando:
- Seleccionas "Compra": el botón se muestra como secundario (seleccionado) y "Venta" como primario
- Seleccionas "Venta": el botón se muestra como secundario (seleccionado) y "Compra" como primario

La funcionalidad debería estar correcta ahora, con los botones mostrando claramente cuál está seleccionado. ¿Podrías probar si ahora funciona como se espera?