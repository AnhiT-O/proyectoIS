AnhiT-O: no me aparece la notificación en pantalla

GitHub Copilot: Para hacer que la notificación aparezca en pantalla, necesitamos hacer varios cambios:

1. Primero, necesitamos agregar un campo para almacenar los valores iniciales de la cotización en la vista de compra/venta: 
````

````


Se realizaron cambios.

2. Agregar el JavaScript para verificar cambios en la plantilla de confirmación: 
````

````


Se realizaron cambios.

3. Actualizar la vista de verificación para devolver la respuesta JSON: 
````

````


Se realizaron cambios.

Estos cambios implementan:
1. Almacenamiento de valores iniciales de cotización
2. Verificación periódica cada 3 segundos
3. Redirección automática al modal cuando hay cambios
4. Manejo adecuado de la respuesta JSON

AnhiT-O: cual es lo que usas para mostrar la notificación en pantalla #file:cotizacion_cambiada.html o #file:cambio_cotizacion.html ?

GitHub Copilot: Estamos usando cotizacion_cambiada.html que es el template más completo que muestra:
- Los precios de compra y venta (anteriores y actuales)
- Las diferencias en los precios
- El temporizador de 30 segundos
- Los botones de aceptar/cancelar

Podemos eliminar cambio_cotizacion.html ya que es redundante y estamos usando cotizacion_cambiada.html como la plantilla principal para mostrar la notificación de cambios en la cotización.

¿Quieres que realice alguna mejora específica en la plantilla cotizacion_cambiada.html para asegurar que se muestre correctamente?

AnhiT-O: elimina lo redundante

GitHub Copilot: Voy a eliminar el archivo redundante `cambio_cotizacion.html` ya que estamos usando cotizacion_cambiada.html como la plantilla principal para las notificaciones. Esto ayudará a mantener el código más limpio y evitar confusiones. Lo siento, parece que no tengo acceso directo al sistema de archivos. En este caso, necesitarás eliminar manualmente el archivo:

```
/home/claudia/Escritorio/ProyectoIS2/proyectoIS/proyecto/transacciones/templates/transacciones/cambio_cotizacion.html
```

Mantendremos cotizacion_cambiada.html como la única plantilla para mostrar las notificaciones de cambios en la cotización.
