from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from .models import Cotizacion
from monedas.models import Moneda
from clientes.models import Cliente

@method_decorator(login_required, name='dispatch')
class CotizacionListView(ListView):
    model = Cotizacion
    template_name = 'cotizacion/cotizacion_lista.html'
    context_object_name = 'cotizaciones'
    ordering = ['-fecha_cotizacion']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Si el usuario es cliente, obtener sus precios personalizados
        if hasattr(self.request.user, 'cliente'):
            cliente = self.request.user.cliente
            cotizaciones_con_precios = []
            for cotizacion in context['cotizaciones']:
                precios = cotizacion.get_precios_cliente(cliente)
                cotizaciones_con_precios.append({
                    'cotizacion': cotizacion,
                    'precio_compra': precios['precio_compra'],
                    'precio_venta': precios['precio_venta']
                })
            context['cotizaciones'] = cotizaciones_con_precios
        return context

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('monedas.cotizacion', raise_exception=True), name='dispatch')
class CotizacionCreateView(CreateView):
    model = Cotizacion
    template_name = 'cotizacion/cotizacion_form.html'
    fields = ['id_moneda']
    success_url = reverse_lazy('cotizacion:cotizacion_lista')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Mostrar solo monedas activas
        form.fields['id_moneda'].queryset = Moneda.objects.filter(activa=True)
        return form

    def form_valid(self, form):
        messages.success(self.request, 'Cotización creada exitosamente.')
        return super().form_valid(form)
