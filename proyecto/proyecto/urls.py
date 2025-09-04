"""
URL configuration for proyecto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('ingresar/', views.login_usuario, name='login'),
    path('cerrar-sesion/', views.logout_usuario, name='logout'),
    path('usuarios/', include('usuarios.urls')),
    path('roles/', include('roles.urls')),
    path('clientes/', include('clientes.urls')),
    path('monedas/', include('monedas.urls')),
    path('tasas/', include('tasa.urls')),
]

# Configuración para manejadores de errores personalizados
handler403 = 'proyecto.views.custom_permission_denied_view'
