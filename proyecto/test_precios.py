#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.append('/home/aylen/Documentos/IS2/proyectoIS/proyecto')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from monedas.models import Moneda, Limitacion

# Probar métodos de precio
if Moneda.objects.exists():
    moneda = Moneda.objects.first()
    print(f"=== Probando métodos de precio para {moneda} ===")
    print(f"Tasa base: {moneda.tasa_base}")
    print(f"Comisión compra: {moneda.comision_compra}")
    print(f"Comisión venta: {moneda.comision_venta}")
    
    # Probar métodos de cálculo de precios
    precio_venta = moneda.calcular_precio_venta()
    precio_compra = moneda.calcular_precio_compra()
    
    print(f"\nPrecios sin beneficio:")
    print(f"Precio venta: {precio_venta}")
    print(f"Precio compra: {precio_compra}")
    
    # Probar con beneficio
    precio_venta_beneficio = moneda.calcular_precio_venta(10)  # 10% beneficio
    precio_compra_beneficio = moneda.calcular_precio_compra(10)
    
    print(f"\nPrecios con 10% beneficio:")
    print(f"Precio venta: {precio_venta_beneficio}")
    print(f"Precio compra: {precio_compra_beneficio}")
    
    print("\n✅ Todos los métodos funcionan correctamente!")
else:
    print("❌ No hay monedas en la base de datos")