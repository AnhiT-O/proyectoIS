from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('crear/', views.cliente_crear, name='cliente_crear'),
    path('', views.cliente_lista, name='cliente_lista'),
    path('<int:pk>/', views.cliente_detalle, name='cliente_detalle'),
    path('<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),
    path('cambiar-segmento/<int:pk>/', views.cambiar_segmento, name='cambiar_segmento'),
]