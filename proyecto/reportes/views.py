from django.shortcuts import render
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth.decorators import login_required
from transacciones.models import Transaccion
from monedas.models import Moneda
from clientes.models import Cliente
from datetime import datetime, timedelta
from django.db.models import Sum, Q, Min, Max
from django.db import models
from collections import defaultdict


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

    # Filtros - soporte para nuevos parámetros de fecha separados
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    # Nuevo filtro unificado: rango de fechas en formato 'YYYY-MM-DD - YYYY-MM-DD'
    rango_fecha = request.GET.get('rango_fecha')
    
    # Nuevos parámetros de fecha separados (día, mes, año)
    dia_inicio = request.GET.get('dia_inicio')
    mes_inicio = request.GET.get('mes_inicio') 
    año_inicio = request.GET.get('año_inicio')
    dia_fin = request.GET.get('dia_fin')
    mes_fin = request.GET.get('mes_fin')
    año_fin = request.GET.get('año_fin')
    
    moneda_id = request.GET.get('moneda')
    estado_filter = request.GET.get('estado')
    cliente_id = request.GET.get('cliente')
    tipo_filter = request.GET.get('tipo')
    
    # Obtener rango de años disponibles para los selectores
    años_rango = []
    try:
        fechas_extremas = Transaccion.objects.aggregate(
            fecha_min=models.Min('fecha_hora'),
            fecha_max=models.Max('fecha_hora')
        )
        if fechas_extremas['fecha_min'] and fechas_extremas['fecha_max']:
            año_min = fechas_extremas['fecha_min'].year
            año_max = fechas_extremas['fecha_max'].year
            años_rango = list(range(año_min, año_max + 1))
    except Exception:
        # Fallback: últimos 5 años hasta el actual
        año_actual = datetime.now().year
        años_rango = list(range(año_actual - 4, año_actual + 1))
    
    # Generar listas para días y meses
    dias_lista = [f"{i:02d}" for i in range(1, 32)]  # 01, 02, ..., 31
    meses_lista = [f"{i:02d}" for i in range(1, 13)]  # 01, 02, ..., 12

    qs = Transaccion.objects.all().order_by('-fecha_hora')
    
    # Procesamiento de fechas separadas (día, mes, año)
    fecha_construida_desde = None
    fecha_construida_hasta = None
    
    if dia_inicio and mes_inicio and año_inicio:
        try:
            fecha_construida_desde = datetime(int(año_inicio), int(mes_inicio), int(dia_inicio))
        except (ValueError, TypeError):
            pass
    
    if dia_fin and mes_fin and año_fin:
        try:
            fecha_construida_hasta = datetime(int(año_fin), int(mes_fin), int(dia_fin))
            # Agregar 23:59:59 para incluir todo el día final
            fecha_construida_hasta = fecha_construida_hasta.replace(hour=23, minute=59, second=59, microsecond=999999)
        except (ValueError, TypeError):
            pass
    
    # Si se construyeron fechas a partir de los selectores, usarlas con prioridad
    if fecha_construida_desde and fecha_construida_hasta:
        qs = qs.filter(fecha_hora__gte=fecha_construida_desde, fecha_hora__lte=fecha_construida_hasta)
    elif rango_fecha:
        try:
            parts = [p.strip() for p in rango_fecha.split('-')]
            if len(parts) >= 2:
                # intentar YYYY-MM-DD primero, si falla intentar DD-MM-YYYY
                fecha1 = parts[0]
                fecha2 = parts[1]
                try:
                    dt_desde = datetime.strptime(fecha1, '%Y-%m-%d')
                    dt_hasta = datetime.strptime(fecha2, '%Y-%m-%d')
                except Exception:
                    dt_desde = datetime.strptime(fecha1, '%d-%m-%Y')
                    dt_hasta = datetime.strptime(fecha2, '%d-%m-%Y')
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
        moneda_simbolo = getattr(moneda_obj, 'simbolo', '') if moneda_obj else ''

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

        # Si cliente tiene segmento, intentar mapear por nombre a porcentajes definidos
        if cliente_obj is not None:
            segmento = getattr(cliente_obj, 'segmento', None)
            if segmento is not None:
                # obtener nombre del segmento si viene como objeto o string
                seg_name = None
                if hasattr(segmento, 'nombre'):
                    seg_name = getattr(segmento, 'nombre', None)
                elif isinstance(segmento, str):
                    seg_name = segmento
                else:
                    # intentar obtener nombre de objeto relacionado
                    try:
                        seg_obj = None
                        from clientes.models import Segmento
                        seg_obj = Segmento.objects.filter(pk=int(segmento)).first()
                        if seg_obj:
                            seg_name = getattr(seg_obj, 'nombre', None)
                    except Exception:
                        seg_name = None

                if seg_name:
                    segmento_nombre = str(seg_name)
                    sn = segmento_nombre.strip().lower()
                    # Mapear segmentos a porcentajes: minorista 0, corporativo 5, vip 10
                    mapping = {
                        'minorista': 0.0,
                        'corporativo': 5.0,
                        'vip': 10.0,
                    }
                    if sn in mapping:
                        porcentaje_descuento = mapping[sn]
                        beneficio_segmento = mapping[sn]

        # Priorizar el valor guardado en la transacción: 'porc_beneficio_segmento' o 'beneficio_segmento'
        trans_benef = getattr(t, 'porc_beneficio_segmento', None) or getattr(t, 'beneficio_segmento', None)
        if trans_benef is not None:
            try:
                porcentaje_descuento = float(trans_benef or 0)
                beneficio_segmento = trans_benef
            except Exception:
                pass

        # Si aún no se definió, fallback a campos genéricos en la transacción
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
            ganancia_vta = monto_origen * (comision_venta - (comision_venta * porcentaje_descuento /100))
        elif tipo == 'compra':
            comision_compra_val = comision_compra
            ganancia_comp = monto_origen * (comision_compra - (comision_compra * porcentaje_descuento / 100))

        # Solo se consideran ganancias si la transacción está completa o confirmada
        if not (estado and str(estado).lower() in ['completa', 'confirmada']):
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
            'moneda_simbolo': moneda_simbolo,
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
        'años_rango': años_rango,
        'dias_lista': dias_lista,
        'meses_lista': meses_lista,
        'f_fecha_desde': fecha_desde,
        'f_fecha_hasta': fecha_hasta,
        'f_fecha_rango': rango_fecha,
        'f_dia_inicio': dia_inicio,
        'f_mes_inicio': mes_inicio,
        'f_año_inicio': año_inicio,
        'f_dia_fin': dia_fin,
        'f_mes_fin': mes_fin,
        'f_año_fin': año_fin,
        'f_moneda': moneda_id,
        'f_estado': estado_filter,
        'f_tipo': tipo_filter,
        'f_cliente': cliente_id,
        'show_compra': show_compra,
        'show_venta': show_venta,
        'f_colspan': f_colspan,
    }
    return render(request, 'reportes/transacciones_reportes.html', context)


@login_required
def dashboard_ganancias(request):
    """
    Dashboard de ganancias con gráfico temporal.
    Acceso exclusivo para Administradores.
    Muestra por defecto las ganancias totales del último mes.
    """
    user = request.user
    if not user.groups.filter(name='Administrador').exists():
        return HttpResponseForbidden('Acceso denegado: requiere rol Administrador')
    
    monedas = Moneda.objects.all()
    
    context = {
        'monedas': monedas,
    }
    return render(request, 'reportes/dashboard_ganancias.html', context)


@login_required
def obtener_datos_ganancias(request):
    """
    API endpoint que devuelve datos de ganancias en formato JSON para el gráfico.
    Parámetros GET:
    - rango: 'semana', 'mes', '6meses', 'año'
    - moneda_id: ID de moneda específica (opcional, si no se envía devuelve total de todas)
    
    Retorna JSON con:
    - fechas: lista de fechas
    - ganancias: lista de ganancias por fecha
    - ganancia_total: suma total
    """
    user = request.user
    if not user.groups.filter(name='Administrador').exists():
        return JsonResponse({'error': 'Acceso denegado'}, status=403)
    
    # Obtener parámetros
    rango = request.GET.get('rango', 'hoy')
    moneda_id = request.GET.get('moneda_id', None)
    
    # Calcular fecha de inicio según el rango
    fecha_hasta = datetime.now()
    if rango == 'hoy':
        fecha_desde = fecha_hasta.replace(hour=0, minute=0, second=0, microsecond=0)
    elif rango == 'semana':
        fecha_desde = fecha_hasta - timedelta(days=7)
    elif rango == 'mes':
        fecha_desde = fecha_hasta - timedelta(days=30)
    elif rango == '6meses':
        fecha_desde = fecha_hasta - timedelta(days=180)
    elif rango == 'año':
        fecha_desde = fecha_hasta - timedelta(days=365)
    else:
        fecha_desde = fecha_hasta - timedelta(days=30)
    
    # Filtrar transacciones
    qs = Transaccion.objects.filter(
        fecha_hora__gte=fecha_desde,
        fecha_hora__lte=fecha_hasta
    ).filter(
        Q(estado__iexact='completa') | Q(estado__iexact='confirmada')
    ).order_by('fecha_hora')
    
    # Filtrar por moneda si se especifica
    if moneda_id:
        try:
            qs = qs.filter(moneda__id=int(moneda_id))
        except Exception:
            pass
    
    # Diccionario para agrupar ganancias por fecha
    ganancias_por_fecha = defaultdict(float)
    
    for t in qs:
        fecha = getattr(t, 'fecha_hora', getattr(t, 'fecha', None))
        if not fecha:
            continue
            
        # Agrupar por día
        fecha_str = fecha.strftime('%Y-%m-%d')
        
        tipo = getattr(t, 'tipo', '').lower()
        moneda_obj = getattr(t, 'moneda', None)
        
        monto_origen = getattr(t, 'monto_origen', None)
        if monto_origen is None:
            monto_origen = getattr(t, 'monto', 0)
        
        # Obtener comisiones
        comision_compra = getattr(t, 'comision_compra', None)
        comision_venta = getattr(t, 'comision_venta', None)
        if moneda_obj is not None:
            if not comision_compra:
                comision_compra = getattr(moneda_obj, 'comision_compra', getattr(moneda_obj, 'comision_comp', 0) or 0)
            if not comision_venta:
                comision_venta = getattr(moneda_obj, 'comision_venta', getattr(moneda_obj, 'comision_vta', 0) or 0)
        
        comision_compra = float(comision_compra or 0)
        comision_venta = float(comision_venta or 0)
        
        # Obtener descuento
        porcentaje_descuento = None
        cliente_obj = getattr(t, 'cliente', None)
        
        if cliente_obj is not None:
            segmento = getattr(cliente_obj, 'segmento', None)
            if segmento is not None:
                seg_name = None
                if hasattr(segmento, 'nombre'):
                    seg_name = getattr(segmento, 'nombre', None)
                elif isinstance(segmento, str):
                    seg_name = segmento
                
                if seg_name:
                    sn = str(seg_name).strip().lower()
                    mapping = {
                        'minorista': 0.0,
                        'corporativo': 5.0,
                        'vip': 10.0,
                    }
                    if sn in mapping:
                        porcentaje_descuento = mapping[sn]
        
        trans_benef = getattr(t, 'porc_beneficio_segmento', None) or getattr(t, 'beneficio_segmento', None)
        if trans_benef is not None:
            try:
                porcentaje_descuento = float(trans_benef or 0)
            except Exception:
                pass
        
        if porcentaje_descuento is None:
            porcentaje_descuento = float(getattr(t, 'porcentaje_descuento', None) or getattr(t, 'pordes', 0) or 0)
        
        try:
            monto_origen = float(monto_origen or 0)
        except Exception:
            monto_origen = 0.0
        
        # Calcular ganancia según tipo
        ganancia_trans = 0.0
        
        if tipo == 'venta':
            ganancia_trans = monto_origen * (comision_venta - (comision_venta * porcentaje_descuento / 100))
        elif tipo == 'compra':
            ganancia_trans = monto_origen * (comision_compra - (comision_compra * porcentaje_descuento / 100))
        
        ganancias_por_fecha[fecha_str] += ganancia_trans
    
    # Convertir a listas ordenadas
    fechas_ordenadas = sorted(ganancias_por_fecha.keys())
    ganancias_lista = [round(ganancias_por_fecha[f], 2) for f in fechas_ordenadas]
    ganancia_total = sum(ganancias_lista)
    
    # Formatear fechas para mejor visualización
    fechas_formateadas = []
    for f in fechas_ordenadas:
        try:
            dt = datetime.strptime(f, '%Y-%m-%d')
            fechas_formateadas.append(dt.strftime('%d/%m/%Y'))
        except Exception:
            fechas_formateadas.append(f)
    
    return JsonResponse({
        'fechas': fechas_formateadas,
        'ganancias': ganancias_lista,
        'ganancia_total': round(ganancia_total, 2),
        'moneda': 'Todas' if not moneda_id else Moneda.objects.filter(id=moneda_id).first().nombre if Moneda.objects.filter(id=moneda_id).exists() else 'Desconocida'
    })
