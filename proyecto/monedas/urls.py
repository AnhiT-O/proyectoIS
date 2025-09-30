from django.urls import path
from . import views

app_name = 'monedas'

urlpatterns = [
    # URL para verificar cambios en precios
    path('verificar-cambios/<int:moneda_id>/', views.verificar_cambios_precios, name='verificar_cambios'),
    # URLs para gestión de monedas
    path('crear/', views.moneda_crear, name='crear_monedas'),
    path('', views.moneda_lista, name='lista_monedas'),
    path('<int:pk>/editar/', views.moneda_editar, name='editar_monedas'),
    path('<int:pk>/detalle/', views.moneda_detalle, name='moneda_detalle'),
    
    # URLs para verificación de cambios de precios
    path('verificar-cambios/<int:moneda_id>/', views.verificar_cambios_precios, name='verificar_cambios'),
]