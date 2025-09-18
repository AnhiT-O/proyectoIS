from django.urls import path
from . import views

app_name = 'transacciones'

urlpatterns = [
    path('comprar/', views.compra_monto_moneda, name='compra_monto_moneda'),
    path('comprar/medio-pago/', views.compra_medio_pago, name='compra_medio_pago')
]