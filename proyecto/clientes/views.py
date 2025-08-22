from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Cliente
from .forms import ClienteForm

def es_administrador(user):
    return user.groups.filter(name='administrador').exists()

@login_required
@user_passes_test(es_administrador)
def cliente_crear(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, 'Cliente creado exitosamente.')
            return redirect('clientes:cliente_detalle', pk=cliente.pk)
    else:
        form = ClienteForm()
    return render(request, 'clientes/cliente_form.html', {'form': form})

@login_required
@user_passes_test(es_administrador)
def cliente_lista(request):
    clientes = Cliente.objects.all()
    return render(request, 'clientes/cliente_lista.html', {'clientes': clientes})

@login_required
@user_passes_test(es_administrador)
def cliente_detalle(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, 'clientes/cliente_detalle.html', {'cliente': cliente})

@login_required
@user_passes_test(es_administrador)
def cliente_editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado exitosamente.')
            return redirect('clientes:cliente_detalle', pk=cliente.pk)
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'clientes/cliente_form.html', {'form': form, 'cliente': cliente})

@login_required
@user_passes_test(es_administrador)
def cliente_eliminar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Cliente eliminado exitosamente.')
        return redirect('clientes:cliente_lista')
    return render(request, 'clientes/cliente_confirmar_eliminar.html', {'cliente': cliente})