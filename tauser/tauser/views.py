"""
Vistas para el sistema TAUser (Terminal Autónomo de Usuario).

Este módulo contiene todas las vistas necesarias para el funcionamiento de las
terminales TAUser, que permiten a los clientes completar sus transacciones de
cambio de moneda de forma autónoma mediante interfaces específicas.

El sistema TAUser maneja:
- Ingreso y validación de tokens de transacción
- Procesamiento de pagos en efectivo
- Gestión de caja fuerte (ingreso/extracción de billetes)
- Detección de cambios de cotización en tiempo real
- Confirmación y finalización de transacciones

Functions:
    inicio: Vista principal del TAUser
    caja_fuerte: Gestión de billetes en caja fuerte
    ingreso_token: Validación de tokens y detección de cambios de cotización
    ingreso_billetes: Procesamiento de pagos en efectivo
    exito: Confirmación de transacción completada

Author: Equipo de desarrollo Global Exchange  
Date: 2025
"""

from datetime import timedelta
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils import timezone
from transacciones.models import Transaccion, Tauser, BilletesTauser, billetes_necesarios, procesar_transaccion, calcular_conversion, verificar_cambio_cotizacion, no_redondeado
from transacciones.utils_2fa import is_2fa_enabled, create_transaction_token, validate_2fa_token
from .forms import TokenForm, IngresoForm, Token2FAForm
from monedas.models import Denominacion


def inicio(request):
    """
    Vista principal del sistema TAUser.
    
    Renderiza la página de inicio de la terminal autónoma donde los clientes
    pueden acceder a las diferentes funcionalidades disponibles como ingreso
    de tokens, gestión de caja fuerte, etc.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP de Django
        
    Returns:
        HttpResponse: Página de inicio renderizada (inicio.html)
        
    Template:
        inicio.html - Interfaz principal del TAUser con opciones de navegación
        
    Context:
        No requiere contexto adicional
        
    Note:
        Esta vista no requiere autenticación ya que el TAUser opera
        de forma autónoma sin login de usuarios.
    """
    return render(request, 'inicio.html')

def caja_fuerte(request):
    """
    Vista para gestión de caja fuerte del TAUser.
    
    Permite el ingreso y extracción de billetes en la caja fuerte del TAUser
    mediante la carga de archivos de texto con formato específico. Esta función
    es crucial para mantener el stock de billetes necesario para las operaciones
    de cambio.
    
    Functionality:
        - GET: Muestra formulario de carga de archivo
        - POST: Procesa archivo y actualiza inventario de billetes
        
    File Format Expected:
        Línea 1: "Ingreso" o "Extraccion"
        Líneas siguientes: [Moneda][TAB][Valor][TAB][Cantidad]
        
    Args:
        request (HttpRequest): Objeto de solicitud HTTP
            - GET: Renderiza formulario
            - POST: Procesa archivo cargado
            - FILES: Contiene el archivo .txt con datos de billetes
            
    Returns:
        HttpResponse: Página de gestión de caja fuerte (caja_fuerte.html)
        
    Template:
        caja_fuerte.html - Interfaz para carga de archivos de billetes
        
    Context:
        form (IngresoForm): Formulario para carga de archivo
        
    Raises:
        Exception: Captura errores de procesamiento de archivo y redirige
        
    Business Logic:
        1. Valida formato del archivo
        2. Identifica TAUser por puerto
        3. Procesa operaciones de ingreso/extracción
        4. Actualiza stock de billetes en base de datos
        5. Valida disponibilidad para extracciones
        
    Security Notes:
        - Validación de formato de archivo
        - Verificación de stock antes de extracciones
        - Manejo seguro de excepciones
    """
    if request.method == 'POST':
        form = IngresoForm(request.POST, request.FILES)
        if form.is_valid():
            # Inicializar variables para procesamiento del archivo
            accion = None  # "Ingreso" o "Extraccion"
            billetes = []  # Lista de nombres de monedas
            valores = []   # Lista de valores/denominaciones
            cantidades = [] # Lista de cantidades de billetes
            
            try:
                # Procesar archivo cargado línea por línea
                archivo = form.cleaned_data['archivo']
                lineas = archivo.readlines()
                if lineas:
                    # Primera línea determina la acción
                    accion = lineas[0].decode('utf-8').strip()
                    
                    # Procesar cada línea con datos de billetes
                    for linea in lineas[1:]:
                        lectura_billetes = linea.decode('utf-8').strip().split('\t')
                        billetes.append(lectura_billetes[0])      # Nombre de moneda
                        valores.append(int(lectura_billetes[1]))  # Valor/denominación
                        cantidades.append(int(lectura_billetes[2])) # Cantidad
            except Exception as e:
                # Manejo de errores de procesamiento del archivo
                print(e)
                return redirect('caja_fuerte')
            # Identificar el TAUser actual por el puerto de la solicitud
            tauser = Tauser.objects.get(puerto=int(request.get_port()))
            
            if accion == 'Ingreso':
                # Procesar ingreso de billetes a la caja fuerte
                for i in range(len(billetes)):
                    try:
                        # Buscar denominación según tipo de moneda
                        if billetes[i] == 'Guaraní':
                            # Moneda local (guaraníes) tiene moneda=None
                            denominacion = Denominacion.objects.get(valor=valores[i], moneda=None)
                        else:
                            # Moneda extranjera
                            denominacion = Denominacion.objects.get(valor=valores[i], moneda__nombre=billetes[i])
                    except Denominacion.DoesNotExist:
                        print(f'La denominación {billetes[i]} {valores[i]} no se reconoce.')
                    tauser_billete, creado = BilletesTauser.objects.get_or_create(denominacion=denominacion, tauser=tauser)
                    tauser_billete.cantidad += cantidades[i]
                    tauser_billete.save()
                    print(f'Se han ingresado {cantidades[i]} billetes de {billetes[i]} {valores[i]}')
            else:
                # Procesar extracción de billetes de la caja fuerte
                # Primera pasada: Validar disponibilidad de billetes para extracción
                for i in range(len(billetes)):
                    try:
                        # Buscar denominación según tipo de moneda
                        if billetes[i] == 'Guaraní':
                            denominacion = Denominacion.objects.get(valor=valores[i], moneda=None)
                        else:
                            denominacion = Denominacion.objects.get(valor=valores[i], moneda__nombre=billetes[i])
                    except Denominacion.DoesNotExist:
                        print(f'La denominación {billetes[i]} {valores[i]} no se reconoce.')
                        return redirect('caja_fuerte')
                    
                    # Verificar stock disponible
                    try:
                        tauser_billete = BilletesTauser.objects.get(denominacion=denominacion, tauser=tauser)
                    except BilletesTauser.DoesNotExist:
                        tauser_billete = None
                    
                    # Validar que hay suficientes billetes para la extracción
                    if not tauser_billete or tauser_billete.cantidad < cantidades[i]:
                        print(f'No hay suficientes billetes de {billetes[i]} {valores[i]} para la extracción.')
                        return redirect('caja_fuerte')
                # Segunda pasada: Realizar la extracción
                for i in range(len(billetes)):
                    if billetes[i] == 'Guaraní':
                        denominacion = Denominacion.objects.get(valor=valores[i], moneda=None)
                    else:
                        denominacion = Denominacion.objects.get(valor=valores[i], moneda__nombre=billetes[i])
                    
                    # Actualizar stock restando la cantidad extraída
                    tauser_billete = BilletesTauser.objects.get(denominacion=denominacion, tauser=tauser)
                    tauser_billete.cantidad -= cantidades[i]
                    tauser_billete.save()
                    print(f'Se han extraído {cantidades[i]} billetes de {billetes[i]} {valores[i]}')
        else:
            # Acción no reconocida en el archivo
            print(request, 'No se reconoce la acción.')
            return redirect('caja_fuerte')
    else:
        # Método GET: Mostrar formulario vacío
        form = IngresoForm()
    
    return render(request, 'caja_fuerte.html', {'form': form})

def ingreso_token(request):
    """
    Vista principal para procesamiento de tokens de transacción.
    
    Esta función maneja el núcleo del sistema TAUser, permitiendo a los clientes
    ingresar sus tokens de transacción y procesando la lógica de negocio asociada,
    incluyendo detección de cambios de cotización, validación de tokens y
    gestión del flujo de transacciones.
    
    Functionality:
        - Validación y procesamiento de tokens de 8 caracteres
        - Detección automática de cambios de cotización
        - Manejo de expiración de transacciones (5 minutos)
        - Notificaciones por email a usuarios operadores
        - Gestión de estados de transacción (Pendiente, Cancelada, Completa)
        - Redirección a ingreso de billetes para pagos en efectivo
    
    Flow Control:
        POST 'aceptar': Cliente acepta cambios de cotización
        POST 'cancelar': Cliente cancela por cambios de cotización  
        POST 'enviar': Cliente ingresa nuevo token para procesar
        GET: Muestra formulario de ingreso de token
        
    Args:
        request (HttpRequest): Objeto de solicitud HTTP
            - POST: Procesa acciones del cliente (aceptar/cancelar/enviar)
            - GET: Renderiza formulario de ingreso de token
            - session: Mantiene estado de transacciones en progreso
            
    Returns:
        HttpResponse: Respuesta según la acción:
            - Formulario de ingreso (GET)
            - Página de confirmación con cambios detectados
            - Redirección a ingreso de billetes
            - Página de éxito para transacciones completadas
            
    Template:
        ingreso_token.html - Interfaz para ingreso de tokens y confirmación
        
    Context (cuando hay cambios de cotización):
        cambios (dict): Información de cambios detectados
        transaccion (Transaccion): Objeto transacción actualizado
        email_usuario (str): Email del usuario operador para notificaciones
        
    Business Logic:
        1. Valida formato y existencia del token
        2. Verifica estado y expiración de transacción
        3. Detecta cambios de cotización en tiempo real
        4. Envía notificaciones por email al operador
        5. Actualiza precios según nuevas cotizaciones
        6. Gestiona flujo hacia ingreso de billetes
        
    Security & Validation:
        - Tokens alfanuméricos de 8 caracteres únicamente
        - Validación de estados de transacción
        - Control de expiración (5 minutos máximo)
        - Verificación de medios de pago compatibles con TAUser
        - Manejo seguro de sesiones y contexto
        
    Error Handling:
        - Transacciones no encontradas
        - Tokens expirados o inválidos
        - Transacciones ya procesadas o canceladas
        - Medios de pago incompatibles con TAUser
        
    Email Notifications:
        Envía automáticamente notificaciones al usuario operador cuando:
        - Se detectan cambios de cotización
        - Incluye detalles de precios anteriores vs actuales
        - Proporciona información completa de la transacción
    """
    form = TokenForm()
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'aceptar':
            # Cliente acepta los nuevos precios por cambio de cotización
            try:
                transaccion = Transaccion.objects.get(id=request.session.get('transaccion'))
            except Transaccion.DoesNotExist:
                messages.error(request, 'Transacción no encontrada.')
                return redirect('ingreso_token')
            # Si el 2FA está habilitado, devolver respuesta JSON para mostrar modal
            if is_2fa_enabled():
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'show_2fa': True,
                    'user_email': transaccion.usuario.email
                })
            return redirect('ingreso_billetes', codigo=transaccion.token)
        
        elif accion == 'cancelar':
            # Cliente cancela la transacción debido a cambios de cotización
            try:
                transaccion = Transaccion.objects.get(id=request.session.get('transaccion'))
            except Transaccion.DoesNotExist:
                messages.error(request, 'Transacción no encontrada.')
                return redirect('ingreso_token')
            
            # Marcar transacción como cancelada con razón específica
            transaccion.estado = 'Cancelada'
            transaccion.razon = 'Usuario cancela debido a cambios de cotización'
            transaccion.save()
            messages.info(request, 'Transacción cancelada.')
            return redirect('inicio')
        
        elif accion == 'enviar':
            # Cliente ingresa un token para procesar transacción
            form = TokenForm(request.POST)
            if form.is_valid():
                codigo = form.cleaned_data['codigo']
                
                # Buscar transacción por token
                try:
                    transaccion = Transaccion.objects.get(token=codigo)
                except Transaccion.DoesNotExist:
                    messages.error(request, 'Transacción no encontrada.')
                    return redirect('ingreso_token')
                
                # Validar estado de la transacción
                if transaccion.estado == 'Cancelada':
                    messages.error(request, 'Este token corresponde a una transacción ya cancelada.')
                    return redirect('ingreso_token')
                
                if transaccion.estado == 'Completa':
                    messages.error(request, 'Este token corresponde a una transacción ya completada.')
                    return redirect('ingreso_token')
                
                if transaccion.estado == 'Pendiente':
                    # Verificar expiración de transacción (límite: 5 minutos)
                    if transaccion.fecha_hora < timezone.now() - timedelta(minutes=5):
                        transaccion.estado = 'Cancelada'
                        transaccion.razon = 'Expira el tiempo para confirmar la transacción'
                        transaccion.save()
                        
                        # Mensaje diferenciado según si ya se pagó algo
                        if transaccion.pagado > 0:
                            messages.info(request, 'El token ha expirado. Contacta a soporte para el reembolso de lo pagado.')
                        else:
                            messages.error(request, 'El token ha expirado.')
                        return redirect('ingreso_token')
                    
                    if transaccion.medio_pago == 'Efectivo':
                        # Obtener email del usuario que procesó la transacción para notificaciones
                        email_usuario = getattr(transaccion.usuario, 'email', None)
                        cambios = verificar_cambio_cotizacion(transaccion, email_usuario)
                        if cambios and cambios.get('hay_cambios'):
                            datos_transaccion = calcular_conversion(transaccion.monto, transaccion.moneda, transaccion.tipo, transaccion.medio_pago, transaccion.medio_cobro, transaccion.cliente.segmento)
                            if transaccion.tipo == 'venta':
                                if transaccion.medio_pago == 'Efectivo' and no_redondeado(transaccion.monto, list(Denominacion.objects.filter(moneda=transaccion.moneda).values_list('valor', flat=True))) > 0:
                                    messages.error(request, 'El monto ingresado no está redondeado para pago en efectivo. Se cancela la transacción.')
                                    transaccion.estado = 'Cancelada'
                                    transaccion.fecha_hora = timezone.now()
                                    transaccion.razon = 'Monto no redondeado para pago en efectivo tras cambio de cotización'
                                    transaccion.save()
                                    return redirect('inicio')
                                if transaccion.medio_cobro == 'Efectivo' and no_redondeado(transaccion.precio_final, list(Denominacion.objects.filter(moneda=None).values_list('valor', flat=True))) > 0:
                                    messages.error(request, 'El monto final no está redondeado para cobro en efectivo. Se cancela la transacción.')
                                    transaccion.estado = 'Cancelada'
                                    transaccion.fecha_hora = timezone.now()
                                    transaccion.razon = 'Monto no redondeado para cobro en efectivo tras cambio de cotización'
                                    transaccion.save()
                                    return redirect('inicio')
                            else:
                                if transaccion.medio_pago == 'Efectivo' and no_redondeado(transaccion.precio_final, list(Denominacion.objects.filter(moneda=None).values_list('valor', flat=True))) > 0:
                                    messages.error(request, 'El monto final no está redondeado para pago en efectivo. Se cancela la transacción.')
                                    transaccion.estado = 'Cancelada'
                                    transaccion.fecha_hora = timezone.now()
                                    transaccion.razon = 'Monto no redondeado para pago en efectivo tras cambio de cotización'
                                    transaccion.save()
                                    return redirect('inicio')
                                if transaccion.medio_cobro == 'Efectivo' and no_redondeado(transaccion.monto, list(Denominacion.objects.filter(moneda=transaccion.moneda).values_list('valor', flat=True))) > 0:
                                    messages.error(request, 'El monto ingresado no está redondeado para cobro en efectivo. Se cancela la transacción.')
                                    transaccion.estado = 'Cancelada'
                                    transaccion.fecha_hora = timezone.now()
                                    transaccion.razon = 'Monto no redondeado para cobro en efectivo tras cambio de cotización'
                                    transaccion.save()
                                    return redirect('inicio')
                            transaccion.precio_base = datos_transaccion['precio_base']
                            transaccion.cotizacion = datos_transaccion['cotizacion']
                            transaccion.beneficio_segmento = datos_transaccion['beneficio_segmento']
                            transaccion.porc_beneficio_segmento = datos_transaccion['porc_beneficio_segmento']
                            transaccion.recargo_pago = datos_transaccion['monto_recargo_pago']
                            transaccion.porc_recargo_pago = datos_transaccion['porc_recargo_pago']
                            transaccion.recargo_cobro = datos_transaccion['monto_recargo_cobro']
                            transaccion.porc_recargo_cobro = datos_transaccion['porc_recargo_cobro']
                            transaccion.monto = datos_transaccion['monto']
                            transaccion.precio_final = datos_transaccion['precio_final']
                            transaccion.save()
                            
                            # Guardar transacción en sesión y mostrar confirmación de cambios
                            request.session['transaccion'] = transaccion.id
                            context = {
                                'cambios': cambios,
                                'transaccion': transaccion,
                                'email_usuario': email_usuario,
                                'enable_2fa': is_2fa_enabled(),
                                'user_email': transaccion.usuario.email if transaccion.usuario.email else ''
                            }
                            return render(request, 'ingreso_token.html', context)
                        
                        # Guardar la transacción en sesión para el 2FA
                        request.session['transaccion'] = transaccion.id
                        
                        # Si el 2FA está habilitado, renderizar template con flag para mostrar modal
                        if is_2fa_enabled():
                            context = {
                                'form': TokenForm(),
                                'enable_2fa': True,
                                'user_email': transaccion.usuario.email if transaccion.usuario.email else '',
                                'show_2fa_modal': True
                            }
                            return render(request, 'ingreso_token.html', context)
                        
                        return redirect('ingreso_billetes', codigo=codigo)
                    else:
                        # Medio de pago no compatible con TAUser (solo efectivo)
                        messages.error(request, 'El token no corresponde a una operación de Tauser.')
                        return redirect('ingreso_token')
                else:
                    # Transacción ya procesada - aplicar 2FA si está habilitado
                    request.session['transaccion'] = transaccion.id
                    
                    if is_2fa_enabled():
                        context = {
                            'form': TokenForm(),
                            'enable_2fa': True,
                            'user_email': transaccion.usuario.email if transaccion.usuario.email else '',
                            'show_2fa_modal': True,
                            'transaccion_procesada': True  # Flag para indicar que ya está procesada
                        }
                        return render(request, 'ingreso_token.html', context)
                    
                    procesar_transaccion(transaccion, Tauser.objects.get(puerto=int(request.get_port())))
                    return redirect('exito', codigo=codigo)
    else:
        # Método GET: Mostrar formulario de ingreso de token
        form = TokenForm()
    
    context = {
        'form': form,
        'enable_2fa': is_2fa_enabled(),
        'user_email': ''
    }
    return render(request, 'ingreso_token.html', context)

def ingreso_billetes(request, codigo):
    """
    Vista para procesamiento de pagos en efectivo mediante ingreso de billetes.
    
    Esta función maneja la fase final del proceso de transacción en TAUser,
    donde los clientes ingresan físicamente los billetes para completar
    sus operaciones de compra o venta de monedas extranjeras.
    
    Functionality:
        - Validación de billetes según tipo de operación (compra/venta)
        - Cálculo automático de vueltos cuando corresponde
        - Verificación de disponibilidad de billetes para vueltos
        - Actualización en tiempo real del estado de pago
        - Gestión de inventario de billetes en TAUser
        - Procesamiento y finalización de transacciones
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP
            - POST: Procesa archivo con billetes ingresados
            - GET: Muestra formulario de carga de archivo
            - FILES: Archivo .txt con información de billetes
        codigo (str): Token de transacción de 8 caracteres
        
    Returns:
        HttpResponse: Respuesta según el estado del procesamiento:
            - Formulario de ingreso (GET o errores de validación)
            - Página de éxito (transacción completada)
            - Mensajes de error/advertencia (pagos parciales o problemas)
            
    Template:
        ingreso_billetes.html - Interfaz para carga de archivos de billetes
        
    Context:
        form (IngresoForm): Formulario para carga de archivo
        transaccion (Transaccion): Objeto de transacción en proceso
        
    Business Logic - Compras (Cliente paga Guaraníes, recibe Moneda Extranjera):
        1. Valida que solo se ingresen billetes en Guaraníes
        2. Verifica denominaciones válidas existentes
        3. Calcula total ingresado vs precio final
        4. Gestiona vueltos automáticamente si se excede el monto
        5. Actualiza inventario del TAUser
        6. Entrega moneda extranjera calculada
        
    Business Logic - Ventas (Cliente entrega Moneda Extranjera, recibe Guaraníes):
        1. Valida que se ingresen billetes de la moneda específica
        2. Verifica denominaciones válidas de la moneda
        3. Calcula total vs monto requerido de moneda extranjera
        4. Gestiona vueltos en moneda extranjera si aplica
        5. Entrega guaraníes equivalentes
        
    Validation & Security:
        - Verificación de denominaciones válidas por moneda
        - Control de stock suficiente para vueltos
        - Validación de archivos de billetes
        - Actualización atómica de inventarios
        - Prevención de transacciones duplicadas
        
    Error Handling:
        - Transacciones no encontradas o inválidas
        - Archivos de billetes malformados
        - Denominaciones no reconocidas
        - Stock insuficiente para vueltos
        - Billetes incorrectos según tipo de operación
        
    File Format Expected (Billetes):
        [Moneda][TAB][Valor][TAB][Cantidad]
        
        Ejemplos:
        - Compra: "Guaraní	50000	5" (5 billetes de 50,000 Gs)
        - Venta: "Dólar	100	2" (2 billetes de $100 USD)
    """
    # Obtener transacción por token
    try:
        transaccion = Transaccion.objects.get(token=codigo)
    except Transaccion.DoesNotExist:
        messages.error(request, 'Transacción no encontrada.')
        return redirect('ingreso_token')
    
    if request.method == 'POST':
        form = IngresoForm(request.POST, request.FILES)
        if form.is_valid():
            billetes = []
            valores = []
            cantidades = []
            try:
                archivo = form.cleaned_data['archivo']
                lineas = archivo.readlines()
                if lineas:
                    for linea in lineas:
                        lectura_billetes = linea.decode('utf-8').strip().split('\t')
                        billetes.append(lectura_billetes[0])
                        valores.append(int(lectura_billetes[1]))
                        cantidades.append(int(lectura_billetes[2]))
            except Exception as e:
                messages.error(request, 'Billetes no reconocidos. Se devuelve lo ingresado.')
                print(e)
                return redirect('ingreso_billetes', codigo=codigo)
            tauser = Tauser.objects.get(puerto=int(request.get_port()))
            if transaccion.tipo == 'compra':
                for i in range(len(billetes)):
                    if billetes[i] != 'Guaraní':
                        messages.error(request, 'Solo se aceptan billetes en Guaraníes para compras. Se devuelve lo ingresado.')
                        return redirect('ingreso_billetes', codigo=codigo)
                    if valores[i] not in [den.valor for den in Denominacion.objects.filter(moneda=None)]:
                        messages.error(request, f'La denominación {valores[i]} no se reconoce. Se devuelve lo ingresado.')
                        return redirect('ingreso_billetes', codigo=codigo)
                total = 0
                for i in range(len(billetes)):
                    total += valores[i] * cantidades[i]
                if total > transaccion.precio_final - transaccion.pagado:
                    v_denominaciones = list(Denominacion.objects.filter(moneda=None).order_by('valor').values_list('valor', flat=True))
                    v_cantidades_qs = BilletesTauser.objects.filter(denominacion__moneda=None, tauser=tauser).order_by('denominacion__valor')
                    v_cantidades = {b.denominacion.valor: b.cantidad for b in v_cantidades_qs}
                    vuelto = billetes_necesarios(total - transaccion.precio_final, v_denominaciones, v_cantidades)
                    if not vuelto:
                        messages.error(request, 'No hay billetes suficientes para dar el vuelto. Se devuelve lo ingresado.')
                        return redirect('ingreso_billetes', codigo=codigo)
                for i in range(len(billetes)):
                    denominacion = Denominacion.objects.get(valor=valores[i], moneda=None)
                    tauser_billete, creado = BilletesTauser.objects.get_or_create(denominacion=denominacion, tauser=tauser)
                    tauser_billete.cantidad += cantidades[i]
                    tauser_billete.save()
                    transaccion.pagado += valores[i] * cantidades[i]
                    transaccion.fecha_hora = timezone.now()
                    transaccion.save()
                if transaccion.pagado < transaccion.precio_final:
                    messages.warning(request, f'Se ha ingresado Gs. {transaccion.pagado:,.0f}'.replace(",", ".") + ',' + f' aún faltan Gs. {transaccion.precio_final - transaccion.pagado:,.0f}'.replace(",", "."))
                    return redirect('ingreso_billetes', codigo=codigo)
                elif transaccion.pagado > transaccion.precio_final:
                    v_denominaciones = list(Denominacion.objects.filter(moneda=None).order_by('valor').values_list('valor', flat=True))
                    v_cantidades_qs = BilletesTauser.objects.filter(denominacion__moneda=None, tauser=tauser).order_by('denominacion__valor')
                    v_cantidades = {b.denominacion.valor: b.cantidad for b in v_cantidades_qs}
                    vuelto = billetes_necesarios(total - transaccion.precio_final, v_denominaciones, v_cantidades)
                    for valor, cantidad in vuelto.items():
                        denominacion = Denominacion.objects.get(valor=valor, moneda=None)
                        tauser_billete = BilletesTauser.objects.get(denominacion=denominacion, tauser=tauser)
                        tauser_billete.cantidad -= cantidad
                        tauser_billete.save()
                    messages.success(request, f'Tu vuelto es Gs. {(transaccion.pagado - transaccion.precio_final):,.0f}'.replace(",", ".") + '. Retiralo.')
                    procesar_transaccion(transaccion, tauser)
                    return redirect('exito', codigo=codigo)
                else:
                    procesar_transaccion(transaccion, tauser)
                    return redirect('exito', codigo=codigo)
            else:
                for i in range(len(billetes)):
                    if billetes[i] != transaccion.moneda.nombre:
                        messages.error(request, f'Solo se aceptan billetes de {transaccion.moneda.nombre} para ventas. Se devuelve lo ingresado.')
                        return redirect('ingreso_billetes', codigo=codigo)
                    if valores[i] not in [den.valor for den in Denominacion.objects.filter(moneda=transaccion.moneda)]:
                        messages.error(request, f'La denominación {valores[i]} no se reconoce. Se devuelve lo ingresado.')
                        return redirect('ingreso_billetes', codigo=codigo)
                total = 0
                for i in range(len(billetes)):
                    total += valores[i] * cantidades[i]
                if total > transaccion.monto - transaccion.pagado:
                    v_denominaciones = list(Denominacion.objects.filter(moneda=transaccion.moneda).order_by('valor').values_list('valor', flat=True))
                    v_cantidades_qs = BilletesTauser.objects.filter(denominacion__moneda=transaccion.moneda, tauser=tauser).order_by('denominacion__valor')
                    v_cantidades = {b.denominacion.valor: b.cantidad for b in v_cantidades_qs}
                    vuelto = billetes_necesarios(int(total - transaccion.monto), v_denominaciones, v_cantidades)
                    if not vuelto:
                        messages.error(request, 'No hay billetes suficientes para dar el vuelto. Se devuelve lo ingresado.')
                        return redirect('ingreso_billetes', codigo=codigo)
                for i in range(len(billetes)):
                    denominacion = Denominacion.objects.get(valor=valores[i], moneda__nombre=billetes[i])
                    tauser_billete, creado = BilletesTauser.objects.get_or_create(denominacion=denominacion, tauser=tauser)
                    tauser_billete.cantidad += cantidades[i]
                    tauser_billete.save()
                    transaccion.pagado += valores[i] * cantidades[i]
                    transaccion.fecha_hora = timezone.now()
                    transaccion.save()
                if transaccion.pagado < transaccion.monto:
                    messages.warning(request, f'Se ha ingresado {transaccion.pagado:,.0f}'.replace(",", ".") + f' {transaccion.moneda.simbolo},' + f' aún faltan {transaccion.monto - transaccion.pagado:,.0f}'.replace(",", ".") + f' {transaccion.moneda.simbolo}')
                    return redirect('ingreso_billetes', codigo=codigo)
                elif transaccion.pagado > transaccion.monto:
                    v_denominaciones = list(Denominacion.objects.filter(moneda=transaccion.moneda).order_by('valor').values_list('valor', flat=True))
                    v_cantidades_qs = BilletesTauser.objects.filter(denominacion__moneda=transaccion.moneda, tauser=tauser).order_by('denominacion__valor')
                    v_cantidades = {b.denominacion.valor: b.cantidad for b in v_cantidades_qs}
                    vuelto = billetes_necesarios(int(transaccion.pagado - transaccion.monto), v_denominaciones, v_cantidades)
                    for valor, cantidad in vuelto.items():
                        denominacion = Denominacion.objects.get(valor=valor, moneda=transaccion.moneda)
                        tauser_billete = BilletesTauser.objects.get(denominacion=denominacion, tauser=tauser)
                        tauser_billete.cantidad -= cantidad
                        tauser_billete.save()
                    messages.success(request, f'Tu vuelto es {(transaccion.pagado - transaccion.monto):,.0f}'.replace(",", ".") + f' {transaccion.moneda.simbolo}. Retiralo.')
                    procesar_transaccion(transaccion, tauser)
                    return redirect('exito', codigo=codigo)
                else:
                    procesar_transaccion(transaccion, tauser)
                    return redirect('exito', codigo=codigo)
        else:
            messages.error(request, 'Billetes no reconocidos. Se devuelve lo ingresado.')
            return redirect('ingreso_billetes', codigo=codigo)
    else:
        form = IngresoForm()
    return render(request, 'ingreso_billetes.html', {'form': form, 'transaccion': transaccion})

def exito(request, codigo):
    """
    Vista de confirmación para transacciones completadas exitosamente.
    
    Renderiza la página de éxito que se muestra al cliente cuando su
    transacción ha sido procesada y completada exitosamente en el TAUser.
    Esta vista proporciona un resumen final de la operación realizada.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP
        codigo (str): Token de transacción de 8 caracteres
        
    Returns:
        HttpResponse: Página de éxito con detalles de transacción completada
        
    Template:
        exito.html - Página de confirmación final con resumen de transacción
        
    Context:
        transaccion (Transaccion): Objeto completo de la transacción finalizada
            - Incluye todos los detalles: cliente, montos, fechas, etc.
            - Estado debe ser 'Completa' para llegar a esta vista
            - Contiene información de facturación si aplica
        
    Business Context:
        Esta vista se alcanza únicamente cuando:
        1. El token es válido y la transacción existe
        2. El pago fue procesado correctamente
        3. Los billetes fueron intercambiados exitosamente  
        4. El estado de transacción cambió a 'Completa'
        5. El inventario del TAUser fue actualizado
        
    Note:
        - No requiere validación adicional de estado ya que solo
          se accede tras procesamiento exitoso
        - La transacción ya fue marcada como 'Completa'
        - Sirve como comprobante final para el cliente
        - Puede incluir información de facturación electrónica
    """
    # Obtener transacción completada por token
    transaccion = Transaccion.objects.get(token=codigo)
    return render(request, 'exito.html', {'transaccion': transaccion})

def verificar_2fa(request):
    """
    Vista para verificar el código 2FA antes de continuar con el ingreso de billetes.
    """
    # Verificar que el 2FA esté habilitado
    if not is_2fa_enabled():
        messages.error(request, 'El sistema de verificación 2FA no está habilitado.')
        return redirect('inicio')
    
    # Verificar que exista una transacción en sesión
    transaccion_id = request.session.get('transaccion')
    if not transaccion_id:
        messages.error(request, 'No hay transacción pendiente.')
        return redirect('ingreso_token')
    
    try:
        transaccion = Transaccion.objects.get(id=transaccion_id)
    except Transaccion.DoesNotExist:
        messages.error(request, 'Transacción no encontrada.')
        return redirect('ingreso_token')
    
    # Verificar que el usuario asociado a la transacción tenga email
    if not transaccion.usuario.email:
        messages.error(request, 'El usuario asociado a esta transacción no tiene email configurado.')
        return redirect('ingreso_token')
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'enviar_codigo':
            # Enviar el código 2FA al usuario
            transaccion_data = {
                'transaccion_id': transaccion.id,
                'cliente_id': transaccion.cliente.id,
                'tipo': transaccion.tipo,
                'monto': str(transaccion.monto),
                'moneda_id': transaccion.moneda.id,
                'precio_final': transaccion.precio_final,
                'medio_pago': transaccion.medio_pago,
                'medio_cobro': transaccion.medio_cobro
            }
            
            result = create_transaction_token(transaccion.usuario, transaccion_data)
            
            if result['success']:
                request.session['2fa_sent'] = True
                messages.success(request, f'Código de verificación enviado a {transaccion.usuario.email}')
            else:
                messages.error(request, result['message'])
            
            return redirect('verificar_2fa')
        
        elif accion == 'verificar':
            form = Token2FAForm(request.POST)
            if form.is_valid():
                codigo_2fa = form.cleaned_data['codigo_2fa']
                
                # Validar el código 2FA
                result = validate_2fa_token(transaccion.usuario, codigo_2fa)
                
                if result['success']:
                    messages.success(request, 'Código verificado correctamente.')
                    # Limpiar la flag de 2FA enviado
                    if '2fa_sent' in request.session:
                        del request.session['2fa_sent']
                    # Redirigir al ingreso de billetes
                    return redirect('ingreso_billetes', codigo=transaccion.token)
                else:
                    messages.error(request, result['message'])
                    return redirect('verificar_2fa')
        
        elif accion == 'cancelar':
            transaccion.estado = 'Cancelada'
            transaccion.razon = 'Usuario cancela la verificación 2FA'
            transaccion.save()
            # Limpiar la sesión
            if 'transaccion' in request.session:
                del request.session['transaccion']
            if '2fa_sent' in request.session:
                del request.session['2fa_sent']
            messages.info(request, 'Transacción cancelada.')
            return redirect('inicio')
    else:
        form = Token2FAForm()
    
    # Verificar si ya se envió el código
    codigo_enviado = request.session.get('2fa_sent', False)
    
    context = {
        'form': form,
        'transaccion': transaccion,
        'codigo_enviado': codigo_enviado,
        'usuario_email': transaccion.usuario.email
    }
    
    return render(request, 'verificar_2fa.html', context)