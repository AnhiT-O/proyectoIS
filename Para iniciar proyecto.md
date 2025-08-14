## Software necesario para instalar y usar en el proyecto
- [Visual Studio Code](https://code.visualstudio.com/)
- [pgAdmin](https://www.pgadmin.org/)
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

## Configurar PostgreSQL y pgAdmin 4
- Primero se debe crear una contraseña para el usuario postgres creado al instalar PostgreSQL:
```bash
sudo -i -u postgres
psql
ALTER USER postgres WITH PASSWORD 'contraseña' #acá poner la contraseña
\q
exit
```
- Configurar sistema para que pueda ejecutar comandos de postgreSQL:
```bash
echo 'export PATH=$PATH:/usr/lib/postgresql/17/bin' >> ~/.bashrc
source ~/.bashrc
```
- Abrir pgAdmin y en Archivo seleccionar Preferencias
- En Miscelaneous y User preferences seleccionar language Spanish
- En Rutas y Rutas a ejecutables colocar en Binary Path de PostgreSQL 17: `/run/user/1000/doc/6905aebe/bin` y marcar Set as default
- Crear dos servidores, uno de desarrollo y otro de producción, en Conexión se debe poner como nombre `localhost` y en contraseña la que creaste para el usuario postgres
- Importar la base de datos del proyecto ubicado en proyectoIS/Base de Datos

## Crear entorno virtual e instalar dependencias
- Dentro del directorio del proyecto (proyectoIS/proyecto) crear el entorno virtual: 
```bash
python3 -m venv venv
```
- Activar el entorno virtual, **esto se deberá hacer cada vez que se trabajará en el proyecto**:
```bash
source ent/bin/activate
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
