from django.apps import AppConfig


class TasaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasa'
    verbose_name = 'Gestión de Tasas de Cambio'
    
    def ready(self):
        try:
            import tasa.signals
        except ImportError:
            pass
