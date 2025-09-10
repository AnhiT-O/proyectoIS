from django.urls import path
from . import views

app_name = 'cotizacion'

urlpatterns = [
    path('', views.CotizacionListView.as_view(), name='cotizacion_lista'),
    path('crear/', views.CotizacionCreateView.as_view(), name='cotizacion_crear'),
    path('simulador/', views.SimuladorView.as_view(), name='simulador'),
    path('simular-conversion/', views.SimuladorView.as_view(), name='simular_conversion'),
]
