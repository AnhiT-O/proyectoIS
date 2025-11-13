AnhiT-O: no usamos el modulo admin de django si no un usuario con Rol con acceso completo al sistema que está en #file:roles 

GitHub Copilot: Modificaré la vista de reportes para exigir que el usuario pertenezca al rol 'Administrador' (en lugar de usar el atributo es_admin). Ahora actualizo el archivo reportes/views.py. 

## views.py+4-3

- He actualizado la verificación de permisos de la vista de reportes para usar el rol 'Administrador' (modelo Roles) en lugar del admin de Django ni un atributo es_admin.

- Ahora solo los usuarios que pertenezcan al grupo llamado 'Administrador' podrán acceder a /reportes/transacciones/.

Si quieres que el acceso use otro nombre de rol o permisos más granulares, indícalo.