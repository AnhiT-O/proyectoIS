from django.urls import path
from . import views
from .views import stripe_webhook, crear_setup_intent, crear_payment_intent, obtener_metodos_pago

app_name = 'medios_pago'

urlpatterns = [
    # URLs para gestión específica de medios de pago del cliente
    path('webhook/', stripe_webhook, name='stripe_webhook'),
    path('setup-intent/', crear_setup_intent, name='crear_setup_intent'),
    path('payment-intent/', crear_payment_intent, name='crear_payment_intent'),
    path('cliente/<int:cliente_id>/metodos-pago/', obtener_metodos_pago, name='obtener_metodos_pago'),
    # Las vistas están en clientes/views.py
]
