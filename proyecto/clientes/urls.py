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
]