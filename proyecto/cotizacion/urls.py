from django.urls import path
from . import views

app_name = 'cotizacion'

urlpatterns = [
    path('', views.CotizacionListView.as_view(), name='cotizacion_lista'),
    path('crear/', views.CotizacionCreateView.as_view(), name='cotizacion_crear'),
]
