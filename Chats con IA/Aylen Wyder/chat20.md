### para que es el comando git fetch
El comando `git fetch` se utiliza para descargar el contenido del repositorio remoto sin realizar cambios automáticos en tu directorio de trabajo local. Es útil por las siguientes razones:

### Principales funciones:

1. **Actualiza referencias remotas**
- Descarga todas las ramas y etiquetas del repositorio remoto
- Actualiza el estado de las ramas remotas (origin/*)

2. **Seguridad**
- No modifica automáticamente tus archivos locales
- Te permite revisar los cambios antes de integrarlos
- Evita conflictos inesperados

### Diferencia con `git pull`:

- `git fetch`: Solo descarga los cambios
- `git pull`: Equivale a hacer `git fetch` + `git merge`

### Ejemplo de uso básico:

````bash
# Obtener cambios del remoto
git fetch origin

# Ver diferencias con la rama remota
git diff origin/main
````

Es una práctica recomendada usar `fetch` antes de hacer `pull` para revisar los cambios que se van a integrar.