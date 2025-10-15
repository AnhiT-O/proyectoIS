como se ejecuta #file:reestablecer_bd.sh 

Para ejecutar el script reestablecer_bd.sh, necesitas seguir estos pasos:

## 1. Hacer el script ejecutable

```bash
chmod +x reestablecer_bd.sh
```

## 2. Ejecutar el script

El script acepta 1 o 2 parámetros:

### Opción A: Solo resetear la BD (sin importar datos)
```bash
./reestablecer_bd.sh nombre_de_tu_base_de_datos
```

### Opción B: Resetear la BD e importar datos desde SQL
```bash
./reestablecer_bd.sh nombre_de_tu_base_de_datos backup_datos.sql
```

## Ejemplo práctico

Si tu base de datos se llama `proyectois` y quieres importar el backup:

```bash
# Hacer ejecutable (solo la primera vez)
chmod +x reestablecer_bd.sh

# Ejecutar con importación de datos
./reestablecer_bd.sh proyectois backup_datos.sql
```

## Qué hace el script paso a paso:

1. **Termina conexiones activas** a la BD
2. **Elimina la base de datos** existente
3. **Crea una nueva base de datos** vacía
4. **Elimina archivos de migraciones** de todas las apps Django
5. **Ejecuta migraciones** de Django (`makemigrations` y `migrate`)
6. **Importa datos** desde el archivo SQL (si se proporciona)

## Notas importantes:

- Ejecuta el script desde el directorio proyectoIS
- Asegúrate de que tu entorno virtual esté activado antes de ejecutar
- El script usa `sudo` para operaciones de PostgreSQL, así que te pedirá la contraseña

¿Cuál es el nombre exacto de tu base de datos para que puedas ejecutarlo correctamente?