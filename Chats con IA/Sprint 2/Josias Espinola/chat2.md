Josias-Esp: Teniendo en cuenta el proyecto #file:proyecto necesito segmentar los clientes #file:clientes  por clientes VIP, Corporativo y Minorista, siendo Minorista el seleccionado por defecto para todos los clientes. Quiero que crees una vista en #file:templates donde solo el administrador puede ingresar y cambiar la categoria del cliente a VIP, Corportivo y Minorista, debes mantener la misma estetica que en los archivos html #file:templates 

GitHub Copilot: Voy a implementar la segmentación de clientes por categorías (VIP, Corporativo, Minorista) y crear una vista para que solo los administradores puedan cambiar estas categorías.

Primero, actualizaré el modelo Cliente para agregar el campo de categoría: Permíteme verificar el contenido actual del archivo models.py: 
````

````


Se realizaron cambios.

Ahora actualizaré el archivo forms.py para agregar un formulario específico para cambiar categorías: 
````

````


Se realizaron cambios.

Ahora actualizaré las vistas para agregar la funcionalidad de cambio de categoría solo para administradores: 
````

````


Se realizaron cambios.

Déjame corregir las importaciones correctas: 
```


Se realizaron cambios.


```

```


Se realizaron cambios.


```
Ahora actualizaré las URLs para agregar la nueva ruta: 
````

````


Se realizaron cambios.

Ahora crearé el template para cambiar categoría: 
````

````


Se realizaron cambios.

Ahora actualizaré la lista de clientes para mostrar las categorías y agregar el botón para cambiar categoría (solo visible para administradores): Déjame verificar el contenido actual del template de lista: 
````

````


Se realizaron cambios.

Ahora actualizaré el template de detalle del cliente para mostrar la categoría: 
````

````


Se realizaron cambios.

Ahora agregemos el botón para cambiar categoría en la vista de detalle (solo para administradores): 
````

````


Se realizaron cambios.

Finalmente, necesitamos crear las migraciones para el nuevo campo: 
````

````


Se realizaron cambios.

He implementado exitosamente la segmentación de clientes con las siguientes características:

## Cambios realizados:

1. **Modelo Cliente actualizado** - Agregué el campo `categoria` con opciones VIP, Corporativo y Minorista (por defecto)

2. **Formulario nuevo** - Creé `CambiarCategoriaForm` específico para cambiar categorías

3. **Vista administrativa** - Implementé `CambiarCategoriaView` que solo permite acceso a usuarios staff (administradores)

4. **Template nuevo** - Creé `cambiar_categoria.html` manteniendo la estética consistente con Bootstrap y FontAwesome

5. **Actualización de templates existentes**:
   - Lista de clientes: muestra categorías con badges de colores y botón para cambiar categoría (solo admin)
   - Detalle de cliente: muestra la categoría y botón para cambiarla (solo admin)

6. **Nueva URL** - Agregué la ruta para acceder a la vista de cambio de categoría

7. **Migración** - Creé la migración para agregar el nuevo campo

## Características principales:

- **Seguridad**: Solo administradores pueden cambiar categorías
- **Visual**: Badges de colores diferentes para cada categoría (VIP=amarillo, Corporativo=azul, Minorista=gris)
- **Usabilidad**: Interfaz intuitiva con información clara del cliente actual
- **Consistencia**: Mantiene la misma estética que el resto de templates

Para aplicar los cambios, ejecuta:
```bash
python manage.py makemigrations clientes
python manage.py migrate