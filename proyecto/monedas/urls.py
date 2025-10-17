from django.urls import path
from . import views

app_name = 'monedas'

urlpatterns = [
    # URL para verificar cambios en precios
    # URLs para gestión de monedas
    path('crear/', views.moneda_crear, name='crear_monedas'),
    path('', views.moneda_lista, name='lista_monedas'),
    path('<int:pk>/editar/', views.moneda_editar, name='editar_monedas'),
    path('<int:pk>/detalle/', views.moneda_detalle, name='moneda_detalle'),
    # URLs para evolución de cotizaciones
    path('<int:pk>/evolucion/', views.evolucion_cotizacion, name='evolucion_cotizacion'),
    path('<int:pk>/api-evolucion/', views.api_evolucion_cotizacion, name='api_evolucion_cotizacion'),
]