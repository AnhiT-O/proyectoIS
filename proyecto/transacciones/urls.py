"""
Configuración de URLs para la aplicación de transacciones.

Este módulo define todas las rutas URL disponibles en la aplicación de transacciones,
organizadas por funcionalidad: compras, ventas, gestión de recargos, historial y
funcionalidades auxiliares.

Grupos de URLs:
    - Proceso de compra: URLs para el flujo completo de compra de monedas
    - Proceso de venta: URLs para el flujo completo de venta de monedas  
    - Gestión de recargos: URLs para administrar recargos por medio de pago
    - Historial: URLs para consultar transacciones históricas
    - Funcionalidades auxiliares: APIs para validaciones y consultas

Author: Equipo de desarrollo Global Exchange
Date: 2024
"""

from django.urls import path
from . import views
from . import views_2fa

app_name = 'transacciones'

urlpatterns = [
    # URLs para proceso de compra
    path('comprar/', views.compra_monto_moneda, name='compra_monto_moneda'),
    path('comprar/medio-pago/', views.compra_medio_pago, name='compra_medio_pago'),
    path('comprar/medio-cobro/', views.compra_medio_cobro, name='compra_medio_cobro'),
    path('comprar/confirmacion/', views.compra_confirmacion, name='compra_confirmacion'),
    path('comprar/exito/', views.compra_exito, name='compra_exito'),
    
    # URLs para proceso de venta
    path('vender/', views.venta_monto_moneda, name='venta_monto_moneda'),
    path('vender/medio-pago/', views.venta_medio_pago, name='venta_medio_pago'),
    path('vender/medio-cobro/', views.venta_medio_cobro, name='venta_medio_cobro'),
    path('vender/confirmacion/', views.venta_confirmacion, name='venta_confirmacion'),
    path('vender/exito/', views.venta_exito, name='venta_exito'),
    
    # URLs para historial de transacciones
    path('historial/<int:cliente_id>/', views.historial_transacciones, name='historial_cliente'),
    path('detalle/<int:transaccion_id>/', views.detalle_historial, name='historial_detalle'),

    path('gestion-transacciones/', views.ver_variables, name='ver_variables'),
    path('edicion-transacciones/', views.editar_variables, name='editar_variables'),
    
    # URLs para gestión de TAUsers
    path('tausers/', views.revisar_tausers, name='revisar_tausers'),
    path('tausers/<int:pk>/', views.tauser_detalle, name='tauser_detalle'),
    path('tausers/<int:tauser_id>/verificar-estado/', views.verificar_estado_tauser, name='verificar_estado_tauser'),
    
    # URLs para autenticación de dos factores (2FA)
    path('2fa/send-token/', views_2fa.send_2fa_token, name='send_2fa_token'),
    path('2fa/verify-token/', views_2fa.verify_2fa_token, name='verify_2fa_token'),
    path('2fa/token-status/', views_2fa.get_token_status_view, name='token_status'),
    path('2fa/resend-token/', views_2fa.resend_2fa_token, name='resend_2fa_token'),
]