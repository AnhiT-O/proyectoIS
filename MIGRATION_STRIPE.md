# Script de Migración para Integración de Stripe

## Pasos de Migración

### 1. Crear migración de base de datos

```bash
$ manage.py makemigrations medios_pago
```

### 2. Aplicar migración

```bash
$ manage.py migrate
```

## Campos Eliminados de la Base de Datos

Estos campos ya no se almacenarán porque Stripe maneja la información sensible:

- `numero_tarjeta` - Ahora manejado por Stripe
- `cvv_tarjeta` - Ahora manejado por Stripe  
- `fecha_vencimiento_tc` - Ahora manejado por Stripe
- `nombre_titular_tarjeta` - Ahora manejado por Stripe

## Campos Agregados

- `stripe_customer_id` - ID del customer en Stripe
- `stripe_payment_method_id` - ID del método de pago en Stripe

## Razones para la Eliminación

1. **Seguridad PCI DSS**: Stripe maneja toda la información sensible cumpliendo con los estándares PCI DSS
2. **Reducción de Responsabilidad**: No almacenar datos sensibles reduce riesgos legales y de seguridad
3. **Tokens de Stripe**: Usamos Payment Methods y Customer IDs de Stripe en lugar de datos de tarjeta
4. **Mejor UX**: Stripe Elements proporciona una mejor experiencia de usuario

## Nuevos Flujos

### Para Agregar Tarjetas:
1. Usuario usa la nueva URL: `/clientes/<id>/agregar-tarjeta-stripe/`
2. El frontend usa Stripe Elements para capturar datos de forma segura
3. Se crea un Setup Intent en Stripe
4. Se guarda solo el Payment Method ID en nuestra base de datos

### Para Procesar Pagos:
1. Se crea un Payment Intent usando el Payment Method guardado
2. Stripe procesa el pago de forma segura
3. Webhook notifica el resultado del pago

## URLs Disponibles

- **Tradicional**: `/clientes/<id>/agregar-tarjeta/` (mantiene compatibilidad)
- **Con Stripe**: `/clientes/<id>/agregar-tarjeta-stripe/` (nuevo método seguro)
- **Webhook**: `/medios-pago/webhook/` (para notificaciones de Stripe)
- **API Setup Intent**: `/medios-pago/setup-intent/` (para crear métodos de pago)
- **API Payment Intent**: `/medios-pago/payment-intent/` (para procesar pagos)

## Testing con Tarjetas de Prueba

Usar estas tarjetas de prueba de Stripe para desarrollo:

- **Visa**: 4242424242424242
- **Visa (debit)**: 4000056655665556  
- **Mastercard**: 5555555555554444
- **American Express**: 378282246310005
- **Fecha**: Cualquier fecha futura
- **CVV**: Cualquier 3 dígitos

## Verificación Post-Migración

1. Verificar que las nuevas columnas existen:
```sql
\d medios_pago_clientes
```

2. Verificar que las vistas funcionan:
- Acceder a `/clientes/<id>/agregar-tarjeta-stripe/`
- Probar agregar una tarjeta de prueba
- Verificar que se guarda en Stripe y en la base de datos local