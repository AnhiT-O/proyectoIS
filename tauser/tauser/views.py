from datetime import timedelta
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils import timezone
from transacciones.models import Transaccion, Tauser, BilletesTauser, Cheque, billetes_necesarios, leer_cheque, procesar_transaccion
from .forms import TokenForm, IngresoForm
from monedas.models import Denominacion

def inicio(request):
    return render(request, 'inicio.html')

def caja_fuerte(request):
    if request.method == 'POST':
        form = IngresoForm(request.POST, request.FILES)
        if form.is_valid():
            accion = None
            billetes = []
            valores = []
            cantidades = []
            try:
                archivo = form.cleaned_data['archivo']
                lineas = archivo.readlines()
                if lineas:
                    accion = lineas[0].decode('utf-8').strip()
                    for linea in lineas[1:]:
                        lectura_billetes = linea.decode('utf-8').strip().split('\t')
                        billetes.append(lectura_billetes[0])
                        valores.append(int(lectura_billetes[1]))
                        cantidades.append(int(lectura_billetes[2]))
            except Exception as e:
                print(e)
                return redirect('caja_fuerte')
            tauser = Tauser.objects.get(puerto=int(request.get_port()))
            if accion == 'Ingreso':
                for i in range(len(billetes)):
                    try:
                        if billetes[i] == 'Guaraní':
                            denominacion = Denominacion.objects.get(valor=valores[i], moneda=None)
                        else:
                            denominacion = Denominacion.objects.get(valor=valores[i], moneda__nombre=billetes[i])
                    except Denominacion.DoesNotExist:
                        print(f'La denominación {billetes[i]} {valores[i]} no se reconoce.')
                    tauser_billete, creado = BilletesTauser.objects.get_or_create(denominacion=denominacion, tauser=tauser)
                    tauser_billete.cantidad += cantidades[i]
                    tauser_billete.save()
                    print(f'Se han ingresado {cantidades[i]} billetes de {billetes[i]} {valores[i]}')
            elif accion == 'Extracción':
                for i in range(len(billetes)):
                    try:
                        if billetes[i] == 'Guaraní':
                            denominacion = Denominacion.objects.get(valor=valores[i], moneda=None)
                        else:
                            denominacion = Denominacion.objects.get(valor=valores[i], moneda__nombre=billetes[i])
                    except Denominacion.DoesNotExist:
                        print(f'La denominación {billetes[i]} {valores[i]} no se reconoce.')
                        return redirect('caja_fuerte')
                    try:
                        tauser_billete = BilletesTauser.objects.get(denominacion=denominacion, tauser=tauser)
                    except BilletesTauser.DoesNotExist:
                        tauser_billete = None
                    if not tauser_billete or tauser_billete.cantidad < cantidades[i]:
                        print(f'No hay suficientes billetes de {billetes[i]} {valores[i]} para la extracción.')
                        return redirect('caja_fuerte')
                for i in range(len(billetes)):
                    if billetes[i] == 'Guaraní':
                        denominacion = Denominacion.objects.get(valor=valores[i], moneda=None)
                    else:
                        denominacion = Denominacion.objects.get(valor=valores[i], moneda__nombre=billetes[i])
                    tauser_billete = BilletesTauser.objects.get(denominacion=denominacion, tauser=tauser)
                    tauser_billete.cantidad -= cantidades[i]
                    tauser_billete.save()
                    print(f'Se han extraído {cantidades[i]} billetes de {billetes[i]} {valores[i]}')
            else:
                cantidad = Cheque.objects.filter(tauser=tauser).count()
                if cantidad == 0:
                    print('No hay cheques para extraer.')
                    return redirect('caja_fuerte')
                total = sum(cheque.monto for cheque in Cheque.objects.filter(tauser=tauser))
                print(f'Se ha extraído todos los cheques ({cantidad}) del tauser. Total: Gs. {total}.')
                Cheque.objects.filter(tauser=tauser).delete()
        else:
            print(request, 'No se reconoce la acción.')
            return redirect('caja_fuerte')
    else:
        form = IngresoForm()
    return render(request, 'caja_fuerte.html', {'form': form})

def ingreso_token(request):
    if request.method == 'POST':
        form = TokenForm(request.POST)
        if form.is_valid():
            codigo = form.cleaned_data['codigo']
            try:
                transaccion = Transaccion.objects.get(token=codigo)
            except Transaccion.DoesNotExist:
                messages.error(request, 'Transacción no encontrada.')
                return redirect('ingreso_token')
            
            if transaccion.estado == 'Cancelada':
                messages.error(request, 'Este token corresponde a una transacción ya cancelada.')
                return redirect('ingreso_token')
            
            if transaccion.estado == 'Completa':
                messages.error(request, 'Este token corresponde a una transacción ya completada.')
                return redirect('ingreso_token')
            
            if transaccion.estado == 'Pendiente':
                if transaccion.fecha_hora < timezone.now() - timedelta(minutes=5):
                    transaccion.estado = 'Cancelada'
                    transaccion.razon = 'Expira el tiempo para confirmar la transacción'
                    transaccion.save()
                    if transaccion.pagado > 0:
                        messages.info(request, 'El token ha expirado. Contacta a soporte para el reembolso de lo pagado.')
                    else:
                        messages.error(request, 'El token ha expirado.')
                    return redirect('ingreso_token')
                
                if transaccion.medio_pago == 'Cheque':
                    return redirect('ingreso_cheque', codigo=codigo)
                elif transaccion.medio_pago == 'Efectivo':
                    return redirect('ingreso_billetes', codigo=codigo)
                else:
                    messages.error(request, 'El token no corresponde a una operación de Tauser.')
                    return redirect('ingreso_token')
            else:
                procesar_transaccion(transaccion, Tauser.objects.get(puerto=int(request.get_port())))
                return redirect('exito', codigo=codigo)
    else:
        form = TokenForm()
    return render(request, 'ingreso_token.html', {'form': form})

def ingreso_cheque(request, codigo):
    try:
        transaccion = Transaccion.objects.get(token=codigo)
    except Transaccion.DoesNotExist:
        messages.error(request, 'Transacción no encontrada.')
        return redirect('ingreso_token')
    if request.method == 'POST':
        form = IngresoForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = form.cleaned_data['archivo']
            lineas = archivo.readlines()
            lineas = [linea.decode('utf-8').strip() for linea in lineas]
            info_cheque = leer_cheque(lineas)
            if info_cheque:
                if transaccion.precio_final == info_cheque['monto']:
                    transaccion.pagado = info_cheque['monto']
                    transaccion.fecha_hora = timezone.now()
                    transaccion.save()
                    tauser = Tauser.objects.get(puerto=int(request.get_port()))
                    Cheque.objects.create(
                        tauser=tauser,
                        monto=info_cheque['monto'],
                        firma=info_cheque['firma']
                    )
                    procesar_transaccion(transaccion, tauser)
                    return redirect('exito', codigo=codigo)
                else:
                    messages.error(request, f'El monto del cheque (Gs. {monto:,.0f}'.replace(",", ".") + f') no coincide con el monto a pagar (Gs. {transaccion.precio_final:,.0f}'.replace(",", ".") + '). Se devuelve lo ingresado.')
                    return redirect('ingreso_cheque', codigo=codigo)
            else:
                messages.error(request, 'Cheque no válido. Intente nuevamente.')
                return redirect('ingreso_cheque', codigo=codigo)
    else:
        form = IngresoForm()
    return render(request, 'ingreso_cheque.html', {'form': form, 'transaccion': transaccion})

def ingreso_billetes(request, codigo):
    try:
        transaccion = Transaccion.objects.get(token=codigo)
    except Transaccion.DoesNotExist:
        messages.error(request, 'Transacción no encontrada.')
        return redirect('ingreso_token')
    if request.method == 'POST':
        form = IngresoForm(request.POST, request.FILES)
        if form.is_valid():
            billetes = []
            valores = []
            cantidades = []
            try:
                archivo = form.cleaned_data['archivo']
                lineas = archivo.readlines()
                if lineas:
                    for linea in lineas:
                        lectura_billetes = linea.decode('utf-8').strip().split('\t')
                        billetes.append(lectura_billetes[0])
                        valores.append(int(lectura_billetes[1]))
                        cantidades.append(int(lectura_billetes[2]))
            except Exception as e:
                messages.error(request, 'Billetes no reconocidos. Se devuelve lo ingresado.')
                print(e)
                return redirect('ingreso_billetes', codigo=codigo)
            tauser = Tauser.objects.get(puerto=int(request.get_port()))
            if transaccion.tipo == 'compra':
                for i in range(len(billetes)):
                    if billetes[i] != 'Guaraní':
                        messages.error(request, 'Solo se aceptan billetes en Guaraníes para compras. Se devuelve lo ingresado.')
                        return redirect('ingreso_billetes', codigo=codigo)
                    if valores[i] not in [den.valor for den in Denominacion.objects.filter(moneda=None)]:
                        messages.error(request, f'La denominación {valores[i]} no se reconoce. Se devuelve lo ingresado.')
                        return redirect('ingreso_billetes', codigo=codigo)
                total = 0
                for i in range(len(billetes)):
                    total += valores[i] * cantidades[i]
                if total > transaccion.precio_final - transaccion.pagado:
                    v_denominaciones = list(Denominacion.objects.filter(moneda=None).order_by('valor').values_list('valor', flat=True))
                    v_cantidades_qs = BilletesTauser.objects.filter(denominacion__moneda=None, tauser=tauser).order_by('denominacion__valor')
                    v_cantidades = {b.denominacion.valor: b.cantidad for b in v_cantidades_qs}
                    vuelto = billetes_necesarios(total - transaccion.precio_final, v_denominaciones, v_cantidades)
                    if not vuelto:
                        messages.error(request, 'No hay billetes suficientes para dar el vuelto. Se devuelve lo ingresado.')
                        return redirect('ingreso_billetes', codigo=codigo)
                for i in range(len(billetes)):
                    denominacion = Denominacion.objects.get(valor=valores[i], moneda=None)
                    tauser_billete, creado = BilletesTauser.objects.get_or_create(denominacion=denominacion, tauser=tauser)
                    tauser_billete.cantidad += cantidades[i]
                    tauser_billete.save()
                    transaccion.pagado += valores[i] * cantidades[i]
                    transaccion.fecha_hora = timezone.now()
                    transaccion.save()
                if transaccion.pagado < transaccion.precio_final:
                    messages.warning(request, f'Se ha ingresado Gs. {transaccion.pagado:,.0f}'.replace(",", ".") + ',' + f' aún faltan Gs. {transaccion.precio_final - transaccion.pagado:,.0f}'.replace(",", "."))
                    return redirect('ingreso_billetes', codigo=codigo)
                elif transaccion.pagado > transaccion.precio_final:
                    v_denominaciones = list(Denominacion.objects.filter(moneda=None).order_by('valor').values_list('valor', flat=True))
                    v_cantidades_qs = BilletesTauser.objects.filter(denominacion__moneda=None, tauser=tauser).order_by('denominacion__valor')
                    v_cantidades = {b.denominacion.valor: b.cantidad for b in v_cantidades_qs}
                    vuelto = billetes_necesarios(total - transaccion.precio_final, v_denominaciones, v_cantidades)
                    for valor, cantidad in vuelto.items():
                        denominacion = Denominacion.objects.get(valor=valor, moneda=None)
                        tauser_billete = BilletesTauser.objects.get(denominacion=denominacion, tauser=tauser)
                        tauser_billete.cantidad -= cantidad
                        tauser_billete.save()
                    messages.success(request, f'Tu vuelto es Gs. {(transaccion.pagado - transaccion.precio_final):,.0f}'.replace(",", ".") + '. Retiralo.')
                    procesar_transaccion(transaccion, tauser)
                    return redirect('exito', codigo=codigo)
                else:
                    procesar_transaccion(transaccion, tauser)
                    return redirect('exito', codigo=codigo)
            else:
                for i in range(len(billetes)):
                    if billetes[i] != transaccion.moneda.nombre:
                        messages.error(request, f'Solo se aceptan billetes de {transaccion.moneda.nombre} para ventas. Se devuelve lo ingresado.')
                        return redirect('ingreso_billetes', codigo=codigo)
                    if valores[i] not in [den.valor for den in Denominacion.objects.filter(moneda=transaccion.moneda)]:
                        messages.error(request, f'La denominación {valores[i]} no se reconoce. Se devuelve lo ingresado.')
                        return redirect('ingreso_billetes', codigo=codigo)
                total = 0
                for i in range(len(billetes)):
                    total += valores[i] * cantidades[i]
                if total > transaccion.monto - transaccion.pagado:
                    v_denominaciones = list(Denominacion.objects.filter(moneda=transaccion.moneda).order_by('valor').values_list('valor', flat=True))
                    v_cantidades_qs = BilletesTauser.objects.filter(denominacion__moneda=transaccion.moneda, tauser=tauser).order_by('denominacion__valor')
                    v_cantidades = {b.denominacion.valor: b.cantidad for b in v_cantidades_qs}
                    vuelto = billetes_necesarios(int(total - transaccion.monto), v_denominaciones, v_cantidades)
                    if not vuelto:
                        messages.error(request, 'No hay billetes suficientes para dar el vuelto. Se devuelve lo ingresado.')
                        return redirect('ingreso_billetes', codigo=codigo)
                for i in range(len(billetes)):
                    denominacion = Denominacion.objects.get(valor=valores[i], moneda__nombre=billetes[i])
                    tauser_billete, creado = BilletesTauser.objects.get_or_create(denominacion=denominacion, tauser=tauser)
                    tauser_billete.cantidad += cantidades[i]
                    tauser_billete.save()
                    transaccion.pagado += valores[i] * cantidades[i]
                    transaccion.fecha_hora = timezone.now()
                    transaccion.save()
                if transaccion.pagado < transaccion.monto:
                    messages.warning(request, f'Se ha ingresado {transaccion.pagado:,.0f}'.replace(",", ".") + f' {transaccion.moneda.simbolo},' + f' aún faltan {transaccion.monto - transaccion.pagado:,.0f}'.replace(",", ".") + f' {transaccion.moneda.simbolo}')
                    return redirect('ingreso_billetes', codigo=codigo)
                elif transaccion.pagado > transaccion.monto:
                    v_denominaciones = list(Denominacion.objects.filter(moneda=transaccion.moneda).order_by('valor').values_list('valor', flat=True))
                    v_cantidades_qs = BilletesTauser.objects.filter(denominacion__moneda=transaccion.moneda, tauser=tauser).order_by('denominacion__valor')
                    v_cantidades = {b.denominacion.valor: b.cantidad for b in v_cantidades_qs}
                    vuelto = billetes_necesarios(int(transaccion.pagado - transaccion.monto), v_denominaciones, v_cantidades)
                    for valor, cantidad in vuelto.items():
                        denominacion = Denominacion.objects.get(valor=valor, moneda=transaccion.moneda)
                        tauser_billete = BilletesTauser.objects.get(denominacion=denominacion, tauser=tauser)
                        tauser_billete.cantidad -= cantidad
                        tauser_billete.save()
                    messages.success(request, f'Tu vuelto es {(transaccion.pagado - transaccion.monto):,.0f}'.replace(",", ".") + f' {transaccion.moneda.simbolo}. Retiralo.')
                    procesar_transaccion(transaccion, tauser)
                    return redirect('exito', codigo=codigo)
                else:
                    procesar_transaccion(transaccion, tauser)
                    return redirect('exito', codigo=codigo)
        else:
            print(request, 'Billetes no reconocidos. Se devuelve lo ingresado.')
            return redirect('ingreso_billetes', codigo=codigo)
    else:
        form = IngresoForm()
    return render(request, 'ingreso_billetes.html', {'form': form, 'transaccion': transaccion})

def exito(request, codigo):
    transaccion = Transaccion.objects.get(token=codigo)
    return render(request, 'exito.html', {'transaccion': transaccion})