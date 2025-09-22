from django.urls import path
from . import views

app_name = 'monedas'

urlpatterns = [
    path('crear/', views.moneda_crear, name='crear_monedas'),
    path('', views.moneda_lista, name='lista_monedas'),
    path('<int:pk>/', views.moneda_detalle, name='moneda_detalle'),
    path('<int:pk>/editar/', views.moneda_editar, name='editar_monedas')
]