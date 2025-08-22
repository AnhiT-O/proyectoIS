from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('login/', views.login_usuario, name='login'),
    path('logout/', views.logout_usuario, name='logout'),
    path('registro/', views.registro_usuario, name='registro'),
    path('registro-exitoso/', views.registro_exitoso, name='registro_exitoso'),
    path('activar/<str:uidb64>/<str:token>/', views.activar_cuenta, name='activar_cuenta'),
    path('perfil/', views.perfil, name='perfil'),
    path('recuperar-password/', views.recuperar_password, name='recuperar_password'),
    path('reset-password/<str:uidb64>/<str:token>/', views.reset_password_confirm, name='reset_password_confirm'),
    # Rutas para administración de usuarios
    path('administrar/', views.administrar_usuarios, name='administrar_usuarios'),
    path('usuario/<int:pk>/bloquear/', views.bloquear_usuario, name='bloquear_usuario'),
    path('usuario/<int:pk>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
]
