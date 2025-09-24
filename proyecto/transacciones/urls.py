from django.urls import path
from . import views

app_name = 'transacciones'

urlpatterns = [
    # URLs para proceso de compra
    path('comprar/', views.compra_monto_moneda, name='compra_monto_moneda'),
    path('comprar/medio-pago/', views.compra_medio_pago, name='compra_medio_pago'),
    path('comprar/medio-cobro/', views.compra_medio_cobro, name='compra_medio_cobro'),
    path('comprar/confirmacion/', views.compra_confirmacion, name='compra_confirmacion'),
    path('comprar/exito/', views.compra_exito, name='compra_exito'),
    
    # URLs para proceso de venta
    path('vender/', views.venta_monto_moneda, name='venta_monto_moneda'),
    path('vender/medio-pago/', views.venta_medio_pago, name='venta_medio_pago'),
    path('vender/medio-cobro/', views.venta_medio_cobro, name='venta_medio_cobro'),
    path('vender/confirmacion/', views.venta_confirmacion, name='venta_confirmacion'),
    path('vender/exito/', views.venta_exito, name='venta_exito')
]