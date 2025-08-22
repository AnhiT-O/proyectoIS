from django.shortcuts import render

# Create your views her
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from usuarios.models import Usuario
from clientes.models import Cliente, UsuarioCliente

def lista_usuarios(request):
    """Muestra todos los usuarios"""
    usuarios = Usuario.objects.all()
    return render(request, "usuarios/lista_usuarios.html", {"usuarios": usuarios})


def detalle_usuario(request, usuario_id):
    """Muestra un usuario, sus clientes asociados y permite asociar o desasociar"""
    usuario = get_object_or_404(Usuario, id=usuario_id)
    clientes = Cliente.objects.all()

    if request.method == "POST":
        if "asociar" in request.POST:
            cliente_id = request.POST.get("cliente_id")
            cliente = get_object_or_404(Cliente, id=cliente_id)

            # Crear la asociación si no existe
            obj, created = UsuarioCliente.objects.get_or_create(usuario=usuario, cliente=cliente)
            if created:
                messages.success(request, f"Cliente {cliente.nombre} asociado a {usuario.username}")
            else:
                messages.warning(request, f"El cliente {cliente.nombre} ya estaba asociado")

        elif "desasociar" in request.POST:
            cliente_id = request.POST.get("cliente_id")
            cliente = get_object_or_404(Cliente, id=cliente_id)

            UsuarioCliente.objects.filter(usuario=usuario, cliente=cliente).delete()
            messages.success(request, f"Cliente {cliente.nombre} desasociado de {usuario.username}")

        return redirect("detalle_usuario", usuario_id=usuario.id)

    return render(request, "usuarios/detalle_usuario.html", {
        "usuario": usuario,
        "clientes": clientes,
        "asociados": usuario.clientes.all(),
    })

