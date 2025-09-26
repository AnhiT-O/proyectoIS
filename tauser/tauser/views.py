from decimal import Decimal
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils import timezone
from monedas.services import LimiteService, Moneda
from clientes.models import Cliente
from transacciones.models import Recargos, Transaccion
from .forms import CodigoForm

def realizar_conversion(transaccion_id):
    precios = Moneda.objects.get(id=transaccion_id.moneda_id).get_precios_cliente(Cliente.objects.get(id=transaccion_id.cliente_id))
    if transaccion_id.tipo == 'compra':
        resultado = transaccion_id.monto * precios['precio_venta']
    else:
        resultado = transaccion_id.monto * precios['precio_compra']
        if transaccion_id.medio_cobro.startswith('Tigo Money'):
            resultado = resultado * (Decimal('1') - (Decimal(str(Recargos.objects.get(nombre='Tigo Money').recargo)) / Decimal('100')))
        elif transaccion_id.medio_cobro.startswith('Billetera Personal'):
            resultado = resultado * (Decimal('1') - (Decimal(str(Recargos.objects.get(nombre='Billetera Personal').recargo)) / Decimal('100')))
        elif transaccion_id.medio_cobro.startswith('Zimple'):
            resultado = resultado * (Decimal('1') - (Decimal(str(Recargos.objects.get(nombre='Zimple').recargo)) / Decimal('100')))
    return resultado

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
                if transaccion.medio_pago not in ['Efectivo', 'Cheque']:
                    messages.info(request, 'Cliente retira del tauser el dinero comprado. Transacción completada.')
                else:
                    messages.info(request, 'Cliente ingresa, luego retira del tauser en el momento. Transacción completada.')
                consumo = LimiteService.obtener_o_crear_consumo(transaccion.cliente_id)
                consumo.consumo_diario += realizar_conversion(transaccion)
                consumo.consumo_mensual += realizar_conversion(transaccion)
                print(realizar_conversion(transaccion))
                print(transaccion.monto)
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
                    consumo.consumo_diario += realizar_conversion(transaccion)
                    consumo.consumo_mensual += realizar_conversion(transaccion)
                    consumo.save()
                    transaccion.estado = 'Completada'
                    transaccion.token = None
                    transaccion.token_expiracion = None
                    transaccion.save()
                    return redirect('inicio')
                else:
                    messages.info(request, 'Cliente ingresa, el sistema automáticamente envía su dinero. Transacción completada.')
                    consumo = LimiteService.obtener_o_crear_consumo(transaccion.cliente_id)
                    consumo.consumo_diario += realizar_conversion(transaccion)
                    consumo.consumo_mensual += realizar_conversion(transaccion)
                    consumo.save()
                    transaccion.estado = 'Completada'
                    transaccion.token = None
                    transaccion.token_expiracion = None
                    transaccion.save()
                    return redirect('inicio')
    else:
        form = CodigoForm()
    return render(request, 'codigo.html', {'form': form})