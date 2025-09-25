from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils import timezone
from monedas.services import LimiteService
from transacciones.models import Recargos, Transaccion
from .forms import CodigoForm

def inicio(request):
    return render(request, 'inicio.html')

def codigo(request):
    if request.method == 'POST':
        form = CodigoForm(request.POST)
        if form.is_valid():
            codigo_ingresado = form.cleaned_data['codigo']
            try:
                transaccion = Transaccion.objects.get(token=codigo_ingresado)
                
                # Verificar si el token ha expirado
                if not transaccion.token_valido():
                    # Token expirado, eliminar la transacción
                    transaccion.delete()
                    messages.error(request, 'El código ha expirado. La transacción ha sido cancelada.')
                    return render(request, 'codigo.html', {'form': CodigoForm()})
                
            except Transaccion.DoesNotExist:
                messages.error(request, 'Código inválido.')
                return render(request, 'codigo.html', {'form': form})
            
            if transaccion.tipo == 'compra':
                messages.info(request, 'Cliente ingresa, luego retira del tauser en el momento. Transacción completada.')
                consumo = LimiteService.obtener_o_crear_consumo(transaccion.cliente_id)
                consumo.consumo_diario += transaccion.moneda.calcular_precio_compra(transaccion.monto)
                consumo.consumo_mensual += transaccion.moneda.calcular_precio_compra(transaccion.monto)
                consumo.save()
                transaccion.estado = 'Completada'
                transaccion.token = None
                transaccion.token_expiracion = None
                transaccion.save()
                return redirect('inicio')
            else:
                if transaccion.medio_cobro == 'Efectivo':
                    messages.info(request, 'Cliente ingresa, luego retira del tauser en el momento. Transacción completada.')
                    consumo = LimiteService.obtener_o_crear_consumo(transaccion.cliente_id)
                    consumo.consumo_diario += transaccion.moneda.calcular_precio_venta(transaccion.monto)
                    consumo.consumo_mensual += transaccion.moneda.calcular_precio_venta(transaccion.monto)
                    consumo.save()
                    transaccion.estado = 'Completada'
                    transaccion.token = None
                    transaccion.token_expiracion = None
                    transaccion.save()
                    return redirect('inicio')
                else:
                    if transaccion.medio_cobro.startswith('Billetera - Tigo Money'):
                        transaccion.monto -= transaccion.monto * (Recargos.objects.get(nombre='Tigo Money').recargo / 100)
                    elif transaccion.medio_cobro.startswith('Billetera - Billetera Personal'):
                        transaccion.monto -= transaccion.monto * (Recargos.objects.get(nombre='Billetera Personal').recargo / 100)
                    elif transaccion.medio_cobro.startswith('Billetera - Zimple'):
                        transaccion.monto -= transaccion.monto * (Recargos.objects.get(nombre='Zimple').recargo / 100)
                    messages.info(request, 'Cliente ingresa, el sistema automáticamente envía su dinero. Transacción completada.')
                    consumo = LimiteService.obtener_o_crear_consumo(transaccion.cliente_id)
                    consumo.consumo_diario += transaccion.moneda.calcular_precio_venta(transaccion.monto)
                    consumo.consumo_mensual += transaccion.moneda.calcular_precio_venta(transaccion.monto)
                    consumo.save()
                    transaccion.estado = 'Completada'
                    transaccion.token = None
                    transaccion.token_expiracion = None
                    transaccion.save()
                    return redirect('inicio')
    else:
        form = CodigoForm()
    return render(request, 'codigo.html', {'form': form})