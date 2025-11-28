"""
Módulo de vistas para el sistema de reportes y análisis de ganancias.

Este módulo contiene las vistas necesarias para generar reportes financieros,
analizar transacciones y mostrar dashboards de ganancias para usuarios
con privilegios de administrador.

Funcionalidades principales:
- Generación de reportes de transacciones con filtros avanzados
- Dashboard interactivo de ganancias con visualización temporal
- APIs REST para datos de gráficos y análisis financiero
- Cálculo de ganancias basado en comisiones y descuentos por segmento

Autor: Sistema de Casa de Cambio
Fecha: Noviembre 2024
"""

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
    Genera un reporte completo de transacciones con análisis de ganancias.
    
    Esta vista proporciona un informe detallado de todas las transacciones del sistema,
    calculando las ganancias basadas en comisiones, descuentos por segmento de cliente
    y tipo de operación (compra/venta). Incluye múltiples opciones de filtrado y 
    separación de datos por tipo de transacción.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP con parámetros GET opcionales
            para filtrar por fechas, monedas, estados, clientes y segmentos.
    
    Returns:
        HttpResponse: Página renderizada con el reporte completo de transacciones
        HttpResponseForbidden: Si el usuario no tiene rol de Administrador
        
    Filtros disponibles:
        - dia_inicio/mes_inicio/año_inicio: Componentes de fecha de inicio
        - dia_fin/mes_fin/año_fin: Componentes de fecha de fin
        - moneda: ID o nombre de moneda
        - estado: Estado de transacción
        - cliente: ID de cliente
        - tipo: Tipo de transacción ('compra' o 'venta')
        - segmento: Segmento de cliente ('minorista', 'corporativo', 'vip')
        
    Fórmulas de cálculo:
        - Venta: monto_origen × (comisión_venta - descuento_segmento)
        - Compra: monto_origen × (comisión_compra - descuento_segmento)
        - Descuentos: Minorista 0%, Corporativo 5%, VIP 10%
    """
    user = request.user
    if not user.groups.filter(name='Administrador').exists():
        return HttpResponseForbidden('Acceso denegado: requiere rol Administrador')

    # Parámetros de fecha por componentes separados (día, mes, año)
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
    segmento_filter = request.GET.get('segmento')
    
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
    
    # Aplicar filtros de fecha si se construyeron correctamente
    if fecha_construida_desde and fecha_construida_hasta:
        qs = qs.filter(fecha_hora__gte=fecha_construida_desde, fecha_hora__lte=fecha_construida_hasta)
    
    # Aplicar filtro de tipo si se especifica
    if tipo_filter:
        qs = qs.filter(tipo__iexact=tipo_filter)
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
    if segmento_filter:
        qs = qs.filter(cliente__segmento__iexact=segmento_filter)

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

    # Obtener segmentos disponibles desde las opciones del modelo
    segmentos_disponibles = Cliente.SEGMENTO_CHOICES

    context = {
        'filas': filas,
        'filas_compra': filas_compra,
        'filas_venta': filas_venta,
        'total_ganancia': total_ganancia,
        'resumen_por_moneda': resumen_por_moneda,
        'monedas': Moneda.objects.all(),
        'clientes': Cliente.objects.all(),
        'segmentos': segmentos_disponibles,
        'años_rango': años_rango,
        'dias_lista': dias_lista,
        'meses_lista': meses_lista,
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
        'f_segmento': segmento_filter,
        'show_compra': show_compra,
        'show_venta': show_venta,
        'f_colspan': f_colspan,
    }
    return render(request, 'reportes/transacciones_reportes.html', context)


@login_required
def dashboard_ganancias(request):
    """
    Renderiza el dashboard principal de análisis de ganancias.
    
    Proporciona una interfaz interactiva para visualizar las ganancias del sistema
    mediante gráficos temporales y análisis por monedas. Los datos se cargan
    de forma asíncrona mediante APIs REST para optimizar el rendimiento.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP
    
    Returns:
        HttpResponse: Página del dashboard con gráficos interactivos
        HttpResponseForbidden: Si el usuario no tiene rol de Administrador
        
    Características:
        - Gráficos de líneas para evolución temporal de ganancias
        - Gráficos de torta para distribución por monedas
        - Filtros por período (hoy, semana, mes, 6 meses, año)
        - Análisis por moneda específica o global
        - Carga de datos asíncrona con Chart.js
        
    Note:
        Los datos se obtienen mediante las APIs obtener_datos_ganancias
        y obtener_desglose_ganancias para mejor rendimiento.
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
    API REST que proporciona datos de ganancias agregados por fecha para gráficos temporales.
    
    Endpoint utilizado por el dashboard para generar gráficos de líneas que muestran
    la evolución temporal de las ganancias. Los datos se agrupan por día y se pueden
    filtrar por período temporal y moneda específica.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP con parámetros GET:
            - rango: Período a analizar ('hoy', 'semana', 'mes', '6meses', 'año')
            - moneda_id: ID de moneda específica (opcional, incluye todas si se omite)
    
    Returns:
        JsonResponse: Datos en formato JSON con estructura:
            {
                "fechas": ["DD/MM/YYYY", ...],        # Fechas formateadas
                "ganancias": [123.45, ...],           # Ganancias por fecha
                "ganancia_total": 1234.56,            # Suma total del período
                "moneda": "Nombre de moneda"           # Moneda filtrada o "Todas"
            }
        JsonResponse con error 403: Si no tiene permisos de administrador
        
    Business Logic:
        - Solo considera transacciones con estado 'completa' o 'confirmada'
        - Aplica las mismas fórmulas de cálculo que transacciones_reportes
        - Agrupa resultados por fecha y los ordena cronológicamente
        - Formatea fechas para mejor visualización en gráficos
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

@login_required
def obtener_desglose_ganancias(request):
    """
    API REST que proporciona análisis detallado de ganancias por moneda y tipo de operación.
    
    Endpoint especializado para generar gráficos de torta (pie charts) y análisis
    comparativos entre diferentes monedas. Separa los datos por tipo de transacción
    (compra/venta) y calcula porcentajes relativos para cada segmento.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP con parámetros GET:
            - rango: Período temporal ('hoy', 'semana', 'mes', '6meses', 'año')
            - moneda_id: ID de moneda específica (opcional)
    
    Returns:
        JsonResponse: Datos estructurados para gráficos con formato:
            {
                "desglose": {
                    "venta": {
                        "labels": ["USD", "EUR", ...],      # Nombres de monedas
                        "percents": [45.5, 32.1, ...],     # Porcentajes relativos
                        "values": [1234.56, 890.12, ...]   # Valores absolutos
                    },
                    "compra": {
                        "labels": [...], "percents": [...], "values": [...]
                    },
                    "total": {
                        "labels": [...], "values": [...]    # Sin porcentajes
                    }
                },
                "ganancia_total": 5678.90,
                "moneda": "Todas"
            }
        JsonResponse con error 403: Si no tiene permisos de administrador
        
    Business Logic:
        - Separa ganancias por tipo de operación (compra/venta)
        - Calcula porcentajes relativos dentro de cada tipo
        - Utiliza las mismas fórmulas de cálculo que otras funciones del módulo
        - Solo considera transacciones completadas
    """
    user = request.user
    if not user.groups.filter(name='Administrador').exists():
        return JsonResponse({'error': 'Acceso denegado'}, status=403)

    rango = request.GET.get('rango', 'hoy')
    moneda_id = request.GET.get('moneda_id', None)

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

    qs = Transaccion.objects.filter(
        fecha_hora__gte=fecha_desde,
        fecha_hora__lte=fecha_hasta
    ).filter(
        Q(estado__iexact='completa') | Q(estado__iexact='confirmada')
    )

    if moneda_id:
        try:
            qs = qs.filter(moneda__id=int(moneda_id))
        except Exception:
            pass

    # Diccionarios para acumular por tipo de transacción
    ganancias_venta = defaultdict(float)
    ganancias_compra = defaultdict(float)

    for t in qs:
        tipo = getattr(t, 'tipo', '').lower()
        moneda_obj = getattr(t, 'moneda', None)
        if moneda_obj is None:
            continue
        moneda_nombre = getattr(moneda_obj, 'nombre', 'Desconocida')

        monto_origen = getattr(t, 'monto_origen', None)
        if monto_origen is None:
            monto_origen = getattr(t, 'monto', 0)
        try:
            monto_origen = float(monto_origen or 0)
        except:
            monto_origen = 0

        # Obtener comisiones
        comision_compra = getattr(t, 'comision_compra', getattr(moneda_obj, 'comision_compra', 0) or 0)
        comision_venta = getattr(t, 'comision_venta', getattr(moneda_obj, 'comision_venta', 0) or 0)
        comision_compra = float(comision_compra or 0)
        comision_venta = float(comision_venta or 0)

        # Descuento: intentar obtener desde segmento del cliente, luego campos en la transacción, luego fallback
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
                else:
                    try:
                        from clientes.models import Segmento
                        seg_obj = Segmento.objects.filter(pk=int(segmento)).first()
                        if seg_obj:
                            seg_name = getattr(seg_obj, 'nombre', None)
                    except Exception:
                        seg_name = None

                if seg_name:
                    sn = str(seg_name).strip().lower()
                    mapping = {
                        'minorista': 0.0,
                        'corporativo': 5.0,
                        'vip': 10.0,
                    }
                    if sn in mapping:
                        porcentaje_descuento = mapping[sn]

        # Priorizar valor guardado en la transacción si existe
        trans_benef = getattr(t, 'porc_beneficio_segmento', None) or getattr(t, 'beneficio_segmento', None)
        if trans_benef is not None:
            try:
                porcentaje_descuento = float(trans_benef or 0)
            except Exception:
                pass

        # Fallback a campos genéricos de la transacción
        if porcentaje_descuento is None:
            porcentaje_descuento = float(getattr(t, 'porcentaje_descuento', None) or getattr(t, 'pordes', 0) or 0)

        # Calcular ganancia según tipo
        ganancia_trans = 0.0
        if tipo == 'venta':
            ganancia_trans = monto_origen * (comision_venta - (comision_venta * porcentaje_descuento / 100))
            ganancias_venta[moneda_nombre] += ganancia_trans
        elif tipo == 'compra':
            ganancia_trans = monto_origen * (comision_compra - (comision_compra * porcentaje_descuento / 100))
            ganancias_compra[moneda_nombre] += ganancia_trans

    # Total por moneda
    monedas = set(list(ganancias_venta.keys()) + list(ganancias_compra.keys()))
    total_por_moneda = {m: round(ganancias_venta.get(m, 0)+ganancias_compra.get(m, 0), 2) for m in monedas}

    # Preparar listas para Chart.js
    def preparar_listas(dic):
        """Prepara listas desde un diccionario para uso en Chart.js.

        Args:
            dic (dict): mapa etiqueta->valor numérico.

        Returns:
            tuple: (labels, values, percents)
                - labels: lista de keys (ordenadas según inserción en el dict)
                - values: lista de values redondeados a 2 decimales
                - percents: lista de porcentajes relativos (0-100) calculados sobre la suma
        """
        labels = list(dic.keys())
        values = [round(dic[m], 2) for m in labels]
        total = sum(values)
        percents = [round(v / total * 100, 2) if total > 0 else 0 for v in values]
        return labels, values, percents

    labels_v, values_v, percents_v = preparar_listas(ganancias_venta)
    labels_c, values_c, percents_c = preparar_listas(ganancias_compra)
    labels_t, values_t, _ = preparar_listas(total_por_moneda)


    total_general = round(sum(total_por_moneda.values()), 2)
    moneda_actual = 'Todas'
    if moneda_id:
        try:
            m = Moneda.objects.filter(id=int(moneda_id)).first()
            if m:
                moneda_actual = m.nombre
            else:
                moneda_actual = 'Desconocida'
        except Exception:
            moneda_actual = 'Desconocida'

    return JsonResponse({
        'desglose': {
            'venta': {'labels': labels_v, 'percents': percents_v, 'values': values_v},
            'compra': {'labels': labels_c, 'percents': percents_c, 'values': values_c},
            'total': {'labels': labels_t, 'values': values_t}
        },
        'ganancia_total': total_general,
        'moneda': moneda_actual
    })

