## Software necesario para instalar y usar en el proyecto
- [Visual Studio Code](https://code.visualstudio.com/)
- [Git](https://git-scm.com/downloads/linux)
- PostgreSQL:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

- Python y su instalador de paquetes (pip) ya vienen instalado con el Ubuntu, pero siempre es importante mantener actualizado todo:
```bash
sudo apt update
sudo apt upgrade
```
## Configurar Visual Studio Code
- Iniciar sesión en tu cuenta de GitHub
- Enlazar cuenta de GitHub en Visual Studio Code para usar GitHub Copilot
- Instalar las extensiones necesarias para el proyecto:
  - Spanish Language Pack for Visual Studio Code
  - Python
  - PostgreSQL
  - Otras que creas necesarias

## Configurar y enlazar Git con VSC
- En Control de Código Fuente click en Clonar Repositorio
- Usar enlace para clonarlo: https://github.com/AnhiT-O/proyectoIS.git
- Abrir terminal desde VSC y añadir email y nombre de usuario de Git:
```bash
git config --global user.email "tu email entre comillas"
git config --global user.name "tu nombre de usuario entre comillas"
```

## Configurar y enlazar PostgreSQL con VSC
- Al instalar postgreSQL se crea un cluster (instancia) en el puerto 5432 que se puede usar para entorno de producción, se debe crear otro cluster en el puerto 5433 para entorno de desarrollo:
```bash
sudo pg_createcluster 17 desarrollo --datadir=/var/lib/postgresql/17/dev --port=5433
sudo pg_ctlcluster 17 desarrollo start
pg_lsclusters #ver si ambos clústeres corren
```
- Se debe crear una contraseña para el usuario postgres creado al instalar PostgreSQL en ambos clusteres:
```bash
sudo -i -u postgres
psql -U postgres -p 5432
ALTER USER postgres WITH PASSWORD 'contraseña' #acá poner la contraseña
\q
psql -U postgres -p 5433
ALTER USER postgres WITH PASSWORD 'contraseña' #acá poner la contraseña
\q
exit
```
- Crear una base de datos para cada cluster:
```bash
sudo -u postgres createdb -p 5432 bd_casacambios
sudo -u postgres createdb -p 5433 bd_casacambios
```
- En Visual Studio Code, en la sección Database se debe conectar a los dos clústeres, uno con nombre 'desarrollo' y otro 'producción'. En ambos servidores el host es `localhost`, username `postgres` con sus respectivas contraseñas, database `bd_casacambios` y los puertos que corresponden a cada cluster. Finalmente darle Connect

## Crear entorno virtual e instalar dependencias
- Dentro del directorio del proyecto (proyectoIS/proyecto) crear el entorno virtual: 
```bash
python3 -m venv venv
```
- Activar el entorno virtual, **esto se deberá hacer cada vez que se trabajará en el proyecto**:
```bash
source venv/bin/activate
```
- Instalar las dependencias que usará el proyecto:
```bash
pip install django #framework del proyecto
pip install psycopg2-binary #conexión con PostgreSQL
pip install python-dotenv #variables de entorno
pip install pytest #para pruebas unitarias
pip install pytest-django #integración de pruebas con django
pip install sphinx #para documentación automática de código
#a medida que el proyecto avance se tendrán que instalar más dependencias
```

## Crear variables de entorno
- Crea un archivo `.env` en el directorio `proyectoIS/proyecto`
- Dentro del archivo debe estar:
```bash
DEBUG=True #True si se ejecuta en entorno de desarrollo, False si es en entorno de producción
DB_PASSWORD=password #la contraseña de tu usuario postgres
#a medida que el proyecto avance se tendrán que añadir más variables de entorno
```

## Git Flow
- En VSC crear rama desde 'desarrollo' con el nombre `feature/SCRUM#` reemplazando '#' por el número de historia de usuario a codificar, y publicarlo
- Desde la nueva rama codificar, commitear y hacer todo lo necesario para la funcionalidad que se esté creando
- Al culminar la funcionalidad, subir (sincronizar) la rama a GitHub
- Desde GitHub en la pestaña Pull Request crear el pull request (solicitud de unión), describiendo todo lo que se hizo lo más detallado posible
- Al estar seguros que todo funciona, realizaremos el merge (mezcla de ramas) desde la rama feature a la rama desarrollo

## Ejecutar proyecto
- Luego de escribir el código:
```bash
python manage.py makemigrations #si hiciste algún cambio en models, este comando preparará la exportación de cambios a la base de datos
python manage.py migrate #exportará los cambios preparados a la base de datos
python manage.py runserver #correrá el proyecto
```
- Se podrá ver los resultados del proyecto en: http://localhost:8000/
