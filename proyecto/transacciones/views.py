from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from monedas.models import Moneda
from .forms import SeleccionMonedaMontoForm
from decimal import Decimal


@login_required
def compra_monto_moneda(request):
    """
    Vista para el primer paso del proceso de compra de monedas.
    Permite al usuario seleccionar la moneda y el monto que desea comprar.
    """
    if request.method == 'POST':
        form = SeleccionMonedaMontoForm(request.POST)
        if form.is_valid():
            moneda = form.cleaned_data['moneda']
            monto = form.cleaned_data['monto_decimal']
            
            # Guardar los datos en la sesión
            request.session['compra_datos'] = {
                'moneda_id': moneda.id,
                'moneda_nombre': moneda.nombre,
                'moneda_simbolo': moneda.simbolo,
                'monto': str(monto),  # Convertir Decimal a string para serialización
                'paso_actual': 2
            }
            
            # Redireccionar al siguiente paso sin parámetros en la URL
            return redirect('transacciones:compra_medio_pago')
    else:
        form = SeleccionMonedaMontoForm()
    
    context = {
        'form': form,
        'paso_actual': 1,
        'total_pasos': 4,
        'titulo_paso': 'Selección de Moneda y Monto'
    }
    
    return render(request, 'transacciones/seleccion_moneda_monto.html', context)


def obtener_precio_moneda(request, moneda_id):
    """
    Vista AJAX para obtener el precio actualizado de una moneda específica.
    """
    try:
        moneda = Moneda.objects.get(id=moneda_id, activa=True)
        precio_compra = moneda.calcular_precio_compra()
        
        return JsonResponse({
            'success': True,
            'precio_compra': precio_compra,
            'simbolo': moneda.simbolo,
            'decimales': moneda.decimales
        })
    except Moneda.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Moneda no encontrada'
        })


# Vista para el segundo paso del proceso de compra
@login_required
def compra_medio_pago(request):
    """
    Vista para el segundo paso del proceso de compra.
    Recupera los datos de la sesión del primer paso.
    """
    # Verificar que existan datos del paso anterior
    compra_datos = request.session.get('compra_datos')
    if not compra_datos or compra_datos.get('paso_actual') != 2:
        messages.error(request, 'Debe completar el primer paso antes de continuar.')
        return redirect('transacciones:compra_monto_moneda')
    
    # Recuperar los datos de la sesión
    try:
        moneda = Moneda.objects.get(id=compra_datos['moneda_id'])
        monto = Decimal(compra_datos['monto'])
    except (Moneda.DoesNotExist, ValueError, KeyError):
        messages.error(request, 'Error al recuperar los datos. Reinicie el proceso.')
        return redirect('transacciones:compra_monto_moneda')
    
    context = {
        'moneda': moneda,
        'monto': monto,
        'paso_actual': 2,
        'total_pasos': 4,
        'titulo_paso': 'Selección de Medio de Pago'
    }
    
    return render(request, 'transacciones/en_construccion.html', {
        'mensaje': f'Segundo paso - Moneda: {moneda.nombre}, Monto: {monto}',
        'paso_actual': 2,
        'total_pasos': 4
    })
