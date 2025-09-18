from django.urls import path
from . import views

app_name = 'transacciones'

urlpatterns = [
    path('comprar/', views.compra_monto_moneda, name='compra_monto_moneda'),
    path('comprar/pago/', views.compra_medio_pago, name='compra_medio_pago'),
    path('ajax/precio-moneda/<int:moneda_id>/', views.obtener_precio_moneda, name='compra_precio_moneda'),
]