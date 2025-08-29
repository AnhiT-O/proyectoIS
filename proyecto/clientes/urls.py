from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('crear/', views.cliente_crear, name='cliente_crear'),
    path('lista/', views.cliente_lista, name='cliente_lista'),
    path('<int:pk>/', views.cliente_detalle, name='cliente_detalle'),
    path('<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),
    path('cambiar-categoria/<int:pk>/', views.cambiar_categoria, name='cambiar_categoria'),
]