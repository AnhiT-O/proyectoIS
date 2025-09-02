from django.urls import path
from . import views

app_name = 'tasa'

urlpatterns = [
    path('', views.lista_tasas, name='lista_tasas'),
    path('crear/', views.crear_tasa, name='crear_tasa'),
    path('editar/<int:tasa_id>/', views.editar_tasa, name='editar_tasa'),
    path('activar/<int:tasa_id>/', views.activar_tasa, name='activar_tasa'),
]
