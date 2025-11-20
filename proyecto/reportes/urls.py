from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('transacciones/', views.transacciones_reportes, name='transacciones'),
    path('dashboard-ganancias/', views.dashboard_ganancias, name='dashboard_ganancias'),
    path('api/ganancias/', views.obtener_datos_ganancias, name='api_ganancias'),
]
