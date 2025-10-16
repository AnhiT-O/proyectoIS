AnhiT-O: quiero que despues de dar a confirmar ya sea la compra o la venta se rediriga a la pasarela de pago si el medio de pago fue transferencia o alguna billetera que te comente antes y que despues de que se haya confirmado el medio de pago vuelva a la ventana donde quedo para seguir con la adquisición en el medio de cobro

GitHub Copilot: Voy a modificar el archivo confirmacion.html para agregar la redirección a la pasarela de pago después de confirmar:

1. Primero agregaré el script de pasarela: 
````

````


Se realizaron cambios.

2. Modificar el formulario de confirmación para incluir la redirección: 
```


Se realizaron cambios.


```
Estos cambios permiten que:
1. Al confirmar la operación, si el medio de pago es billetera o transferencia, redirija a la pasarela
2. La pasarela recibe todos los datos necesarios de la transacción
3. Cuando regresa de la pasarela, continúa con el flujo normal
4. Si el pago se completó exitosamente, envía el formulario automáticamente para continuar
5. Si el pago no se completó o fue cancelado, permite intentar nuevamente
