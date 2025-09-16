losrivarola98: @terminal /explain #terminalSelection

Terminal: El error cp: no se puede efectuar `stat' sobre './backup_datos.sql': No existe el archivo o el directorio ocurre porque el script intenta copiar el archivo SQL usando una ruta relativa, pero el archivo sí existe en el directorio actual según el resultado de ls.

El problema está en esta línea del script:

```bash
sudo cp $SQL_FILE /var/lib/postgresql/$SQL_FILE
```

Si ejecutas el script desde otro directorio (por ejemplo, dentro de ./proyecto tras el cd), la ruta relativa ./backup_datos.sql ya no apunta al archivo correcto.

**Solución recomendada:** Usa la ruta absoluta para el archivo SQL. Modifica la línea así:

```bash
sudo cp "$(dirname "$0")/$SQL_FILE" /var/lib/postgresql/$SQL_FILE
```

Esto asegura que el archivo se copie desde el directorio donde está el script, sin importar el directorio actual.

**Alternativamente**, puedes guardar la ruta absoluta antes de cambiar de directorio:

```bash
SQL_FILE_PATH="$(pwd)/$SQL_FILE"
...
cd ./proyecto
...
sudo cp "$SQL_FILE_PATH" /var/lib/postgresql/
sudo -i -u postgres psql -d $DB_NAME -f "/var/lib/postgresql/$SQL_FILE"
```

Así evitas el error de ruta.Así evitas el error de ruta.