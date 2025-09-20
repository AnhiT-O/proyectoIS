### .tarjeta-moneda {
    background: #fff;
    border-radius: 18px;
    padding: 1.5rem 1.2rem;
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.13);
    transition: all 0.3s ease;
    border: 1.5px solid #e9ecef;
    position: relative;
    margin-bottom: 2rem;
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
    min-height: unset;
    width: 100%;

El estilo de los contenedores de cada moneda está definido por la clase `.tarjeta-moneda` en tu archivo  
gestion.css.

Si quieres **hacer más grande el tamaño de los contenedores**, puedes modificar las siguientes propiedades:

- `padding`: aumenta el espacio interno.
- `width`: puedes poner un valor mayor o usar `max-width`.
- `min-height`: puedes establecer una altura mínima.

Por ejemplo, para hacerlos más grandes:

````css
.tarjeta-moneda {
    background: #fff;
    border-radius: 18px;
    padding: 2.5rem 2rem;      /* Aumenta el padding */
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.13);
    transition: all 0.3s ease;
    border: 1.5px solid #e9ecef;
    position: relative;
    margin-bottom: 2rem;
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
    min-height: 220px;         /* Establece una altura mínima */
    width: 100%;
    max-width: 600px;          /* Opcional: limita el ancho máximo */
}
````

Puedes ajustar los valores según lo que necesites.  
Guarda los cambios y recarga la página para ver el nuevo tamaño.

### y esta parte como tengo que hacer para que la celda de stock sea mas grande:                             <th style="width: 30%;">Estado</th>
                            <th style="width: 30%;">Decimales a mostrar</th>
                            <th style="width: 30%;">Tasa base</th>
                            <th style="width: 30%;">Comisión de compra</th>
                            <th style="width: 30%;">Comisión de venta</th>
                            <th style="width: 30%;">Stock</th>

Para que la celda de **Stock** sea más grande, solo necesitas aumentar el valor del atributo `width` en el `<th>` correspondiente y reducir el de las otras columnas para que sumen 100% o menos.

Por ejemplo, podrías dejar la columna Stock con un 40% y repartir el resto entre las otras columnas:

````html
<th style="width: 12%;">Estado</th>
<th style="width: 12%;">Decimales a mostrar</th>
<th style="width: 12%;">Tasa base</th>
<th style="width: 12%;">Comisión de compra</th>
<th style="width: 12%;">Comisión de venta</th>
<th style="width: 40%;">Stock</th>
````

Esto hará que la columna Stock sea más ancha y el número se vea mejor.  
Puedes ajustar los porcentajes según lo que necesites visualmente.

