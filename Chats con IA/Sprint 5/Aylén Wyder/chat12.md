IntegrityError at /monedas/4/editar/
duplicate key value violates unique constraint "historial_cotizaciones_pkey"
DETAIL:  Key (id)=(12) already exists.
Request Method:	POST
Request URL:	http://127.0.0.1:8000/monedas/4/editar/
Django Version:	5.2.6
Exception Type:	IntegrityError
Exception Value:	
duplicate key value violates unique constraint "historial_cotizaciones_pkey"
DETAIL:  Key (id)=(12) already exists.
Exception Location:	/home/aylen/Documentos/IS2/proyectoIS/dvenv/lib/python3.12/site-packages/django/db/backends/utils.py, line 105, in _execute
Raised during:	monedas.views.moneda_editar
Python Executable:	/home/aylen/Documentos/IS2/proyectoIS/dvenv/bin/python
Python Version:	3.12.3
Python Path:	
['/home/aylen/Documentos/IS2/proyectoIS/proyecto',
 '/usr/lib/python312.zip',
 '/usr/lib/python3.12',
 '/usr/lib/python3.12/lib-dynload',
 '/home/aylen/Documentos/IS2/proyectoIS/dvenv/lib/python3.12/site-packages']
Server time:	Wed, 15 Oct 2025 13:53:04 -0300


¡Ah! Ahora hay un problema diferente. El error indica que hay un conflicto con la **clave primaria** (primary key) de la tabla `historial_cotizaciones`. El ID 12 ya existe y está intentando crear otro registro con el mismo ID.

Este es un problema clásico que ocurre cuando la secuencia de IDs de PostgreSQL se desincroniza. Vamos a solucionarlo: 

Ran terminal command: cd /home/aylen/Documentos/IS2/proyectoIS && source dvenv/bin/activate && cd proyecto && python manage.py shell -c "
from monedas.models import HistorialCotizacion
from django.db import connection

# Ver el estado actual de la tabla
print('=== ESTADO ACTUAL DE HISTORIAL_COTIZACIONES ===')
registros = HistorialCotizacion.objects.all().order_by('id')
print(f'Total registros: {registros.count()}')

if registros.exists():
    print(f'Primer ID: {registros.first().id}')
    print(f'Último ID: {registros.last().id}')
    print('IDs existentes:', [r.id for r in registros])

# Verificar la secuencia de PostgreSQL
with connection.cursor() as cursor:
    cursor.execute(\"SELECT last_value FROM historial_cotizaciones_id_seq;\")
    resultado = cursor.fetchone()
    print(f'Último valor de secuencia: {resultado[0]}')
"

Entiendo, vamos directo a la solución. El problema es que la secuencia de PostgreSQL está desincronizada. Esto suele ocurrir cuando se importan datos o se hacen cambios manuales en la base de datos.

La solución es resetear la secuencia para que continúe desde el ID más alto existente: 

Ran terminal command: cd /home/aylen/Documentos/IS2/proyectoIS && source dvenv/bin/activate && cd proyecto && python manage.py shell -c "
from django.db import connection

# Resetear la secuencia de historial_cotizaciones
with connection.cursor() as cursor:
    cursor.execute(\"SELECT setval('historial_cotizaciones_id_seq', (SELECT MAX(id) FROM historial_cotizaciones));\")
    print('Secuencia de historial_cotizaciones reestablecida correctamente.')
    
    # Verificar el nuevo estado
    cursor.execute(\"SELECT last_value FROM historial_cotizaciones_id_seq;\")
    resultado = cursor.fetchone()
    print(f'Nuevo último valor de secuencia: {resultado[0]}')
