from django.urls import path
from . import views

app_name = 'monedas'

urlpatterns = [
    path('crear/', views.moneda_crear, name='crear_monedas'),
    path('', views.moneda_lista, name='lista_monedas'),
    path('<int:pk>/editar/', views.moneda_editar, name='editar_monedas'),
    path('simulador/', views.simular, name='simular')
]