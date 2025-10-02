from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('crear/', views.cliente_crear, name='cliente_crear'),
    path('', views.cliente_lista, name='cliente_lista'),
    path('<int:pk>/', views.cliente_detalle, name='cliente_detalle'),
    path('<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),
    path('<int:pk>/agregar-tarjeta/', views.agregar_tarjeta, name='agregar_tarjeta'),
    path('<int:pk>/eliminar-tarjeta/<str:payment_method_id>/', views.eliminar_tarjeta, name='eliminar_tarjeta'),
    
    # URLs para gestión de medios de acreditación del cliente
    path('<int:pk>/agregar-cuenta-bancaria/', views.cliente_agregar_cuenta_bancaria, name='cliente_agregar_cuenta_bancaria'),
    path('<int:pk>/agregar-billetera/', views.cliente_agregar_billetera, name='cliente_agregar_billetera'),
    path('<int:pk>/eliminar-medio-acreditacion/<str:tipo>/<int:medio_id>/', views.cliente_eliminar_medio_acreditacion, name='cliente_eliminar_medio_acreditacion'),
    
    # URLs para historial de transacciones del cliente
    path('<int:cliente_id>/historial/', views.historial_transacciones, name='cliente_historial'),
    path('<int:cliente_id>/historial/<int:transaccion_id>/', views.cliente_detalle_transaccion, name='cliente_historial_detalle')
]