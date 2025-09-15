from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('crear/', views.cliente_crear, name='cliente_crear'),
    path('', views.cliente_lista, name='cliente_lista'),
    path('<int:pk>/', views.cliente_detalle, name='cliente_detalle'),
    path('<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),
    
    # URLs para gestión de medios de pago del cliente
    path('<int:pk>/agregar-tarjeta/', views.cliente_agregar_tarjeta, name='cliente_agregar_tarjeta'),
    path('<int:pk>/agregar-cuenta/', views.cliente_agregar_cuenta, name='cliente_agregar_cuenta'),
    path('<int:pk>/medio-pago/<int:medio_id>/cambiar-estado/', views.cliente_cambiar_estado_medio_pago, name='cliente_cambiar_estado_medio_pago'),
    path('<int:pk>/medio-pago/<int:medio_id>/eliminar/', views.cliente_eliminar_medio_pago, name='cliente_eliminar_medio_pago'),
]