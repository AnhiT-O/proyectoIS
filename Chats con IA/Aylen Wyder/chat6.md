### crear una tabla cotizacion en la app de cotizacion con los siguintes atributos: id (int) PK, id_moneda FK de la tabla moneda, precio_venta (numeric), precio_compra (numeric), fecha_cotizacion

Voy a crear el modelo `Cotizacion` en el archivo models.py de la aplicación `cotizacion`. Voy a usar una relación con el modelo `Moneda` y configurar los campos según lo solicitado: Lo siento, parece que el archivo ya existe. Voy a usar la herramienta de reemplazo: 
```


Se realizaron cambios.


```
Ahora voy a crear la migración para este nuevo modelo: Ahora voy a aplicar la migración: ¡Listo! He creado la tabla `cotizaciones` con las siguientes características:

1. **Campos**:
   - `id`: Campo AutoField (PK) creado automáticamente por Django
   - `id_moneda`: ForeignKey a la tabla `monedas`
   - `precio_venta`: DecimalField(12,2) para valores monetarios
   - `precio_compra`: DecimalField(12,2) para valores monetarios
   - `fecha_cotizacion`: DateTimeField que se auto-genera al crear el registro

2. **Características adicionales**:
   - Restricción `unique_together` para evitar cotizaciones duplicadas
   - Ordenamiento por fecha descendente
   - Protección contra eliminación de monedas relacionadas
   - Nombres verbosos para mejor visualización en el admin
   - Método `__str__` para mostrar el símbolo de la moneda y la fecha

La tabla está lista para ser utilizada. ¿Necesitas ayuda para agregar alguna funcionalidad adicional o para comenzar a usarla?