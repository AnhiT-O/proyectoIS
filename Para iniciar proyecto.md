## Software necesario para instalar y usar en el proyecto
- [Visual Studio Code](https://code.visualstudio.com/)
- [Git](https://git-scm.com/downloads/linux)
- PostgreSQL:
```bash
sudo apt update
sudo apt upgrade
sudo apt install postgresql postgresql-contrib
```
- Nginx:
```bash
sudo apt update
sudo apt upgrade
sudo apt install nginx
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
- Se debe crear una contraseña para el usuario postgres creado al instalar PostgreSQL:
```bash
sudo -i -u postgres
psql -U postgres
ALTER USER postgres WITH PASSWORD 'contraseña'; #acá poner la contraseña
\q
exit
```
- Crear una base de datos para cada entorno:
```bash
sudo -u postgres createdb bd_desarrollo
sudo -u postgres createdb bd_produccion
```
- En Visual Studio Code, en la sección Database se debe conectar al servidor de base de datos, el host es `localhost`, username `postgres` con su contraseña. Finalmente darle Connect

## Crear entorno virtual e instalar dependencias en cada entorno
- Crear dos entornos virtuales dentro del directorio del proyecto(proyectoIS/proyecto): 
```bash
python3 -m venv dvenv #entorno de desarrollo
python3 -m venv pvenv #entorno de producción
```
- Activar el entorno virtual a utilizar, **esto se deberá hacer cada vez que se ejecutará comandos del proyecto desde ese entorno**:
```bash
source dvenv/bin/activate #activar este para usar entorno de desarrollo
source pvenv/bin/activate #activar este para usar entorno de producción
```
- Con el entorno virtual de producción activado, instalar estas dependencias:
```bash
pip install django #framework del proyecto
pip install psycopg2-binary #conexión con PostgreSQL
pip install python-dotenv #variables de entorno
pip install gunicorn #para despliegue de la página
#a medida que el proyecto avance se tendrán que instalar más dependencias
```

- Con el entorno virtual de desarrollo activado, instalar estas dependencias:
```bash
pip install django #framework del proyecto
pip install psycopg2-binary #conexión con PostgreSQL
pip install python-dotenv #variables de entorno
pip install pytest #para pruebas unitarias
pip install pytest-django #integración de pruebas con django
pip install sphinx #para documentación automática de código
#a medida que el proyecto avance se tendrán que instalar más dependencias
```

- Para desactivar el entorno virtual simplemente se ejecuta el comando `deactivate`

## Habilitar dirección de correo electrónico para usarlo como confirmador de registros 
- Para verificar que la confirmación de registros de usuario por correo funcione, se debe establecer tu propio correo como el remitente, estos serían los pasos para hacerlo desde Gmail:
- Activar verificación en dos pasos en tu correo
- En la sección Contraseña de aplicaciones crear uno llamado "Django App"
- La contraseña generada se debe copiar y pegar en una variable de entorno

## Crear variables de entorno
- Crea un archivo `.env` en el directorio `proyectoIS/proyecto`
- Dentro del archivo debe estar:
```bash
DB_PASSWORD=password #la contraseña de tu usuario postgres
EMAIL_HOST_USER=correo #el correo a usar para envío de confirmación
EMAIL_HOST_PASSWORD=contraseña_generada #la contraseña generada desde tu gmail
#a medida que el proyecto avance se tendrán que añadir más variables de entorno
```

## Git Flow
- En VSC crear rama desde 'desarrollo' con el nombre `feature/SCRUM#` reemplazando '#' por el número de historia de usuario a codificar, y publicarlo
- Desde la nueva rama codificar, commitear y hacer todo lo necesario para la funcionalidad que se esté creando
- Al culminar la funcionalidad, subir (sincronizar) la rama a GitHub
- Desde GitHub en la pestaña Pull Request crear el pull request (solicitud de unión), describiendo todo lo que se hizo lo más detallado posible
- Al estar seguros que todo funciona, realizaremos el merge (mezcla de ramas) desde la rama feature a la rama desarrollo

## Ejecutar proyecto en desarrollo
- Luego de escribir el código:
```bash
python manage.py makemigrations #si hiciste algún cambio en models, este comando preparará la exportación de cambios a la base de datos
python manage.py migrate #exportará los cambios preparados a la base de datos
python manage.py runserver #correrá el proyecto
```
- Se podrá ver los resultados del proyecto en: http://localhost:8000/
 