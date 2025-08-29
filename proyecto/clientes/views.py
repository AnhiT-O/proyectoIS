from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.db.models import Q
from .models import Cliente
from .forms import ClienteForm, CambiarCategoriaForm
@login_required
@permission_required('clientes.gestion', raise_exception=True)
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
@permission_required('clientes.gestion', raise_exception=True)
def cliente_lista(request):
    # Obtener todos los clientes para verificar si hay alguno
    todos_los_clientes = Cliente.objects.all()
    
    # Obtener clientes para mostrar (con filtros aplicados)
    clientes = todos_los_clientes
    
    # Manejar búsqueda
    busqueda = request.GET.get('busqueda', '').strip()
    if busqueda:
        clientes = clientes.filter(
            Q(nombre__icontains=busqueda) | 
            Q(apellido__icontains=busqueda) |
            Q(docCliente__icontains=busqueda) |
            Q(correoElecCliente__icontains=busqueda) |
            Q(telefono__icontains=busqueda)
        )
    
    # Ordenar por nombre
    clientes = clientes.order_by('nombre', 'apellido')
    
    context = {
        'clientes': clientes,
        'hay_clientes': todos_los_clientes.exists(),  # Para saber si mostrar la tabla o el mensaje
        'busqueda': busqueda,
    }
    return render(request, 'clientes/cliente_lista.html', context)

@login_required
@permission_required('clientes.gestion', raise_exception=True)
def cliente_detalle(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, 'clientes/cliente_detalle.html', {'cliente': cliente})

@login_required
@permission_required('clientes.gestion', raise_exception=True)
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
@permission_required('clientes.gestion', raise_exception=True)
def cambiar_categoria(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        form = CambiarCategoriaForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f'Categoría del cliente {cliente.nombre} actualizada exitosamente.')
            return redirect('clientes:cliente_lista')
    else:
        form = CambiarCategoriaForm(instance=cliente)
    
    context = {
        'form': form,
        'cliente': cliente,
        'titulo': f'Cambiar Categoría - {cliente.nombre}'
    }
    return render(request, 'clientes/cambiar_categoria.html', context)