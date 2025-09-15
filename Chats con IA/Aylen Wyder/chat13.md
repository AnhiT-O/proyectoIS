### lo que quiero que haya son 3 cotizaciones del dia, uno por cada segmento_cliente, es decir quiero que haya una cotizacion del dia donde el benficio sea 0, otro donde sea 0.05 y otro donde sea 0.10, y quiero que dependiendo de a que segmento pertenzca el cliente se le muestre una cotizacion del dia en la pantalla de inicio, por favor ya no cambies los nombres de las tablas de base de datos

Entiendo que quieres:

1. Tener 3 cotizaciones del día, una para cada segmento de cliente (con beneficios de 0, 0.05 y 0.10)
2. En la pantalla de inicio, mostrar la cotización correspondiente según el segmento del cliente

Primero, voy a revisar el modelo de Cliente para ver cómo está definido el segmento: Ahora voy a revisar la vista de inicio: Primero, voy a modificar el modelo de `Cotizacion` para agregar una referencia al segmento de cliente: Voy a agregar un campo de segmento al modelo de `Cotizacion` para indicar para qué segmento está pensada esa cotización: 
```


Se realizaron cambios.


```


### #file:inicio.css en que parte esta el contenedor 
El contenedor principal está definido en la clase `.contenido` en el archivo inicio.css. Aquí está la sección específica:

```css
.contenido {
    background: white;
    padding: 3rem;
    border-radius: 15px;
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
    text-align: center;
    max-width: 800px;
    width: 95%;
    margin: 0 auto;
}
```

Este es el contenedor principal que:
- Tiene un fondo blanco
- Tiene un padding de 3rem
- Tiene bordes redondeados (border-radius: 15px)
- Tiene una sombra suave
- Está centrado (text-align: center y margin: 0 auto)
- Tiene un ancho máximo de 800px
- Ocupa el 95% del ancho disponible cuando el espacio es menor a 800px

¿Quieres hacer algún cambio en estas propiedades del contenedor?