### TemplateSyntaxError at /cotizaciones/
'block' tag with name 'content' appears more than once
Request Method:	GET
Request URL:	http://127.0.0.1:8000/cotizaciones/
Django Version:	5.2.6
Exception Type:	TemplateSyntaxError
Exception Value:	
'block' tag with name 'content' appears more than once
Exception Location:	/home/aylen/Documentos/IS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages/django/template/loader_tags.py, line 228, in do_block
Raised during:	cotizacion.views.CotizacionListView
Python Executable:	/home/aylen/Documentos/IS2/proyectoIS/proyecto/dvenv/bin/python
Python Version:	3.12.3
Python Path:	
['/home/aylen/Documentos/IS2/proyectoIS/proyecto',
 '/usr/lib/python312.zip',
 '/usr/lib/python3.12',
 '/usr/lib/python3.12/lib-dynload',
 '/home/aylen/Documentos/IS2/proyectoIS/proyecto/dvenv/lib/python3.12/site-packages']
Server time:	Thu, 04 Sep 2025 21:51:44 +0000

El error indica que hay más de un bloque `content` en el template. Voy a revisar todo el archivo para encontrar y corregir esta duplicación. Ahora veo el problema. El template tiene dos bloques `content` y además está mezclando la estructura del template. Voy a reorganizar el archivo correctamente: 
```


Se realizaron cambios.


```
He reorganizado el template para corregir los siguientes problemas:

1. Eliminé el bloque `content` duplicado
2. Moví `{% load static %}` al principio del archivo, después de `extends`
3. Organicé los bloques en el orden correcto:
   - `extends`
   - `load`
   - `title`
   - `extra_css`
   - `content`

La estructura del template ahora es correcta y debería funcionar sin errores. Los bloques están organizados de manera lógica y no hay duplicaciones. Intenta recargar la página de cotizaciones ahora. Si encuentras algún otro error, házmelo saber.