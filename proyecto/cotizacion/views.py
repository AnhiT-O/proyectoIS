from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView
from django.views import View
from django.urls import reverse_lazy
from django.http import JsonResponse
from decimal import Decimal
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

class SimuladorView(View):
    template_name = 'cotizacion/simulador.html'

    def get(self, request):
        monedas = Moneda.objects.filter(activa=True)
        return render(request, self.template_name, {'monedas': monedas})

    def post(self, request):
        try:
            moneda_id = request.POST.get('moneda')
            monto = Decimal(request.POST.get('monto', '0'))
            operacion = request.POST.get('operacion')

            if not all([moneda_id, monto, operacion]):
                return JsonResponse({
                    'success': False,
                    'error': 'Todos los campos son requeridos'
                })

            moneda = Moneda.objects.get(id=moneda_id)
            
            # Obtener la última cotización de la moneda
            cotizacion = (Cotizacion.objects
                         .filter(id_moneda=moneda)
                         .order_by('-fecha_cotizacion')
                         .first())

            if not cotizacion:
                return JsonResponse({
                    'success': False,
                    'error': 'No hay cotizaciones disponibles para esta moneda'
                })

            # Obtener el cliente si el usuario está autenticado
            cliente = None
            if request.user.is_authenticated and hasattr(request.user, 'cliente'):
                cliente = request.user.cliente

            # Obtener precios según la segmentación del cliente
            precios = cotizacion.get_precios_cliente(cliente) if cliente else {
                'precio_compra': cotizacion.calcular_precio_compra(),
                'precio_venta': cotizacion.calcular_precio_venta()
            }

            # Realizar la conversión según el tipo de operación
            if operacion == 'venta':
                # Venta: moneda extranjera a PYG
                resultado = monto * precios['precio_venta']
                mensaje = f"{resultado:,.0f} PYG"
            else:  # compra
                # Compra: PYG a moneda extranjera
                resultado = monto / precios['precio_compra']
                mensaje = f"{resultado:.2f} {moneda.simbolo}"

            return JsonResponse({
                'success': True,
                'resultado': mensaje
            })

        except (ValueError, Moneda.DoesNotExist) as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
