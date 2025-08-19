from django.shortcuts import render

def inicio(request):
    """Vista para la página de inicio"""
    return render(request, 'inicio.html')
