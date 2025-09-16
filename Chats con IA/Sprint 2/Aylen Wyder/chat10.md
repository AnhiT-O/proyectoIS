### podrias aplicar el patron de estilo css que esta en #file:static a #file:cotizacion_lista.html y a #file:cotizacion_form.html  sin hacer otros cambios que no tengan que ver solo con el estilo
Veo dos problemas en tus templates relacionados con los estilos:

1. En cotizacion_lista.html, ya estás usando el estilo correcto:
```html
{% block extra_css %}
<link rel="stylesheet" href="{% static 'gestion.css' %}">
{% endblock %}
```
Esto está bien porque estás usando `gestion.css` que es el archivo de estilo para las listas y tablas.

2. En `cotizacion_form.html`, necesitas cambiar el estilo para usar `formularios.css` que es el patrón de estilo para formularios en tu sistema:
```html
{% block extra_css %}
<link rel="stylesheet" href="{% static 'formularios.css' %}">
{% endblock %}
```

Los archivos CSS que mencionas (`gestion.css` y `formularios.css`) ya están siendo usados correctamente en tus templates. No se necesitan cambios adicionales porque:

- `gestion.css` proporciona los estilos para:
  - Tablas
  - Listados
  - Encabezados
  - Mensajes
  - Botones de acción

- `formularios.css` proporciona los estilos para:
  - Campos de formulario
  - Etiquetas
  - Botones de envío
  - Mensajes de error

Si los estilos no se están aplicando correctamente, el problema podría ser:
1. Los archivos CSS no están en la carpeta `static`
2. El servidor de desarrollo no está sirviendo los archivos estáticos
3. La caché del navegador necesita ser limpiada

¿Quieres que verifique alguna de estas posibilidades?