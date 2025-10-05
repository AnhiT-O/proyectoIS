from datetime import timedelta
from decimal import Decimal
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils import timezone
from clientes.models import Cliente
from monedas.models import Moneda
from transacciones.models import Recargos, Transaccion
from .forms import TokenForm

def inicio(request):
    return render(request, 'inicio.html')

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
                    if transaccion.tipo == 'compra':
                        print('Ingreso de guaraníes')
                    else:
                        print('Ingreso de moneda extranjera')
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