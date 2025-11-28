from io import BytesIO
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from transacciones.models import Transaccion
from django.utils.timezone import localtime
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from datetime import datetime
from monedas.models import Moneda
from clientes.models import Cliente

@login_required
def view2(request):
    """Genera un PDF con tablas separadas para Compras y Ventas y resumen por moneda.
       Solo considera ganancias de transacciones completas y aplica descuentos por segmento de cliente."""
    
    user = request.user
    if not user.groups.filter(name='Administrador').exists():
        return HttpResponse('Acceso denegado', status=403)

    # Capturar filtros GET
    rango_fecha = request.GET.get('rango_fecha')
    fecha_desde_q = request.GET.get('fecha_desde')
    fecha_hasta_q = request.GET.get('fecha_hasta')
    moneda_id = request.GET.get('moneda')
    estado_filter = request.GET.get('estado')
    cliente_id = request.GET.get('cliente')
    tipo_filter = request.GET.get('tipo')
    
    # Diccionario de descuentos por segmento
    descuentos_segmento = {
        'minorista': 0.0,
        'corporativo': 5.0,
        'vip': 10.0,
    }

    # Obtener transacciones y aplicar filtros
    qs = Transaccion.objects.all().order_by('-fecha_hora')
    if rango_fecha:
        try:
            parts = [p.strip() for p in rango_fecha.split('-')]
            if len(parts) >= 2:
                f1 = parts[0]
                f2 = parts[1]
                try:
                    dt_desde = datetime.strptime(f1, '%Y-%m-%d')
                    dt_hasta = datetime.strptime(f2, '%Y-%m-%d')
                except Exception:
                    dt_desde = datetime.strptime(f1, '%d-%m-%Y')
                    dt_hasta = datetime.strptime(f2, '%d-%m-%Y')
                # incluir todo el día final
                dt_hasta = dt_hasta.replace(hour=23, minute=59, second=59)
                qs = qs.filter(fecha_hora__gte=dt_desde, fecha_hora__lte=dt_hasta)
        except Exception:
            pass
    else:
        if tipo_filter:
            qs = qs.filter(tipo__iexact=tipo_filter)
        if fecha_desde_q:
            try:
                dt_desde = datetime.strptime(fecha_desde_q, '%Y-%m-%d')
                qs = qs.filter(fecha_hora__gte=dt_desde)
            except Exception:
                try:
                    dt_desde = datetime.strptime(fecha_desde_q, '%d-%m-%Y')
                    qs = qs.filter(fecha_hora__gte=dt_desde)
                except Exception:
                    pass
        if fecha_hasta_q:
            try:
                dt_hasta = datetime.strptime(fecha_hasta_q, '%Y-%m-%d')
                dt_hasta = dt_hasta.replace(hour=23, minute=59, second=59)
                qs = qs.filter(fecha_hora__lte=dt_hasta)
            except Exception:
                try:
                    dt_hasta = datetime.strptime(fecha_hasta_q, '%d-%m-%Y')
                    dt_hasta = dt_hasta.replace(hour=23, minute=59, second=59)
                    qs = qs.filter(fecha_hora__lte=dt_hasta)
                except Exception:
                    pass
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

    # Construir resumen de filtros aplicados para imprimir en PDF
    applied = []
    if rango_fecha:
        applied.append(f"Rango: {rango_fecha}")
    else:
        if fecha_desde_q:
            applied.append(f"Desde: {fecha_desde_q}")
        if fecha_hasta_q:
            applied.append(f"Hasta: {fecha_hasta_q}")
    if moneda_id:
        try:
            m = Moneda.objects.filter(id=int(moneda_id)).first()
            applied.append(f"Moneda: {m.nombre if m else moneda_id}")
        except Exception:
            applied.append(f"Moneda: {moneda_id}")
    if cliente_id:
        try:
            c = Cliente.objects.filter(id=int(cliente_id)).first()
            applied.append(f"Cliente: {c.nombre if c else cliente_id}")
        except Exception:
            applied.append(f"Cliente: {cliente_id}")
    if tipo_filter:
        applied.append(f"Tipo: {tipo_filter}")
    if estado_filter:
        applied.append(f"Estado: {estado_filter}")

    compras_data = [['Fecha/Hora', 'Cliente', 'Operación', 'Moneda',
                     'Monto Origen', 'Monto Destino', 'Comisión Compra', 'Ganancia Compra', 'Descuento', 'Estado']]
    ventas_data = [['Fecha/Hora', 'Cliente', 'Operación', 'Moneda',
                    'Monto Origen', 'Monto Destino', 'Comisión Venta', 'Ganancia Venta', 'Descuento', 'Estado']]

    resumen_por_moneda = {}


    cell_style = ParagraphStyle(name='CellStyle', fontSize=8, leading=10)
    for t in qs:
        fecha = getattr(t, 'fecha_hora', getattr(t, 'fecha', None))
        
        if fecha:
            fecha = localtime(fecha)
            fecha_str =  fecha_str = Paragraph(f"{fecha.strftime('%d/%m/%Y')}<br/>{fecha.strftime('%H:%M:%S')}", cell_style)  
        else:  fecha_str = Paragraph("", cell_style)

        tipo = str(getattr(t, 'tipo', '')).lower()
        moneda_obj = getattr(t, 'moneda', None)
        moneda_nombre = getattr(moneda_obj, 'nombre', 'Sin moneda') if moneda_obj else 'Sin moneda'

        monto_origen = float(getattr(t, 'monto_origen', getattr(t, 'monto', 0)) or 0)
        monto_destino = float(getattr(t, 'monto_destino', getattr(t, 'precio_final', 0)) or 0)

        comision_compra = float(getattr(t, 'comision_compra',
                                       getattr(moneda_obj, 'comision_compra',
                                               getattr(moneda_obj, 'comision_comp', 0) or 0) or 0))
        comision_venta = float(getattr(t, 'comision_venta',
                                      getattr(moneda_obj, 'comision_venta',
                                              getattr(moneda_obj, 'comision_vta', 0) or 0) or 0))

        cliente_obj = getattr(t, 'cliente', None)
        cliente_nombre = getattr(cliente_obj, 'nombre', None) if cliente_obj else (getattr(t, 'usuario', None) and getattr(t.usuario, 'username', None)) or ''

        # Descuento: primero el de la transacción, si no existe usar el segmento del cliente
        porcentaje_descuento = getattr(t, 'porcentaje_descuento', None)
        if porcentaje_descuento is None:
            segmento = getattr(cliente_obj, 'segmento', 'minorista').lower() if cliente_obj else 'minorista'
            porcentaje_descuento = descuentos_segmento.get(segmento, 0.0)
        porcentaje_descuento = float(porcentaje_descuento or 0)

        estado = str(getattr(t, 'estado', '')).lower()
        # Solo calcular ganancias si la transacción está completa
        if estado == 'completa' or estado== 'confirmada':
            if tipo == 'compra':
                ganancia_comp = monto_origen * (comision_compra - (comision_compra * porcentaje_descuento / 100))
                ganancia_vta = 0
            elif tipo == 'venta':
                ganancia_vta = monto_origen * (comision_venta - (comision_venta * porcentaje_descuento / 100))
                ganancia_comp = 0
            else:
                ganancia_comp = ganancia_vta = 0
        else:
            ganancia_comp = ganancia_vta = 0

        ganancia_total_trans = ganancia_comp + ganancia_vta

        # Solo sumar al resumen si está completa
        if estado == 'completa' or estado== 'confirmada':
            resumen_por_moneda.setdefault(moneda_nombre, 0.0)
            resumen_por_moneda[moneda_nombre] += ganancia_total_trans

        # Construir fila según tipo
        if tipo == 'compra':
            row = [
                fecha_str, cliente_nombre, tipo, moneda_nombre,
                f"{monto_origen:,.2f}", f"{monto_destino:,.2f}",
                f"{comision_compra:,.2f}", f"{ganancia_comp:,.2f}",
                f"{porcentaje_descuento:.2f}%", getattr(t, 'estado', '') or ''
            ]
            compras_data.append(row)
        elif tipo == 'venta':
            row = [
                fecha_str, cliente_nombre, tipo, moneda_nombre,
                f"{monto_origen:,.2f}", f"{monto_destino:,.2f}",
                f"{comision_venta:,.2f}", f"{ganancia_vta:,.2f}",
                f"{porcentaje_descuento:.2f}%", getattr(t, 'estado', '') or ''
            ]
            ventas_data.append(row)

    # Crear PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            leftMargin=18, rightMargin=18, topMargin=18, bottomMargin=18)
    elements = []
    styles = getSampleStyleSheet()

    # Cabecera con resumen de filtros
    # (No se incluirá un bloque de filtros aplicados en el PDF)

    # Tabla de Compras
    if len(compras_data) > 1:
        elements.append(Paragraph('Compras', styles['Title']))
        elements.append(Spacer(1, 12))
        col_widths = [70, 80, 60, 90, 70, 90, 90, 90, 55, 50]
        compras_table = Table(compras_data, colWidths=col_widths, repeatRows=1)
        compras_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('ALIGN', (4,1), (5,-1), 'RIGHT'),
            ('ALIGN', (6,1), (7,-1), 'RIGHT'),
            ('ALIGN', (-2,1), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.25, colors.black),
        ]))
        elements.append(compras_table)
        elements.append(Spacer(1, 18))

    # Tabla de Ventas
    if len(ventas_data) > 1:
        elements.append(Paragraph('Ventas', styles['Title']))
        elements.append(Spacer(1, 12))
        col_widths = [70, 80, 60, 90, 70, 90, 90, 90, 55, 50]
        ventas_table = Table(ventas_data, colWidths=col_widths, repeatRows=1)
        ventas_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('ALIGN', (4,1), (5,-1), 'RIGHT'),
            ('ALIGN', (6,1), (7,-1), 'RIGHT'),
            ('ALIGN', (-2,1), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.25, colors.black),
        ]))
        elements.append(ventas_table)
        elements.append(Spacer(1, 18))

    # Resumen por Moneda
    elements.append(Paragraph('Resumen de Ganancias por Moneda', styles['Heading2']))
    elements.append(Spacer(1, 6))
    resumen_data = [['Moneda', 'Ganancia Total']]
    for moneda, gan in sorted(resumen_por_moneda.items()):
        resumen_data.append([moneda, f"{gan:,.2f}"])

    resumen_table = Table(resumen_data, colWidths=[150, 100])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0f0f0')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-1), 0.25, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    elements.append(resumen_table)

    # Generar PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="transacciones_reportes.pdf"'
    response.write(pdf)
    return response
