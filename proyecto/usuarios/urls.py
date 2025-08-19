from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('registro/', views.registro_usuario, name='registro'),
    path('registro-exitoso/', views.registro_exitoso, name='registro_exitoso'),
    path('activar/<str:uidb64>/<str:token>/', views.activar_cuenta, name='activar_cuenta'),
    path('perfil/', views.perfil, name='perfil'),
]
