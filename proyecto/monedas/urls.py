from django.urls import path
from . import views

app_name = 'monedas'

urlpatterns = [
    # URLs para gestión de monedas
    path('crear/', views.moneda_crear, name='crear_monedas'),
    path('', views.moneda_lista, name='lista_monedas'),
    path('<int:pk>/editar/', views.moneda_editar, name='editar_monedas'),
    path('<int:pk>/detalle/', views.moneda_detalle, name='moneda_detalle'),
    
    # URLs para gestión de límites
    path('limites/', views.lista_limites, name='lista_limites'),
    path('limites/crear/', views.crear_limite, name='crear_limite'),
    path('limites/<int:pk>/editar/', views.editar_limite, name='editar_limite'),
    path('limites/<int:pk>/activar/', views.activar_limite, name='activar_limite'),
    
    # URLs AJAX para consultas de límites
    path('api/limites/cliente/', views.consultar_limites_cliente, name='api_limites_cliente'),
    path('api/limites/validar/', views.validar_transaccion_limite, name='api_validar_transaccion'),
]