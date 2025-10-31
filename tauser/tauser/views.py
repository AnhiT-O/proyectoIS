from datetime import timedelta
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils import timezone
from transacciones.models import Transaccion, Tauser, BilletesTauser, billetes_necesarios, procesar_transaccion, calcular_conversion, verificar_cambio_cotizacion
from transacciones.utils_2fa import is_2fa_enabled, create_transaction_token, validate_2fa_token
from .forms import TokenForm, IngresoForm, Token2FAForm
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
            else:
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
            print(request, 'No se reconoce la acción.')
            return redirect('caja_fuerte')
    else:
        form = IngresoForm()
    return render(request, 'caja_fuerte.html', {'form': form})

def ingreso_token(request):
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'aceptar':
            try:
                transaccion = Transaccion.objects.get(id=request.session.get('transaccion'))
            except Transaccion.DoesNotExist:
                messages.error(request, 'Transacción no encontrada.')
                return redirect('ingreso_token')
            # Si el 2FA está habilitado, devolver respuesta JSON para mostrar modal
            if is_2fa_enabled():
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'show_2fa': True,
                    'user_email': transaccion.usuario.email
                })
            return redirect('ingreso_billetes', codigo=transaccion.token)
        elif accion == 'cancelar':
            try:
                transaccion = Transaccion.objects.get(id=request.session.get('transaccion'))
            except Transaccion.DoesNotExist:
                messages.error(request, 'Transacción no encontrada.')
                return redirect('ingreso_token')
            transaccion.estado = 'Cancelada'
            transaccion.razon = 'Usuario cancela debido a cambios de cotización'
            transaccion.save()
            messages.info(request, 'Transacción cancelada.')
            return redirect('inicio')
        elif accion == 'enviar':
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
                    
                    if transaccion.medio_pago == 'Efectivo':
                        # Obtener email del usuario que procesó la transacción para notificaciones
                        email_usuario = getattr(transaccion.usuario, 'email', None)
                        cambios = verificar_cambio_cotizacion(transaccion, email_usuario)
                        if cambios and cambios.get('hay_cambios'):
                            datos_transaccion = calcular_conversion(transaccion.monto, transaccion.moneda, transaccion.tipo, transaccion.medio_pago, transaccion.medio_cobro, transaccion.cliente.segmento)
                            transaccion.precio_base = datos_transaccion['precio_base']
                            transaccion.cotizacion = datos_transaccion['cotizacion']
                            transaccion.beneficio_segmento = datos_transaccion['beneficio_segmento']
                            transaccion.porc_beneficio_segmento = datos_transaccion['porc_beneficio_segmento']
                            transaccion.recargo_pago = datos_transaccion['monto_recargo_pago']
                            transaccion.porc_recargo_pago = datos_transaccion['porc_recargo_pago']
                            transaccion.recargo_cobro = datos_transaccion['monto_recargo_cobro']
                            transaccion.porc_recargo_cobro = datos_transaccion['porc_recargo_cobro']
                            transaccion.redondeo_efectivo_monto = datos_transaccion['redondeo_efectivo_monto']
                            transaccion.redondeo_efectivo_precio_final = datos_transaccion['redondeo_efectivo_precio_final']
                            transaccion.monto_original = datos_transaccion['monto_original']
                            transaccion.monto = datos_transaccion['monto']
                            transaccion.precio_final = datos_transaccion['precio_final']
                            transaccion.save()
                            request.session['transaccion'] = transaccion.id
                            context = {
                                'cambios': cambios,
                                'transaccion': transaccion,
                                'email_usuario': email_usuario,
                                'enable_2fa': is_2fa_enabled(),
                                'user_email': transaccion.usuario.email if transaccion.usuario.email else ''
                            }
                            return render(request, 'ingreso_token.html', context)
                        
                        # Guardar la transacción en sesión para el 2FA
                        request.session['transaccion'] = transaccion.id
                        
                        # Si el 2FA está habilitado, renderizar template con flag para mostrar modal
                        if is_2fa_enabled():
                            context = {
                                'form': TokenForm(),
                                'enable_2fa': True,
                                'user_email': transaccion.usuario.email if transaccion.usuario.email else '',
                                'show_2fa_modal': True
                            }
                            return render(request, 'ingreso_token.html', context)
                        
                        return redirect('ingreso_billetes', codigo=codigo)
                    else:
                        messages.error(request, 'El token no corresponde a una operación de Tauser.')
                        return redirect('ingreso_token')
                else:
                    # Transacción ya procesada - aplicar 2FA si está habilitado
                    request.session['transaccion'] = transaccion.id
                    
                    if is_2fa_enabled():
                        context = {
                            'form': TokenForm(),
                            'enable_2fa': True,
                            'user_email': transaccion.usuario.email if transaccion.usuario.email else '',
                            'show_2fa_modal': True,
                            'transaccion_procesada': True  # Flag para indicar que ya está procesada
                        }
                        return render(request, 'ingreso_token.html', context)
                    
                    procesar_transaccion(transaccion, Tauser.objects.get(puerto=int(request.get_port())))
                    return redirect('exito', codigo=codigo)
    else:
        form = TokenForm()
    
    context = {
        'form': form,
        'enable_2fa': is_2fa_enabled(),
        'user_email': ''
    }
    return render(request, 'ingreso_token.html', context)

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
            messages.error(request, 'Billetes no reconocidos. Se devuelve lo ingresado.')
            return redirect('ingreso_billetes', codigo=codigo)
    else:
        form = IngresoForm()
    return render(request, 'ingreso_billetes.html', {'form': form, 'transaccion': transaccion})

def exito(request, codigo):
    transaccion = Transaccion.objects.get(token=codigo)
    return render(request, 'exito.html', {'transaccion': transaccion})

def verificar_2fa(request):
    """
    Vista para verificar el código 2FA antes de continuar con el ingreso de billetes.
    """
    # Verificar que el 2FA esté habilitado
    if not is_2fa_enabled():
        messages.error(request, 'El sistema de verificación 2FA no está habilitado.')
        return redirect('inicio')
    
    # Verificar que exista una transacción en sesión
    transaccion_id = request.session.get('transaccion')
    if not transaccion_id:
        messages.error(request, 'No hay transacción pendiente.')
        return redirect('ingreso_token')
    
    try:
        transaccion = Transaccion.objects.get(id=transaccion_id)
    except Transaccion.DoesNotExist:
        messages.error(request, 'Transacción no encontrada.')
        return redirect('ingreso_token')
    
    # Verificar que el usuario asociado a la transacción tenga email
    if not transaccion.usuario.email:
        messages.error(request, 'El usuario asociado a esta transacción no tiene email configurado.')
        return redirect('ingreso_token')
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'enviar_codigo':
            # Enviar el código 2FA al usuario
            transaccion_data = {
                'transaccion_id': transaccion.id,
                'cliente_id': transaccion.cliente.id,
                'tipo': transaccion.tipo,
                'monto': str(transaccion.monto),
                'moneda_id': transaccion.moneda.id,
                'precio_final': transaccion.precio_final,
                'medio_pago': transaccion.medio_pago,
                'medio_cobro': transaccion.medio_cobro
            }
            
            result = create_transaction_token(transaccion.usuario, transaccion_data)
            
            if result['success']:
                request.session['2fa_sent'] = True
                messages.success(request, f'Código de verificación enviado a {transaccion.usuario.email}')
            else:
                messages.error(request, result['message'])
            
            return redirect('verificar_2fa')
        
        elif accion == 'verificar':
            form = Token2FAForm(request.POST)
            if form.is_valid():
                codigo_2fa = form.cleaned_data['codigo_2fa']
                
                # Validar el código 2FA
                result = validate_2fa_token(transaccion.usuario, codigo_2fa)
                
                if result['success']:
                    messages.success(request, 'Código verificado correctamente.')
                    # Limpiar la flag de 2FA enviado
                    if '2fa_sent' in request.session:
                        del request.session['2fa_sent']
                    # Redirigir al ingreso de billetes
                    return redirect('ingreso_billetes', codigo=transaccion.token)
                else:
                    messages.error(request, result['message'])
                    return redirect('verificar_2fa')
        
        elif accion == 'cancelar':
            transaccion.estado = 'Cancelada'
            transaccion.razon = 'Usuario cancela la verificación 2FA'
            transaccion.save()
            # Limpiar la sesión
            if 'transaccion' in request.session:
                del request.session['transaccion']
            if '2fa_sent' in request.session:
                del request.session['2fa_sent']
            messages.info(request, 'Transacción cancelada.')
            return redirect('inicio')
    else:
        form = Token2FAForm()
    
    # Verificar si ya se envió el código
    codigo_enviado = request.session.get('2fa_sent', False)
    
    context = {
        'form': form,
        'transaccion': transaccion,
        'codigo_enviado': codigo_enviado,
        'usuario_email': transaccion.usuario.email
    }
    
    return render(request, 'verificar_2fa.html', context)