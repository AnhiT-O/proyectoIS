from django.urls import path
from . import views
from . import views_pdf

app_name = 'reportes'

urlpatterns = [
    path('transacciones/', views.transacciones_reportes, name='transacciones'),
    path('transacciones/pdf/', views_pdf.view2, name='transacciones_pdf'),
    path('dashboard-ganancias/', views.dashboard_ganancias, name='dashboard_ganancias'),
    path('api/ganancias/', views.obtener_datos_ganancias, name='api_ganancias'),
    path('api/desglose-ganancias/', views.obtener_desglose_ganancias, name='api_desglose_ganancias'),
]
