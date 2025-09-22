from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import Http404, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import MedioPago, MedioPagoCliente
import os
import stripe
import json
import logging

# Configurar Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_ENDPOINT_SECRET")

logger = logging.getLogger(__name__)

@login_required
def crear_setup_intent(request):
    """
    Crea un Setup Intent para guardar métodos de pago sin cargos inmediatos
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        cliente_id = data.get('cliente_id')
        
        if not cliente_id:
            return JsonResponse({'error': 'Cliente ID requerido'}, status=400)
        
        # Obtener o crear un customer en Stripe
        from clientes.models import Cliente
        cliente = get_object_or_404(Cliente, id=cliente_id)
        
        # Buscar si ya tiene un customer_id de Stripe
        stripe_customer = None
        medio_pago_tc = MedioPago.objects.get(tipo='tarjeta_credito')
        medio_cliente_tc = MedioPagoCliente.objects.filter(
            cliente=cliente,
            medio_pago=medio_pago_tc
        ).first()
        
        if medio_cliente_tc and medio_cliente_tc.stripe_customer_id:
            try:
                stripe_customer = stripe.Customer.retrieve(medio_cliente_tc.stripe_customer_id)
            except stripe.error.InvalidRequestError:
                # Customer no existe en Stripe, crear uno nuevo
                stripe_customer = None
        
        if not stripe_customer:
            # Crear customer en Stripe
            stripe_customer = stripe.Customer.create(
                email=cliente.correoElecCliente,
                name=cliente.nombre,
                metadata={
                    'cliente_id': str(cliente.id),
                    'documento': cliente.docCliente
                }
            )
            
            # Guardar o actualizar el customer_id en la base de datos
            if not medio_cliente_tc:
                medio_cliente_tc = MedioPagoCliente.objects.create(
                    cliente=cliente,
                    medio_pago=medio_pago_tc,
                    stripe_customer_id=stripe_customer.id,
                    activo=True
                )
            else:
                medio_cliente_tc.stripe_customer_id = stripe_customer.id
                medio_cliente_tc.save()
        
        # Crear Setup Intent
        setup_intent = stripe.SetupIntent.create(
            customer=stripe_customer.id,
            payment_method_types=['card'],
            usage='off_session',
            metadata={
                'cliente_id': str(cliente.id),
                'tipo_operacion': 'guardar_tarjeta'
            }
        )
        
        return JsonResponse({
            'client_secret': setup_intent.client_secret,
            'customer_id': stripe_customer.id
        })
        
    except Cliente.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado'}, status=404)
    except MedioPago.DoesNotExist:
        return JsonResponse({'error': 'Medio de pago tarjeta de crédito no configurado'}, status=500)
    except stripe.error.StripeError as e:
        logger.error(f"Error de Stripe: {e}")
        return JsonResponse({'error': 'Error al procesar con Stripe'}, status=500)
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)

@login_required
def crear_payment_intent(request):
    """
    Crea un Payment Intent para procesar un pago inmediato
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        amount = data.get('amount')  # en centavos
        currency = data.get('currency', 'usd')
        cliente_id = data.get('cliente_id')
        payment_method_id = data.get('payment_method_id')
        
        if not all([amount, cliente_id]):
            return JsonResponse({'error': 'Faltan parámetros requeridos'}, status=400)
        
        from clientes.models import Cliente
        cliente = get_object_or_404(Cliente, id=cliente_id)
        
        # Obtener el customer_id de Stripe
        medio_pago_tc = MedioPago.objects.get(tipo='tarjeta_credito')
        medio_cliente_tc = MedioPagoCliente.objects.filter(
            cliente=cliente,
            medio_pago=medio_pago_tc
        ).first()
        
        if not medio_cliente_tc or not medio_cliente_tc.stripe_customer_id:
            return JsonResponse({'error': 'Cliente no tiene configuración de Stripe'}, status=400)
        
        # Crear Payment Intent
        payment_intent_data = {
            'amount': int(amount),
            'currency': currency,
            'customer': medio_cliente_tc.stripe_customer_id,
            'metadata': {
                'cliente_id': str(cliente.id),
                'tipo_operacion': 'compra_moneda'
            }
        }
        
        if payment_method_id:
            payment_intent_data['payment_method'] = payment_method_id
            payment_intent_data['confirmation_method'] = 'manual'
            payment_intent_data['confirm'] = True
        
        payment_intent = stripe.PaymentIntent.create(**payment_intent_data)
        
        return JsonResponse({
            'client_secret': payment_intent.client_secret,
            'status': payment_intent.status
        })
        
    except Cliente.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado'}, status=404)
    except stripe.error.StripeError as e:
        logger.error(f"Error de Stripe: {e}")
        return JsonResponse({'error': 'Error al procesar pago con Stripe'}, status=500)
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)

@login_required
def obtener_metodos_pago(request, cliente_id):
    """
    Obtiene los métodos de pago guardados de un cliente en Stripe
    """
    try:
        from clientes.models import Cliente
        cliente = get_object_or_404(Cliente, id=cliente_id)
        
        medio_pago_tc = MedioPago.objects.get(tipo='tarjeta_credito')
        medio_cliente_tc = MedioPagoCliente.objects.filter(
            cliente=cliente,
            medio_pago=medio_pago_tc
        ).first()
        
        if not medio_cliente_tc or not medio_cliente_tc.stripe_customer_id:
            return JsonResponse({'payment_methods': []})
        
        # Obtener métodos de pago de Stripe
        payment_methods = stripe.PaymentMethod.list(
            customer=medio_cliente_tc.stripe_customer_id,
            type='card'
        )
        
        # Formatear respuesta
        methods_data = []
        for pm in payment_methods.data:
            card = pm.card
            methods_data.append({
                'id': pm.id,
                'brand': card.brand,
                'last4': card.last4,
                'exp_month': card.exp_month,
                'exp_year': card.exp_year,
                'funding': card.funding
            })
        
        return JsonResponse({'payment_methods': methods_data})
        
    except Cliente.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado'}, status=404)
    except stripe.error.StripeError as e:
        logger.error(f"Error de Stripe: {e}")
        return JsonResponse({'error': 'Error al obtener métodos de pago'}, status=500)
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)

@csrf_exempt  # desactiva CSRF solo en este endpoint
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        logger.error(f"Error al parsear JSON del webhook: {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Firma inválida del webhook: {e}")
        return HttpResponse(status=400)

    # Manejo de eventos
    try:
        if event["type"] == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]
            amount = payment_intent["amount"] / 100
            currency = payment_intent["currency"]
            cliente_id = payment_intent["metadata"].get("cliente_id")
            
            logger.info(f"✅ Pago exitoso: {amount} {currency} para cliente {cliente_id}")
            
            # Aquí puedes actualizar tu base de datos con la transacción exitosa
            # Por ejemplo, crear un registro de transacción, actualizar saldos, etc.
            
        elif event["type"] == "setup_intent.succeeded":
            setup_intent = event["data"]["object"]
            customer_id = setup_intent["customer"]
            payment_method = setup_intent["payment_method"]
            cliente_id = setup_intent["metadata"].get("cliente_id")
            
            logger.info(f"✅ Método de pago guardado: {payment_method} para cliente {cliente_id}")
            
            # Actualizar la base de datos con el nuevo método de pago
            if cliente_id:
                try:
                    from clientes.models import Cliente
                    cliente = Cliente.objects.get(id=cliente_id)
                    medio_pago_tc = MedioPago.objects.get(tipo='tarjeta_credito')
                    
                    medio_cliente_tc, created = MedioPagoCliente.objects.get_or_create(
                        cliente=cliente,
                        medio_pago=medio_pago_tc,
                        defaults={
                            'stripe_customer_id': customer_id,
                            'stripe_payment_method_id': payment_method,
                            'activo': True
                        }
                    )
                    
                    if not created:
                        medio_cliente_tc.stripe_payment_method_id = payment_method
                        medio_cliente_tc.stripe_customer_id = customer_id
                        medio_cliente_tc.activo = True
                        medio_cliente_tc.save()
                        
                except (Cliente.DoesNotExist, MedioPago.DoesNotExist) as e:
                    logger.error(f"Error al actualizar método de pago en BD: {e}")
            
        elif event["type"] == "payment_method.attached":
            payment_method = event["data"]["object"]
            logger.info(f"Método de pago adjuntado: {payment_method['id']}")
            
        else:
            logger.info(f"Evento no manejado: {event['type']}")

    except Exception as e:
        logger.error(f"Error procesando webhook: {e}")
        return HttpResponse(status=500)

    return JsonResponse({"success": True})
