from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from transacciones.models import Transaccion
from monedas.models import Moneda
from clientes.models import Cliente
from datetime import datetime


@login_required
def transacciones_reportes(request):
    """
    Informe de transacciones y cálculo de ganancias usando exclusivamente las fórmulas proporcionadas.
    Acceso reservado a usuarios con rol 'Administrador'.
    Se aceptan filtros GET: fecha_desde (YYYY-MM-DD), fecha_hasta (YYYY-MM-DD), moneda (id), estado, cliente (id).
    Reglas:
    - En venta: solo comisión y ganancia de venta.
    - En compra: solo comisión y ganancia de compra.
    - Descuento proviene del segmento del cliente (si existe).
    - Ganancia total se resume por moneda en resumen_por_moneda.
    """
    user = request.user
    if not user.groups.filter(name='Administrador').exists():
        return HttpResponseForbidden('Acceso denegado: requiere rol Administrador')

    # Filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    # Nuevo filtro unificado: rango de fechas en formato 'YYYY-MM-DD - YYYY-MM-DD'
    rango_fecha = request.GET.get('rango_fecha')
    moneda_id = request.GET.get('moneda')
    estado_filter = request.GET.get('estado')
    cliente_id = request.GET.get('cliente')
    tipo_filter = request.GET.get('tipo')

    qs = Transaccion.objects.all().order_by('-fecha_hora')
    # Si se proporciona rango_fecha, parsearlo y aplicar filtro, sino usar fecha_desde/fecha_hasta individuales
    if rango_fecha:
        try:
            parts = [p.strip() for p in rango_fecha.split('-')]
            if len(parts) >= 2:
                # permitir formatos con guion largo u otros, tomar los primeros dos
                dt_desde = datetime.strptime(parts[0], '%Y-%m-%d')
                dt_hasta = datetime.strptime(parts[1], '%Y-%m-%d')
                qs = qs.filter(fecha_hora__gte=dt_desde, fecha_hora__lte=dt_hasta)
        except Exception:
            # Si falla el parseo, no aplicar filtro por rango
            pass
    else:
        if tipo_filter:
            qs = qs.filter(tipo__iexact=tipo_filter)
        if fecha_desde:
            try:
                dt_desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
                qs = qs.filter(fecha_hora__gte=dt_desde)
            except Exception:
                pass
        if fecha_hasta:
            try:
                dt_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                qs = qs.filter(fecha_hora__lte=dt_hasta)
            except Exception:
                pass
    # Si no se usó rango_fecha y se pasó tipo_filter, ya fue aplicado arriba
    if moneda_id:
        try:
            qs = qs.filter(moneda__id=int(moneda_id))
        except Exception:
            qs = qs.filter(moneda__nombre__icontains=moneda_id)
    if estado_filter:
        qs = qs.filter(estado__iexact=estado_filter)
    if cliente_id:
        try:
            qs = qs.filter(cliente__id=int(cliente_id))
        except Exception:
            pass

    filas = []
    resumen_por_moneda = {}

    for t in qs:
        fecha = getattr(t, 'fecha_hora', getattr(t, 'fecha', None))
        tipo = getattr(t, 'tipo', '').lower()
        moneda_obj = getattr(t, 'moneda', None)
        moneda_nombre = getattr(moneda_obj, 'nombre', 'Sin moneda') if moneda_obj else 'Sin moneda'

        monto_origen = getattr(t, 'monto_origen', None)
        if monto_origen is None:
            monto_origen = getattr(t, 'monto', 0)
        monto_destino = getattr(t, 'monto_destino', None)
        if monto_destino is None:
            monto_destino = getattr(t, 'precio_final', 0)

        # obtener comisiones desde transacción o moneda
        comision_compra = getattr(t, 'comision_compra', None)
        comision_venta = getattr(t, 'comision_venta', None)
        if moneda_obj is not None:
            if not comision_compra:
                comision_compra = getattr(moneda_obj, 'comision_compra', getattr(moneda_obj, 'comision_comp', 0) or 0)
            if not comision_venta:
                comision_venta = getattr(moneda_obj, 'comision_venta', getattr(moneda_obj, 'comision_vta', 0) or 0)

        comision_compra = float(comision_compra or 0)
        comision_venta = float(comision_venta or 0)

        # (Se usan las comisiones tal como están en el registro: número directo)

        # descuento: prioridad segmento del cliente
        porcentaje_descuento = None
        cliente_obj = getattr(t, 'cliente', None)
        segmento_nombre = None
        beneficio_segmento = None
        if cliente_obj is not None:
            segmento = getattr(cliente_obj, 'segmento', None)
            if segmento is not None:
                # segmento puede ser un objeto con atributos, una cadena (nombre) o una PK
                if hasattr(segmento, 'porcentaje_descuento') or hasattr(segmento, 'pordes') or hasattr(segmento, 'porcentaje'):
                    porcentaje_descuento = getattr(segmento, 'porcentaje_descuento', None) or getattr(segmento, 'pordes', None) or getattr(segmento, 'porcentaje', None)
                    # intentar extraer nombre del segmento si está disponible
                    segmento_nombre = getattr(segmento, 'nombre', None) or getattr(segmento, 'nombre_segmento', None)
                    # intentar obtener beneficio del segmento
                    beneficio_segmento = getattr(segmento, 'beneficio_segmento', None) or getattr(segmento, 'beneficio', None)
                else:
                    # intentar buscar un objeto Segmento por nombre o id
                    try:
                        from clientes.models import Segmento
                        seg_obj = None
                        if isinstance(segmento, str):
                            seg_obj = Segmento.objects.filter(nombre__iexact=segmento).first()
                            if seg_obj:
                                segmento_nombre = getattr(seg_obj, 'nombre', None)
                                beneficio_segmento = getattr(seg_obj, 'beneficio_segmento', None) or getattr(seg_obj, 'beneficio', None)
                        else:
                            try:
                                seg_obj = Segmento.objects.filter(pk=int(segmento)).first()
                                if seg_obj:
                                    segmento_nombre = getattr(seg_obj, 'nombre', None)
                                    beneficio_segmento = getattr(seg_obj, 'beneficio_segmento', None) or getattr(seg_obj, 'beneficio', None)
                            except Exception:
                                seg_obj = None
                        if seg_obj:
                            porcentaje_descuento = getattr(seg_obj, 'porcentaje_descuento', None) or getattr(seg_obj, 'pordes', None) or getattr(seg_obj, 'porcentaje', None)
                    except Exception:
                        porcentaje_descuento = None
        # fallback a valor en la transacción o 0
        # Priorizar beneficio_segmento definido en la propia transacción si existe
        beneficio_segmento = getattr(t, 'beneficio_segmento', beneficio_segmento)
        if porcentaje_descuento is None:
            porcentaje_descuento = float(getattr(t, 'porcentaje_descuento', None) or getattr(t, 'pordes', 0) or 0)
        else:
            try:
                porcentaje_descuento = float(porcentaje_descuento or 0)
            except Exception:
                porcentaje_descuento = 0.0

        try:
            monto_origen = float(monto_origen or 0)
        except Exception:
            monto_origen = 0.0
        try:
            monto_destino = float(monto_destino or 0)
        except Exception:
            monto_destino = 0.0

        # Obtener estado antes de calcular ganancias
        estado = getattr(t, 'estado', None)

        # según tipo, calcular solo la ganancia aplicable
        ganancia_comp = 0.0
        ganancia_vta = 0.0
        comision_compra_val = 0.0
        comision_venta_val = 0.0

        if tipo == 'venta':
            # usar comision_venta y monto_destino (comision como número directo)
            comision_venta_val = comision_venta
            ganancia_vta = monto_destino * (comision_venta - (comision_venta * porcentaje_descuento / 100))
        elif tipo == 'compra':
            comision_compra_val = comision_compra
            ganancia_comp = monto_origen * (comision_compra - (comision_compra * porcentaje_descuento / 100))

        # Solo se consideran ganancias si la transacción está completa
        if not (estado and str(estado).lower() == 'completa'):
            ganancia_comp = 0.0
            ganancia_vta = 0.0

        ganancia_total_trans = ganancia_comp + ganancia_vta
        # acumular resumen por moneda
        resumen_por_moneda.setdefault(moneda_nombre, 0.0)
        resumen_por_moneda[moneda_nombre] += ganancia_total_trans

        # determinar cliente/actor
        cliente_nombre = None
        if cliente_obj is not None:
            cliente_nombre = getattr(cliente_obj, 'nombre', None) or str(cliente_obj)
        elif hasattr(t, 'usuario') and getattr(t, 'usuario') is not None:
            usuario_obj = getattr(t, 'usuario')
            cliente_nombre = getattr(usuario_obj, 'nombre_completo', None) or getattr(usuario_obj, 'username', None) or str(usuario_obj)

        estado = getattr(t, 'estado', None)

        # Mostrar descuento derivado del segmento del cliente si existe (display)
        porcentaje_descuento_display = porcentaje_descuento

        filas.append({
             'fecha': fecha,
             'tipo_transaccion': tipo,
             'moneda': moneda_nombre,
             'monto_origen': monto_origen,
             'monto_destino': monto_destino,
             'comision_compra': comision_compra_val,
             'comision_venta': comision_venta_val,
             'porcentaje_descuento': porcentaje_descuento,
             'porcentaje_descuento_display': porcentaje_descuento_display,
             'segmento': segmento_nombre,
             'beneficio_segmento': beneficio_segmento,
             'ganancia_comp': ganancia_comp,
             'ganancia_vta': ganancia_vta,
             'cliente': cliente_nombre,
             'estado': estado,
         })

    total_ganancia = sum(resumen_por_moneda.values())

    # Separar por tipo para renderear tablas independientes
    filas_compra = [f for f in filas if f['tipo_transaccion'] == 'compra']
    filas_venta = [f for f in filas if f['tipo_transaccion'] == 'venta']

    # Determinar si mostrar columnas de compra/venta en cabecera
    show_compra = len(filas_compra) > 0
    show_venta = len(filas_venta) > 0

    # Calcular colspan para el mensaje vacío: columnas fijas = 5 (Fecha, Cliente, Operación, Moneda, Monto, %Descuento, Estado) ajustado por cada tabla
    f_colspan = 5 + (2 if show_compra else 0) + 2  # kept fallback, template uses per-table colspan separately

    context = {
        'filas': filas,
        'filas_compra': filas_compra,
        'filas_venta': filas_venta,
        'total_ganancia': total_ganancia,
        'resumen_por_moneda': resumen_por_moneda,
        'monedas': Moneda.objects.all(),
        'clientes': Cliente.objects.all(),
        'f_fecha_desde': fecha_desde,
        'f_fecha_hasta': fecha_hasta,
        'f_fecha_rango': rango_fecha,
        'f_moneda': moneda_id,
        'f_estado': estado_filter,
        'f_tipo': tipo_filter,
        'f_cliente': cliente_id,
        'show_compra': show_compra,
        'show_venta': show_venta,
        'f_colspan': f_colspan,
    }
    return render(request, 'reportes/transacciones_reportes.html', context)
