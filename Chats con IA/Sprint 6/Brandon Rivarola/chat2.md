losrivarola98: Error: get() returned more than one Denominacion -- it returned 6!

GitHub Copilot: El error ocurre porque `Denominacion.objects.get()` está devolviendo múltiples objetos cuando esperas solo uno. El problema está en estas líneas donde usas `moneda=None` o `moneda=moneda` sin especificar qué denominación específica quieres obtener.

Necesitas modificar la lógica para verificar si existe alguna denominación que no permita el redondeo, en lugar de intentar obtener una sola. Aquí está la corrección:

````python
if operacion == 'venta':
    if medio_pago == 'Efectivo':
        denominaciones_moneda = Denominacion.objects.filter(moneda=moneda)
        no_pago = any(no_redondeado(monto, denom) > 0 for denom in denominaciones_moneda)
    if medio_cobro == 'Efectivo':
        denominaciones_guaranies = Denominacion.objects.filter(moneda=None)
        no_cobro = any(no_redondeado(resultado['precio_final'], denom) > 0 for denom in denominaciones_guaranies)
else:
    if medio_pago == 'Efectivo':
        denominaciones_guaranies = Denominacion.objects.filter(moneda=None)
        no_pago = any(no_redondeado(resultado['precio_final'], denom) > 0 for denom in denominaciones_guaranies)
    if medio_cobro == 'Efectivo':
        denominaciones_moneda = Denominacion.objects.filter(moneda=moneda)
        no_cobro = any(no_redondeado(monto, denom) > 0 for denom in denominaciones_moneda)
````

**Explicación del cambio:**

1. Uso `filter()` en lugar de `get()` para obtener todas las denominaciones
2. Uso `any()` para verificar si alguna denominación tiene problemas de redondeo
3. Esto evita el error y verifica correctamente contra todas las denominaciones disponibles

losrivarola98: la funcion no_redondeado espera una lista en el segundo parámetro

GitHub Copilot: Entendido, si `no_redondeado` espera una lista de denominaciones, entonces debes pasar el queryset directamente. Aquí está la corrección:

````python
if operacion == 'venta':
    if medio_pago == 'Efectivo' and no_redondeado(monto, list(Denominacion.objects.filter(moneda=moneda))) > 0:
        no_pago = True
    if medio_cobro == 'Efectivo' and no_redondeado(resultado['precio_final'], list(Denominacion.objects.filter(moneda=None))) > 0:
        no_cobro = True
else:
    if medio_pago == 'Efectivo' and no_redondeado(resultado['precio_final'], list(Denominacion.objects.filter(moneda=None))) > 0:
        no_pago = True
    if medio_cobro == 'Efectivo' and no_redondeado(monto, list(Denominacion.objects.filter(moneda=moneda))) > 0:
        no_cobro = True
````

**Cambio realizado:**

- Convertí el queryset a lista usando `list()` para que la función `no_redondeado` reciba una lista de objetos `Denominacion` como segundo parámetro, tal como espera.

losrivarola98: Quiero obtener los valores de la columna 'valor' filtrando por 'moneda=moneda'

GitHub Copilot: Para obtener solo los valores de la columna 'valor' filtrando por moneda, usa `values_list`:

````python
list(Denominacion.objects.filter(moneda=moneda).values_list('valor', flat=True))
````

**Explicación:**

- `values_list('valor', flat=True)` obtiene solo los valores de la columna 'valor'
- `flat=True` devuelve una lista plana de valores en lugar de tuplas
- `list()` convierte el queryset a lista

Entonces tu código quedaría así:

````python
if operacion == 'venta':
    if medio_pago == 'Efectivo' and no_redondeado(monto, list(Denominacion.objects.filter(moneda=moneda).values_list('valor', flat=True))) > 0:
        no_pago = True
    if medio_cobro == 'Efectivo' and no_redondeado(resultado['precio_final'], list(Denominacion.objects.filter(moneda=None).values_list('valor', flat=True))) > 0:
        no_cobro = True
else:
    if medio_pago == 'Efectivo' and no_redondeado(resultado['precio_final'], list(Denominacion.objects.filter(moneda=None).values_list('valor', flat=True))) > 0:
        no_pago = True
    if medio_cobro == 'Efectivo' and no_redondeado(monto, list(Denominacion.objects.filter(moneda=moneda).values_list('valor', flat=True))) > 0:
        no_cobro = True
````

losrivarola98: hace falta list() ahí?

GitHub Copilot: No, `list()` no es estrictamente necesario si `no_redondeado` acepta cualquier iterable (como un queryset). Sin embargo, **es recomendable usarlo** porque:

1. **Evalúa la consulta inmediatamente**: evita múltiples accesos a la base de datos si la función itera varias veces sobre los valores
2. **Mayor claridad**: deja explícito que estás pasando una lista de valores
3. **Evita problemas**: algunos querysets pueden comportarse de forma inesperada si se iteran múltiples veces

**Sin `list()`:**
```python
Denominacion.objects.filter(moneda=moneda).values_list('valor', flat=True)
```
Esto devuelve un `ValuesListQuerySet` que es lazy (perezoso).

**Con `list()`:**
```python
list(Denominacion.objects.filter(moneda=moneda).values_list('valor', flat=True))
```
Esto devuelve una lista Python evaluada inmediatamente.

**Recomendación**: Mantén el `list()` a menos que sepas con certeza que `no_redondeado` solo itera una vez y está optimizado para querysets. Para mayor seguridad y claridad, déjalo como está.