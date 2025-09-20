# DOCUMENTACIÓN DE FUNCIONALIDADES DE STOCK Y LIMITACIONES
# Para el módulo de compra y venta de divisas

## IMPORTACIONES NECESARIAS
```python
from monedas.models import Moneda, Limitacion
from monedas.guaranies import (
    STOCK_GUARANIES, 
    puede_vender_divisa, 
    actualizar_stock_guaranies,
    obtener_stock_guaranies
)
```

## FUNCIONES DISPONIBLES PARA LIMITACIONES

### 1. Verificar límites por segmentación de cliente
```python
# Obtener cantidad máxima que puede comprar/vender un cliente según su segmentación
moneda = Moneda.objects.get(simbolo='USD')
cantidad_maxima = moneda.get_cantidad_maxima_por_segmentacion('VIP')  # o 'CORPORATIVO', 'MINORISTA'

# Verificar si una cantidad específica está dentro del límite
puede_operar = moneda.tiene_stock_disponible(cantidad_solicitada, 'VIP')
```

### 2. Obtener precios con beneficios
```python
# Calcular precios considerando el beneficio del cliente
precio_compra = moneda.calcular_precio_compra(porcentaje_beneficio)
precio_venta = moneda.calcular_precio_venta(porcentaje_beneficio)

# O usar el método completo con objeto cliente
precios = moneda.get_precios_cliente(cliente)  # Retorna dict con ambos precios
```

## FUNCIONES PARA GESTIÓN DE STOCK

### 3. Stock de monedas extranjeras
```python
# Verificar stock disponible
stock_actual = moneda.stock

# Actualizar stock después de transacción
moneda.actualizar_stock(cantidad)  # Positivo: suma, Negativo: resta
```

### 4. Stock de guaraníes
```python
# Verificar si hay suficientes guaraníes para venta de divisa
if puede_vender_divisa(monto_guaranies_a_entregar):
    # Proceder con la venta
    pass

# Actualizar stock de guaraníes después de transacción
actualizar_stock_guaranies(monto)  # Positivo: suma, Negativo: resta

# Obtener stock actual de guaraníes
stock_gs = obtener_stock_guaranies()
```

## EJEMPLO DE FLUJO COMPLETO PARA COMPRA DE DIVISA

```python
def comprar_divisa(cliente, moneda, cantidad_divisa):
    # 1. Verificar límites por segmentación
    segmentacion = cliente.segmentacion  # Ejemplo: 'VIP'
    if not moneda.tiene_stock_disponible(cantidad_divisa, segmentacion):
        return "Error: Cantidad excede el límite permitido"
    
    # 2. Verificar stock de la moneda
    if moneda.stock < cantidad_divisa:
        return "Error: Stock insuficiente de la moneda"
    
    # 3. Calcular precio
    precio_compra = moneda.calcular_precio_compra(cliente.beneficio_segmento)
    monto_guaranies = cantidad_divisa * precio_compra
    
    # 4. Actualizar stocks
    moneda.actualizar_stock(-cantidad_divisa)  # Resta del stock de divisa
    actualizar_stock_guaranies(monto_guaranies)  # Suma guaraníes recibidos
    
    return "Compra realizada exitosamente"
```

## EJEMPLO DE FLUJO COMPLETO PARA VENTA DE DIVISA

```python
def vender_divisa(cliente, moneda, cantidad_divisa):
    # 1. Verificar límites por segmentación
    segmentacion = cliente.segmentacion  # Ejemplo: 'CORPORATIVO'
    if not moneda.tiene_stock_disponible(cantidad_divisa, segmentacion):
        return "Error: Cantidad excede el límite permitido"
    
    # 2. Calcular guaraníes a entregar
    precio_venta = moneda.calcular_precio_venta(cliente.beneficio_segmento)
    monto_guaranies = cantidad_divisa * precio_venta
    
    # 3. Verificar stock de guaraníes
    if not puede_vender_divisa(monto_guaranies):
        return "Error: Stock insuficiente de guaraníes"
    
    # 4. Actualizar stocks
    moneda.actualizar_stock(cantidad_divisa)  # Suma a stock de divisa
    actualizar_stock_guaranies(-monto_guaranies)  # Resta guaraníes entregados
    
    return "Venta realizada exitosamente"
```

## SEGMENTACIONES DISPONIBLES
- 'VIP'
- 'CORPORATIVO'  
- 'MINORISTA'

## NOTAS IMPORTANTES
- Los porcentajes de limitación se configuran desde el formulario de edición de monedas
- El stock de guaraníes es global y se gestiona separadamente
- Todos los métodos manejan automáticamente la persistencia en base de datos
- Las cantidades negativas en actualizar_stock() restan, las positivas suman