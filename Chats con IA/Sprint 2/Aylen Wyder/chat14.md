### ahora quiero que el simbolo de la moneda aparezca a la iquierda del nombre de la moneda, con el estilo que tiene en #file:cotizacion_lista.html y en #file:moneda_lista.html 

Voy a actualizar la plantilla de inicio para mostrar el símbolo de la moneda con el mismo estilo. Primero veo que en las otras plantillas el símbolo tiene una clase especial `moneda-simbolo`. Voy a hacer los cambios: 
```


Se realizaron cambios.


```

```


Se realizaron cambios.


```
He realizado los siguientes cambios:

1. En inicio.html:
   - Moví el símbolo de la moneda al inicio de la celda
   - Lo envolví en un `<span>` con la clase `moneda-simbolo`
   - Eliminé los paréntesis alrededor del símbolo

2. En inicio.css:
   - Agregué los estilos para la clase `moneda-simbolo` que son similares a los usados en las otras vistas:
     - Fondo azul (#667eea)
     - Texto blanco
     - Bordes redondeados
     - Padding para que se vea como una etiqueta
     - Margen a la derecha para separarlo del nombre

Ahora el símbolo de la moneda aparecerá como una etiqueta azul a la izquierda del nombre de la moneda, consistente con el estilo usado en las otras vistas. ¿Necesitas algún ajuste adicional?

### #file:inicio.html como hago para que este centrado el texto de funcionalidades:         <div class="funcionalidades">
            <div class="funcionalidad">
                <div class="icono-funcionalidad">✓</div>
                <span>Gestión segura de transacciones</span>
            </div>
            <div class="funcionalidad">
                <div class="icono-funcionalidad">📊</div>
                <span>Reportes y estadísticas detalladas</span>
            </div>
            <div class="funcionalidad">
                <div class="icono-funcionalidad">🔒</div>
                <span>Seguridad y privacidad garantizada</span>
            </div>
            <div class="funcionalidad">
                <div class="icono-funcionalidad">⚡</div>
                <span>Proceso rápido y confiable</span>
            </div>
        </div>


Voy a modificar los estilos CSS para centrar el contenido de las funcionalidades. Voy a actualizar la clase `.funcionalidades` y `.funcionalidad`: 
```


Se realizaron cambios.


```
He realizado los siguientes cambios:

1. En la clase `.funcionalidades`:
   - Eliminé `text-align: left`
   - Agregué `display: flex` y `flex-direction: column`
   - Agregué `align-items: center` para centrar los elementos horizontalmente

2. En la clase `.funcionalidad`:
   - Agregué `justify-content: center` para centrar el contenido horizontalmente
   - Agregué `width: 100%` y `max-width: 400px` para controlar el ancho y mantener una buena legibilidad

Ahora las funcionalidades deberían aparecer centradas en la página. Los íconos y el texto estarán alineados en el centro de cada línea. ¿Quieres que haga algún ajuste adicional?