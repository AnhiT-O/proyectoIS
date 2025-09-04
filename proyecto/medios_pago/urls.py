from django.urls import path
from . import views

app_name = 'medios_pago'

urlpatterns = [
    path('', views.medio_pago_lista, name='medio_pago_lista'),
    path('<int:pk>/', views.medio_pago_detalle, name='medio_pago_detalle'),
    path('<int:pk>/cambiar-estado/', views.medio_pago_cambiar_estado, name='medio_pago_cambiar_estado'),
    path('ajax/campos-por-tipo/', views.obtener_campos_por_tipo, name='obtener_campos_por_tipo'),
]
