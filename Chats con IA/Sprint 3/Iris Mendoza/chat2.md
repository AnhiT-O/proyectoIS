irismendoza03: en el proyecto, dónde exactamente veo la integración son stripe?

GitHub Copilot: En el archivo views.py puedes ver la integración con Stripe principalmente en la función auxiliar llamada `procesar_medios_pago_cliente`. Allí se utiliza el paquete `stripe` para recuperar información de tarjetas de crédito asociadas a un cliente, usando el método:

```python
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
payment_method = stripe.PaymentMethod.retrieve(medio_cliente.stripe_payment_method_id)
card = payment_method.card
```

Esto ocurre tanto para administradores como para operadores, dependiendo del tipo de usuario. Además, en la vista `cliente_agregar_tarjeta`, se pasa la clave pública de Stripe al template para usar Stripe Elements en el frontend:

```python
'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
```

Por lo tanto, la integración con Stripe está en la lógica de obtención y visualización de tarjetas de crédito, y en la preparación del frontend para agregar nuevas tarjetas mediante Stripe.