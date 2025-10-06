from datetime import timedelta
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils import timezone
from transacciones.models import Transaccion
from .forms import TokenForm, BilleteForm, CajaFuerteForm
from monedas.models import Denominacion
from transacciones.models import Tauser, BilletesTauser

def inicio(request):
    return render(request, 'inicio.html')

def caja_fuerte(request):
    if request.method == 'POST':
        form = CajaFuerteForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                archivo = form.cleaned_data['archivo']
                lineas = archivo.readlines()
                if lineas:
                    accion = lineas[0].decode('utf-8').strip()
                    for linea in lineas[1:]:
                        billetes = linea.decode('utf-8').strip().split('\t')
                        denominacion_valor = int(billetes[1])
                        tauser = Tauser.objects.get(puerto=int(request.get_port()))
                        cantidad = int(billetes[2])
                        if billetes[0] == 'Guaraní':
                            denominacion = Denominacion.objects.get(valor=denominacion_valor, moneda=None)
                        else:
                            denominacion = Denominacion.objects.get(valor=denominacion_valor, moneda__nombre=billetes[0])
                        if accion == 'Ingreso':
                            tauser_billete, creado = BilletesTauser.objects.get_or_create(denominacion=denominacion, tauser=tauser)
                            tauser_billete.cantidad += cantidad
                            tauser_billete.save()
                        else:
                            tauser_billete = BilletesTauser.objects.get(denominacion=denominacion, tauser=tauser)
                            if not tauser_billete or tauser_billete.cantidad < cantidad:
                                raise ValueError('No hay suficientes billetes para la extracción.')
                            tauser_billete.cantidad -= cantidad
                            tauser_billete.save()
                return redirect('inicio')
            except Exception as e:
                messages.error(request, f'Error al procesar el archivo: {e}')
                return redirect('caja_fuerte')
        else:
            messages.error(request, 'No se reconoce la acción.')
            return redirect('inicio')
    else:
        form = CajaFuerteForm()
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
                    messages.error(request, 'El token ha expirado.')
                    return redirect('ingreso_token')
                
                if transaccion.medio_pago == 'Cheque':
                    print('Ingreso de cheque')
                elif transaccion.medio_pago == 'Efectivo':
                    return redirect('ingreso_billetes', codigo=codigo)
                else:
                    messages.error(request, 'El token no corresponde a una operación de Tauser.')
                    return redirect('ingreso_token')
            else:
                if transaccion.tipo == 'compra':
                    print('Extracción de moneda extranjera')
                else:
                    print('Extracción de guaraníes')
    else:
        form = TokenForm()
    return render(request, 'ingreso_token.html', {'form': form})

def ingreso_billetes(request, codigo):
    if request.method == 'POST':
        form = BilleteForm(request.POST, request.FILES)
        if form.is_valid():
            print('Procesar billetes')
            return redirect('inicio')
        else:
            messages.error(request, 'Billete no reconocido.')
            return redirect('ingreso_billetes', codigo=codigo)
    else:
        try:
            transaccion = Transaccion.objects.get(token=codigo)
        except Transaccion.DoesNotExist:
            messages.error(request, 'Transacción no encontrada.')
            return redirect('ingreso_token')
        form = BilleteForm()
    return render(request, 'ingreso_billetes.html', {'form': form, 'transaccion': transaccion})