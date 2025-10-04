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
                messages.success(request, f'Transacción encontrada')
                return redirect('inicio')
            except Transaccion.DoesNotExist:
                messages.error(request, 'Transacción no encontrada.')
    else:
        form = TokenForm()
    return render(request, 'ingreso_token.html', {'form': form})