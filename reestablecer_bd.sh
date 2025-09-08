#!/bin/bash

# Este script automatiza el reseteo de una base de datos de PostgreSQL
# para un proyecto de Django. Incluye:
# 1. Terminación de conexiones activas.
# 2. Eliminación de la base de datos.
# 3. Creación de la base de datos.
# 4. Ejecución de las migraciones de Django.
# 5. Importación de un archivo .sql.


# --- Parámetros ---
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
	echo "Uso: $0 <DB_NAME> [SQL_FILE]"
	exit 1
fi

DB_NAME="$1"
SQL_FILE="$2"

# --- Proceso de reseteo ---

echo "Iniciando el proceso de reseteo para la base de datos: $DB_NAME"

# 1. Terminación de conexiones activas
# Nos conectamos a la base de datos 'postgres' como el usuario 'postgres'
# para asegurarnos de que el comando de terminación de conexiones funcione.
echo "1. Terminando las conexiones activas a la base de datos..."
sudo -i -u postgres psql -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$DB_NAME' AND pid <> pg_backend_pid();"

# 2. Eliminación de la base de datos
echo "2. Eliminando la base de datos..."
# Se usa 'sudo -i -u $DB_USER' para asegurar que se tengan los permisos.
sudo -i -u postgres dropdb $DB_NAME


# 3. Creación de la base de datos de nuevo
echo "3. Creando la base de datos de nuevo..."
sudo -i -u postgres createdb $DB_NAME

# Eliminación de archivos de migraciones en todas las apps
echo "Eliminando archivos de migraciones en todas las apps..."
find ./proyecto -type f -path "*/clientes/migrations/*" -name "[0-9]*.py" -exec rm {} +
find ./proyecto -type f -path "*/cotizacion/migrations/*" -name "[0-9]*.py" -exec rm {} +
find ./proyecto -type f -path "*/medios_pago/migrations/*" -name "[0-9]*.py" -exec rm {} +
find ./proyecto -type f -path "*/monedas/migrations/*" -name "[0-9]*.py" -exec rm {} +
find ./proyecto -type f -path "*/roles/migrations/*" -name "[0-9]*.py" -exec rm {} +
find ./proyecto -type f -path "*/usuarios/migrations/*" -name "[0-9]*.py" -exec rm {} +

# 4. Ejecución de las migraciones de Django
# Asume que te encuentras en el directorio raíz de tu proyecto de Django
echo "4. Ejecutando las migraciones de Django..."
cd ./proyecto
python manage.py makemigrations
python manage.py migrate
cd ..

# 5. Importación de datos desde el archivo SQL (solo si se proporciona)
if [ -n "$SQL_FILE" ]; then
	echo "5. Importando datos desde el archivo '$SQL_FILE'..."
	sudo cp $SQL_FILE /var/lib/postgresql/$SQL_FILE
	sudo -i -u postgres psql -d $DB_NAME -f "$SQL_FILE"
	echo "La base de datos ahora está limpia, con las migraciones aplicadas y los datos de '$SQL_FILE' importados."
else
	echo "La base de datos ahora está limpia y con las migraciones aplicadas. No se importaron datos adicionales."
fi

echo "Proceso de reseteo completado para la base de datos '$DB_NAME'."