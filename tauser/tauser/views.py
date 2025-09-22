from django.shortcuts import render
from .forms import CodigoForm

def inicio(request):
    return render(request, 'inicio.html')

def codigo(request):
    if request.method == 'POST':
        form = CodigoForm(request.POST)
        if form.is_valid():
            codigo_ingresado = form.cleaned_data['codigo']
            # Aquí puedes agregar la lógica para verificar el código
            # Por simplicidad, asumimos que cualquier código es válido
            return render(request, 'codigo_exitoso.html', {'codigo': codigo_ingresado})
    else:
        form = CodigoForm()
    return render(request, 'codigo.html', {'form': form})