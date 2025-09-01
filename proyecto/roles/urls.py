from django.urls import path
from . import views

app_name = 'roles'

urlpatterns = [
    path('', views.listar_roles, name='listar_roles'),
    path('crear/', views.crear_rol, name='crear_rol'),
    path('editar/<int:pk>/', views.editar_rol, name='editar_rol'),
    path('detalle/<int:pk>/', views.detalle_rol, name='detalle_rol'),
]
