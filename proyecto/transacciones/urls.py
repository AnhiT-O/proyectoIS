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
    path('vender/exito/', views.venta_exito, name='venta_exito'),

    # URLs para edicion de recargos
    path('recargos/', views.editar_recargos, name='editar_recargos'),
    
    # URLs para funcionalidades auxiliares de límites
    path('limites/cliente/', views.obtener_limites_cliente, name='obtener_limites_cliente'),
    path('limites/simular/', views.simular_transaccion_limites, name='simular_transaccion_limites'),
    
    # URLs para historial de transacciones
    path('historial/', views.historial_transacciones, name='historial'),
    path('detalle/<int:transaccion_id>/', views.detalle_transaccion, name='detalle'),
    path('editar/<int:transaccion_id>/', views.editar_transaccion, name='editar'),
]