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
    path('cotizaciones/', include('cotizacion.urls')),
    path('medios-pago/', include('medios_pago.urls', namespace='medios_pago'))
]

handler403 = 'proyecto.views.custom_permission_denied_view'
