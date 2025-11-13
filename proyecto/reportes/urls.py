from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('transacciones/', views.transacciones_reportes, name='transacciones'),
]
