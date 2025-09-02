from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied

def inicio(request):
    """Vista para la página de inicio"""
    context = {}
    if request.user.is_authenticated:
        context['user_groups'] = [g.name for g in request.user.groups.all()]
    return render(request, 'inicio.html', context)

def custom_permission_denied_view(request, exception):
    """
    Vista personalizada para manejar errores 403 (Permission Denied)
    Se renderiza cuando un usuario autenticado no tiene permisos para acceder a una vista
    """
    return HttpResponseForbidden(render(request, '403.html').content)
