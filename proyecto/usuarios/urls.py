from django.urls import path
from . import views
from transacciones.views import historial_transacciones

app_name = 'usuarios'

urlpatterns = [
    path('registro/', views.registro_usuario, name='registro'),
    path('activar/<str:uidb64>/<str:token>/', views.activar_cuenta, name='activar_cuenta'),
    path('perfil/', views.perfil, name='perfil'),
    path('recuperar-password/', views.recuperar_password, name='recuperar_password'),
    path('reset-password/<str:uidb64>/<str:token>/', views.reset_password_confirm, name='reset_password_confirm'),
    # Rutas para administración de usuarios
    path('administrar/', views.administrar_usuarios, name='administrar_usuarios'),
    path('usuario/<int:pk>/', views.usuario_detalle, name='usuario_detalle'),
    path('usuario/<int:pk>/bloquear/', views.bloquear_usuario, name='bloquear_usuario'),
    path('usuario/<int:pk>/asignar-rol/', views.asignar_rol, name='asignar_rol'),
    path('usuario/<int:pk>/desasignar-rol/<int:rol_id>/', views.remover_rol, name='remover_rol'),
    # Rutas para gestión de clientes-usuarios
    path('usuario/<int:pk>/asignar-clientes/', views.asignar_clientes, name='asignar_clientes'),
    path('usuario/<int:pk>/desasignar-cliente/<int:cliente_id>/', views.remover_cliente, name='remover_cliente'),
    path('mis-clientes/', views.ver_clientes_asociados, name='mis_clientes'),
    path('seleccionar-cliente-activo/<int:cliente_id>/', views.seleccionar_cliente_activo, name='seleccionar_cliente_activo'),
    path('cliente/<int:cliente_id>/', views.detalle_cliente, name='detalle_cliente'),
    # Rutas para gestión de tarjetas por operadores
    path('cliente/<int:pk>/agregar-tarjeta/', views.agregar_tarjeta_cliente, name='agregar_tarjeta_cliente'),
    path('cliente/<int:pk>/eliminar-tarjeta/<str:payment_method_id>/', views.eliminar_tarjeta_cliente, name='eliminar_tarjeta_cliente'),
    # URL para historial de transacciones del cliente
    path('cliente/<int:cliente_id>/historial/', historial_transacciones, name='cliente_historial'),
]
