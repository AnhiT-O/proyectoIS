losrivarola98: POrqué no me lee mi archivo #file:global.js ?

GitHub Copilot: El problema está en la línea donde incluyes el archivo `global.js` en tu plantilla `base.html`:

```html
<link rel="stylesheet" href="{% static 'global.js' %}">
```

Estás usando `<link rel="stylesheet">`, que es solo para archivos CSS. Para archivos JavaScript debes usar la etiqueta `<script>`:

```html
<script src="{% static 'global.js' %}"></script>
```

Cambia esa línea y tu archivo JS se cargará correctamente. ¿Quieres que lo corrija automáticamente en tu archivo?