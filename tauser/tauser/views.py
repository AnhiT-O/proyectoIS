from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils import timezone

from transacciones.models import Transaccion
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
                if transaccion.medio_pago == 'Efectivo':
                    return redirect('ingreso_billete')
                else:
                    return redirect('ingreso_cheque')
            else:
                return redirect('ingreso_billete')
    else:
        form = CodigoForm()
    return render(request, 'codigo.html', {'form': form})

def ingreso_billete(request):
    return render(request, 'ingreso_billete.html')

def ingreso_cheque(request):
    return render(request, 'ingreso_cheque.html')