# Sistema de Límites de Transacciones

## Descripción General

Este sistema implementa la gestión de límites diarios y mensuales para transacciones de clientes en una casa de cambio, cumpliendo con las regulaciones legales que establecen límites globales iguales para todos los clientes.

## Arquitectura del Sistema

### 1. Modelos de Base de Datos

#### LimiteGlobal
- **Propósito**: Almacena los límites máximos que aplican a todos los clientes
- **Campos**:
  - `limite_diario`: Límite diario en guaraníes (ej: 90,000,000)
  - `limite_mensual`: Límite mensual en guaraníes (ej: 450,000,000)
  - `fecha_inicio`: Desde cuándo rige este límite
  - `fecha_fin`: Hasta cuándo rige (opcional)
  - `activo`: Si el límite está vigente

#### ConsumoLimiteCliente
- **Propósito**: Registra cuánto ha consumido cada cliente de sus límites
- **Campos**:
  - `cliente`: Referencia al cliente
  - `fecha`: Fecha del registro
  - `consumo_diario`: Monto consumido en el día
  - `consumo_mensual`: Monto consumido en el mes

### 2. Servicio de Gestión (LimiteService)

El servicio centraliza toda la lógica de negocio relacionada con límites:

#### Métodos Principales:
- `convertir_a_guaranies()`: Convierte montos a guaraníes según el tipo de transacción
- `validar_limite_transaccion()`: Valida si una transacción puede realizarse
- `actualizar_consumo_cliente()`: Actualiza el consumo tras una transacción
- `obtener_limites_disponibles()`: Consulta límites disponibles para un cliente
- `resetear_consumos_diarios/mensuales()`: Resetea consumos periódicamente

## Flujo de Validación de Transacciones

### 1. Conversión a Guaraníes
```python
# Ejemplo: Cliente compra 1000 USD
monto_guaranies = LimiteService.convertir_a_guaranies(
    monto=1000,
    moneda=moneda_usd,
    tipo_transaccion='COMPRA',
    cliente=cliente
)
# Resultado: 7,650,000 PYG (usando tasa de venta)
```

### 2. Validación de Límites
```python
# Verifica que no supere límites diarios y mensuales
LimiteService.validar_limite_transaccion(cliente, monto_guaranies)
# Lanza ValidationError si supera algún límite
```

### 3. Actualización de Consumo
```python
# Actualiza el consumo del cliente
LimiteService.actualizar_consumo_cliente(cliente, monto_guaranies)
```

## Uso del Sistema

### Para Desarrolladores de Transacciones

```python
from monedas.services import LimiteService
from django.core.exceptions import ValidationError

def procesar_transaccion(cliente, moneda, tipo, monto):
    try:
        # Validar y procesar en una sola operación
        resultado = LimiteService.validar_y_procesar_transaccion(
            cliente=cliente,
            moneda=moneda,
            tipo_transaccion=tipo,
            monto_original=monto
        )
        
        # El resultado contiene:
        # - monto_original
        # - monto_guaranies
        # - tasa_utilizada
        # - consumo_diario_actualizado
        # - consumo_mensual_actualizado
        # - limites_restantes
        
        return resultado
        
    except ValidationError as e:
        # Manejar error de límite superado
        print(f"Transacción rechazada: {e}")
        raise
```

### Consultar Límites Disponibles

```python
# Obtener información detallada de límites
limites_info = LimiteService.obtener_limites_disponibles(cliente)

print(f"Disponible hoy: {limites_info['disponible_diario']:,} PYG")
print(f"Disponible este mes: {limites_info['disponible_mensual']:,} PYG")
print(f"Uso diario: {limites_info['porcentaje_uso_diario']}%")
```

## Administración del Sistema

### 1. Gestión de Límites Globales

#### URLs disponibles:
- `/monedas/limites/` - Lista de límites
- `/monedas/limites/crear/` - Crear nuevo límite
- `/monedas/limites/<id>/editar/` - Editar límite
- `/monedas/limites/<id>/activar/` - Activar límite

#### Funcionalidades:
- Solo un límite puede estar activo a la vez
- Historial completo de cambios de límites
- Validaciones automáticas (diario ≤ mensual)

### 2. Management Commands

#### Reseteo Automático
```bash
# Resetear límites diarios y mensuales (ejecutar diariamente)
python manage.py resetear_limites

# Forzar reset mensual
python manage.py resetear_limites --force-monthly

# Ver qué se haría sin ejecutar
python manage.py resetear_limites --dry-run
```

#### Configuración en Cron
```bash
# Ejecutar diariamente a las 00:01
1 0 * * * cd /ruta/del/proyecto && python manage.py resetear_limites
```

## APIs AJAX

### 1. Consultar Límites de Cliente
```javascript
// GET /monedas/api/limites/cliente/?cliente_id=123
fetch('/monedas/api/limites/cliente/?cliente_id=123')
    .then(response => response.json())
    .then(data => {
        console.log('Límites disponibles:', data.data.limites);
    });
```

### 2. Validar Transacción
```javascript
// POST /monedas/api/limites/validar/
const formData = new FormData();
formData.append('cliente_id', '123');
formData.append('moneda_id', '2');
formData.append('tipo_transaccion', 'COMPRA');
formData.append('monto', '1000');

fetch('/monedas/api/limites/validar/', {
    method: 'POST',
    body: formData,
    headers: {
        'X-CSRFToken': getCookie('csrftoken')
    }
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('Transacción válida:', data.data);
    } else {
        console.log('Error:', data.error);
    }
});
```

## Migraciones

### Aplicar las Nuevas Tablas
```bash
# Crear migraciones
python manage.py makemigrations monedas

# Aplicar migraciones
python manage.py migrate

# Verificar que se creó el límite inicial
python manage.py shell -c "from monedas.models import LimiteGlobal; print(LimiteGlobal.objects.all())"
```

## Permisos Requeridos

### Para Gestionar Límites
- `monedas.gestion` - Crear, editar y activar límites globales

### Para Consultar APIs
- Usuario autenticado para consultas AJAX

## Consideraciones de Rendimiento

1. **Índices**: Los modelos incluyen índices en campos frecuentemente consultados
2. **Consultas optimizadas**: El servicio minimiza las consultas a base de datos
3. **Caché**: Se puede implementar caché para límites vigentes si es necesario

## Monitoreo y Logs

### Logs Importantes
- Creación/activación de nuevos límites
- Transacciones rechazadas por límites
- Ejecución de resets automáticos

### Métricas Sugeridas
- Porcentaje de uso de límites por cliente
- Transacciones rechazadas por día
- Distribución de uso de límites

## Extensiones Futuras

1. **Límites personalizados por cliente** (modificar para casos especiales)
2. **Alertas automáticas** cuando clientes se acercan al límite
3. **Dashboard de monitoreo** en tiempo real
4. **Integración con sistemas de notificaciones**

## Ejemplos de Configuración

### Límites Típicos
```python
# Límites estándar
limite_diario = 90_000_000    # 90 millones PYG
limite_mensual = 450_000_000  # 450 millones PYG

```

### Conversiones Típicas
```python
# USD a PYG (ejemplo con tasa 7600)
1000 USD compra = 1000 * 7650 = 7,650,000 PYG
1000 USD venta = 1000 * 7550 = 7,550,000 PYG

# EUR a PYG (ejemplo con tasa 8200)
500 EUR compra = 500 * 8250 = 4,125,000 PYG
```

---

## Soporte y Mantenimiento

Para dudas o problemas con el sistema de límites:

1. Revisar logs de Django para errores
2. Verificar que hay límites globales activos
3. Comprobar que los cron jobs se ejecutan correctamente
4. Validar permisos de usuario para gestión de límites