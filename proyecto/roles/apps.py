# myapp/apps.py

from django.apps import AppConfig

class RolesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'roles'

    def ready(self):
        # Importar el archivo de señales
        import roles.signals