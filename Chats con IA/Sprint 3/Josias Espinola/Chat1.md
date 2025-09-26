Josias-Esp: Necesito que en #file:base.html en el apartado "zona-usuario" crees un acceso para el usuario y el administrador a un historial de transacciones, el template de las transacciones lo debes crear en #file:usuarios en un archivo html nuevo, quiero que la estetica y la apariencia sea igual a #file:cliente_lista.html . Los siguientes datos que debe contener la transaccion debes extraelos del sistema: usuario que opera en nombre del cliente, el cliente que realizo la operacion, numero de documento del cliente, informacion de contacto del cliente, el nombre de la divisa comprada y vendida, monto de la divisa original, monto de la divisa resultante de la conversion. hora y fecha de la operacion, tipo de cambio aplicado, comisiones aplicadas. Luego los siguientes datos aun no estan implementados en el sistema pero quiero que crees los campos para luego extraerlos del sistema, los siguientes datos son el tipo de operacion si es compra o venta de divisa y el estado de la transaccion

GitHub Copilot: # Solución para implementar historial de transacciones

Voy a crear una solución en tres pasos:
1. Modificar `base.html` para agregar el acceso al historial de transacciones
2. Crear un nuevo template para visualizar el historial de transacciones

## Paso a paso:
1. Añadir un enlace al historial de transacciones en la barra de navegación para usuarios autenticados
2. Crear un nuevo template para mostrar las transacciones con diseño similar al de cliente_lista.html
3. Incluir todos los campos solicitados en la visualización de transacciones

### [base.html](file:///home/josias/Documentos/proyectoIS/proyecto/templates/base.html)

Modificar la zona de usuario para agregar el acceso al historial de transacciones:

````html
<!DOCTYPE html>
<html lang="es">
<head>
    <!-- ...existing code... -->
</head>
<body>
    <!-- Barra de navegación -->
    {% block navbar %}
    <nav class="zona-barra">
        <div class="barra-contenido">
            <a href="{% url 'inicio' %}" class="barra-logo">
                💰 Global Exchange
            </a>
            
            <div class="barra-navegacion">
                {% if user.is_authenticated %}
                    <div class="zona-usuario">
                        <span class="usuario-nombre">Hola, {{ user.first_name }}!</span>

                        <!-- Panel de Administración basado en permisos -->
                        {% if perms.usuarios or perms.clientes or perms.roles or perms.monedas %}
                            <div class="panel-gestiones">
                                <a href="#" class="btn-panel" onclick="toggleAdminMenu(event)">
                                    ⚙️ Panel de Gestiones
                                </a>
                                <div class="gestion-menu" id="adminMenu">
                                    <!-- ...existing code... -->
                                    
                                    <!-- Historial de Transacciones para Administradores -->
                                    <a href="{% url 'usuarios:historial_transacciones' %}" class="gestion-seleccion">
                                        📊 Historial de Transacciones
                                    </a>
                                </div>
                            </div>
                        {% endif %}
                        
                        <!-- ...existing code... -->
                        
                        <!-- Historial de Transacciones para todos los usuarios -->
                        <a href="{% url 'usuarios:historial_transacciones' %}" class="btn-panel">
                            📝 Historial de Transacciones
                        </a>
                        
                        <a href="{% url 'usuarios:perfil' %}" class="btn-secundario">
                            👤 Mi Perfil
                        </a>
                        <a href="{% url 'logout' %}" class="btn-primario">
                             Cerrar Sesión
                        </a>
                    </div>
                {% else %}
                    <!-- ...existing code... -->
                {% endif %}
            </div>
        </div>
    </nav>
    {% endblock %}

    <!-- ...existing code... -->
</body>
</html>
````

### [historial_transacciones.html](file:///home/josias/Documentos/proyectoIS/proyecto/usuarios/templates/usuarios/historial_transacciones.html)

Crear un nuevo template para el historial de transacciones:

````html
{% extends 'base.html' %}
{% load static %}

{% block title %}Historial de Transacciones - Global Exchange{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'claro/gestion.css' %}" media="(prefers-color-scheme: light)">
<link rel="stylesheet" href="{% static 'oscuro/gestion.css' %}" media="(prefers-color-scheme: dark)">
{% endblock %}

{% block content %}
<div class="contenido">
    <div class="gestion-cabecera">
        <h2>Historial de Transacciones</h2>
    </div>
    <!-- Formulario de búsqueda con nuevo estilo -->
    <div class="zona-busqueda">
        <form method="get" class="busqueda-form">
            <div class="campo-busqueda">
                <input type="text" 
                       name="busqueda" 
                       class="texto-busqueda" 
                       value="{{ busqueda }}" 
                       placeholder="Buscar por cliente o documento">
            </div>
            <div class="campo-filtro">
                <select name="tipo_operacion" class="select-filtro">
                    <option value="">Tipo de operación</option>
                    <option value="compra" {% if tipo_operacion == 'compra' %}selected{% endif %}>Compra</option>
                    <option value="venta" {% if tipo_operacion == 'venta' %}selected{% endif %}>Venta</option>
                </select>
            </div>
            <div class="campo-filtro">
                <select name="estado" class="select-filtro">
                    <option value="">Estado</option>
                    <option value="completada" {% if estado == 'completada' %}selected{% endif %}>Completada</option>
                    <option value="pendiente" {% if estado == 'pendiente' %}selected{% endif %}>Pendiente</option>
                    <option value="cancelada" {% if estado == 'cancelada' %}selected{% endif %}>Cancelada</option>
                </select>
            </div>
            <div class="botones-busqueda">
                <button type="submit" class="btn-buscar">
                    Buscar
                </button>
                {% if busqueda or tipo_operacion or estado %}
                <a href="{% url 'usuarios:historial_transacciones' %}" class="btn-limpiar">
                    Limpiar
                </a>
                {% endif %}
            </div>
        </form>
    </div>

    <div class="zona-conteo">
        <div class="conteo-info">
            Total de transacciones: <span class="conteo">{{ transacciones|length }}</span>
            {% if busqueda or tipo_operacion or estado %}
                <span style="margin-left: 1rem; color: #6c757d;">
                    ({{ transacciones|length }} resultado{{ transacciones|length|pluralize }}
                    {% if busqueda %}para "{{ busqueda }}"{% endif %}
                    {% if tipo_operacion %}con operación {{ tipo_operacion }}{% endif %}
                    {% if estado %}en estado {{ estado }}{% endif %})
                </span>
            {% endif %}
        </div>
    </div>
    <table class="gestion-tabla">
        <thead>
            <tr>
                <th style="width: 10%">Fecha</th>
                <th style="width: 14%">Cliente</th>
                <th style="width: 14%">Operador</th>
                <th style="width: 20%">Divisas (Origen → Destino)</th>
                <th style="width: 14%">Montos</th>
                <th style="width: 10%">Tipo Cambio</th>
                <th style="width: 8%">Comisión</th>
                <th style="width: 10%">Estado</th>
            </tr>
        </thead>
        <tbody>
            {% for transaccion in transacciones %}
            <tr>
                <td>
                    {{ transaccion.fecha|date:"d/m/Y" }}<br>
                    <small>{{ transaccion.hora|time:"H:i" }}</small>
                </td>
                <td>
                    <strong>{{ transaccion.cliente.nombre }}</strong><br>
                    <small>{{ transaccion.cliente.get_tipoDocCliente_display }}: {{ transaccion.cliente.docCliente }}</small>
                </td>
                <td>
                    {{ transaccion.operador.get_full_name }}
                </td>
                <td>
                    <strong>{{ transaccion.divisa_origen.nombre }}</strong> → 
                    <strong>{{ transaccion.divisa_destino.nombre }}</strong><br>
                    <small>{{ transaccion.tipo_operacion|title }}</small>
                </td>
                <td>
                    <strong>Origen:</strong> {{ transaccion.monto_origen }} {{ transaccion.divisa_origen.codigo }}<br>
                    <strong>Destino:</strong> {{ transaccion.monto_destino }} {{ transaccion.divisa_destino.codigo }}
                </td>
                <td>
                    {{ transaccion.tipo_cambio }}
                </td>
                <td>
                    {{ transaccion.comision }}%
                </td>
                <td>
                    <span class="estado-{{ transaccion.estado|lower }}">
                        {{ transaccion.estado|title }}
                    </span>
                </td>
            </tr>
            {% empty %}
            <tr>
                <td colspan="8">
                    {% if busqueda or tipo_operacion or estado %}
                        No se encontraron transacciones que coincidan con los filtros aplicados.
                    {% else %}
                        No hay transacciones registradas.
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}

{% block extra_js %}
<script>
    // Script adicional para el historial de transacciones si es necesario
</script>
{% endblock %}
````

Este código implementa:
1. Un enlace al historial de transacciones tanto para usuarios normales como para administradores
2. Un nuevo template para visualizar el historial de transacciones con filtros de búsqueda
3. Campos para mostrar toda la información solicitada incluyendo:
   - Usuario operador
   - Cliente y sus datos
   - Divisas origen y destino
   - Montos de la operación
   - Tipo de cambio
   - Comisiones
   - Tipo de operación (compra/venta)
   - Estado de la transacción (pendiente/completada/cancelada)

El diseño mantiene la misma estética que el template cliente_lista.html como fue solicitado.

Se realizaron cambios.

Josias-Esp: Crea las urls y archivos necesarios para que se puede acceder en el sistema

GitHub Copilot: # Solución para implementar historial de transacciones

Para completar la implementación del historial de transacciones, necesitamos crear las URLs y los archivos necesarios para que se pueda acceder a esta funcionalidad en el sistema.

Voy a trabajar en tres archivos:
1. Crear el archivo de vista para el historial de transacciones
2. Actualizar las URLs en la aplicación de usuarios
3. Crear un modelo para las transacciones (si no existe)

## Paso a paso:

### [views.py](file:///home/josias/Documentos/proyectoIS/proyecto/usuarios/views.py)

Primero, vamos a añadir la vista para el historial de transacciones:

````python
# ...existing code...

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
# Importar el modelo de Transaccion (suponiendo que existe en una app 'transacciones')
from transacciones.models import Transaccion

@login_required
def historial_transacciones(request):
    """
    Vista para mostrar el historial de transacciones según los permisos del usuario.
    Los administradores ven todas las transacciones, los usuarios normales solo las suyas.
    """
    # Parámetros de búsqueda y filtrado
    busqueda = request.GET.get('busqueda', '')
    tipo_operacion = request.GET.get('tipo_operacion', '')
    estado = request.GET.get('estado', '')
    
    # Base de la consulta según permisos
    if request.user.has_perm('transacciones.view_all_transacciones'):
        # Administradores ven todas las transacciones
        transacciones = Transaccion.objects.all()
    else:
        # Usuarios normales ven solo las transacciones que ellos operaron
        transacciones = Transaccion.objects.filter(operador=request.user)
    
    # Aplicar filtros de búsqueda
    if busqueda:
        transacciones = transacciones.filter(
            Q(cliente__nombre__icontains=busqueda) |
            Q(cliente__docCliente__icontains=busqueda)
        )
    
    if tipo_operacion:
        transacciones = transacciones.filter(tipo_operacion=tipo_operacion)
        
    if estado:
        transacciones = transacciones.filter(estado=estado)
    
    # Ordenar por fecha descendente (más reciente primero)
    transacciones = transacciones.order_by('-fecha', '-hora')
    
    context = {
        'transacciones': transacciones,
        'busqueda': busqueda,
        'tipo_operacion': tipo_operacion,
        'estado': estado,
    }
    
    return render(request, 'usuarios/historial_transacciones.html', context)

# ...existing code...
````

### [urls.py](file:///home/josias/Documentos/proyectoIS/proyecto/usuarios/urls.py)

A continuación, actualizamos las URLs de la aplicación de usuarios para incluir la URL del historial de transacciones:

````python
from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # ...existing code...
    
    # Añadir la URL para el historial de transacciones
    path('historial-transacciones/', views.historial_transacciones, name='historial_transacciones'),
    
    # ...existing code...
]
````

### [models.py](file:///home/josias/Documentos/proyectoIS/proyecto/transacciones/models.py)

Finalmente, vamos a crear un modelo para las transacciones (si no existe ya). Primero, necesitamos crear una nueva aplicación llamada 'transacciones' si no existe:

````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
from django.db import models
from django.conf import settings
from clientes.models import Cliente
from monedas.models import Moneda

class Transaccion(models.Model):
    """
    Modelo para almacenar información de transacciones de cambio de divisas.
    """
    # Opciones para el tipo de operación
    TIPO_OPERACION_CHOICES = [
        ('compra', 'Compra'),
        ('venta', 'Venta'),
    ]
    
    # Opciones para el estado de la transacción
    ESTADO_CHOICES = [
        ('completada', 'Completada'),
        ('pendiente', 'Pendiente'),
        ('cancelada', 'Cancelada'),
    ]
    
    # Relaciones con otros modelos
    operador = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='transacciones_operadas',
        help_text='Usuario que realizó la operación'
    )
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.PROTECT, 
        related_name='transacciones',
        help_text='Cliente que realizó la transacción'
    )
    divisa_origen = models.ForeignKey(
        Moneda, 
        on_delete=models.PROTECT, 
        related_name='transacciones_origen',
        help_text='Divisa original de la transacción'
    )
    divisa_destino = models.ForeignKey(
        Moneda, 
        on_delete=models.PROTECT, 
        related_name='transacciones_destino',
        help_text='Divisa resultante de la transacción'
    )
    
    # Detalles de la transacción
    fecha = models.DateField(auto_now_add=True, help_text='Fecha de la transacción')
    hora = models.TimeField(auto_now_add=True, help_text='Hora de la transacción')
    monto_origen = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        help_text='Monto en la divisa original'
    )
    monto_destino = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        help_text='Monto en la divisa resultante'
    )
    tipo_cambio = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        help_text='Tipo de cambio aplicado a la operación'
    )
    comision = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        help_text='Porcentaje de comisión aplicado'
    )
    tipo_operacion = models.CharField(
        max_length=10, 
        choices=TIPO_OPERACION_CHOICES, 
        default='compra',
        help_text='Indica si es una operación de compra o venta'
    )
    estado = models.CharField(
        max_length=10, 
        choices=ESTADO_CHOICES, 
        default='pendiente',
        help_text='Estado actual de la transacción'
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
        permissions = [
            ('view_all_transacciones', 'Puede ver todas las transacciones'),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_operacion_display()} - {self.cliente.nombre} - {self.fecha}"
    
    def get_total_comision(self):
        """Calcula el monto total de la comisión"""
        return (self.monto_origen * self.comision / 100)
````

### [admin.py](file:///home/josias/Documentos/proyectoIS/proyecto/transacciones/admin.py)

Para poder administrar las transacciones desde el panel de administración de Django:

````python
from django.contrib import admin
from .models import Transaccion

@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'operador', 'fecha', 'hora', 
                   'divisa_origen', 'divisa_destino', 'monto_origen', 
                   'monto_destino', 'tipo_operacion', 'estado')
    list_filter = ('estado', 'tipo_operacion', 'fecha')
    search_fields = ('cliente__nombre', 'cliente__docCliente', 
                    'operador__username', 'operador__first_name')
    date_hierarchy = 'fecha'
````

### [apps.py](file:///home/josias/Documentos/proyectoIS/proyecto/transacciones/apps.py)

Creamos el archivo de configuración de la aplicación:

````python
from django.apps import AppConfig

class TransaccionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transacciones'
    verbose_name = 'Gestión de Transacciones'
````

### [__init__.py](file:///home/josias/Documentos/proyectoIS/proyecto/transacciones/__init__.py)

No olvides crear este archivo vacío para que Python reconozca la carpeta como un paquete:

````python
# Este archivo puede estar vacío
````

### [settings.py](file:///home/josias/Documentos/proyectoIS/proyecto/proyecto/settings.py)

Finalmente, necesitas registrar la nueva aplicación en el archivo de configuración del proyecto:

````python
# ...existing code...

INSTALLED_APPS = [
    # ...existing code...
    'transacciones.apps.TransaccionesConfig',  # Añadir la nueva aplicación de transacciones
    # ...existing code...
]

# ...existing code...
````

Con estos cambios, tendrás:
1. Una nueva aplicación "transacciones" con su modelo Transaccion
2. Una vista para ver el historial de transacciones
3. Las URLs necesarias para acceder a esta funcionalidad
4. La configuración en el panel de administración

Ahora, debes ejecutar las migraciones para crear las tablas en la base de datos:
```
python manage.py makemigrations transacciones
python manage.py migrate
```

Se realizaron cambios.

Josias-Esp: No se puede usar el admin de django, utiliza los permisos correspondientes de el administrador ya creado en el sistema

GitHub Copilot: # Solución para implementar historial de transacciones usando permisos existentes

Entendido, modificaré la solución para trabajar con los permisos existentes en el sistema en lugar de usar el admin de Django. Voy a enfocarme en mantener la consistencia con el sistema actual.

## Paso a paso:

### [models.py](file:///home/josias/Documentos/proyectoIS/proyecto/transacciones/models.py)

Primero, creamos el modelo de transacciones:

````python
from django.db import models
from django.conf import settings
from clientes.models import Cliente
from monedas.models import Moneda

class Transaccion(models.Model):
    """
    Modelo para almacenar información de transacciones de cambio de divisas.
    """
    # Opciones para el tipo de operación
    TIPO_OPERACION_CHOICES = [
        ('compra', 'Compra'),
        ('venta', 'Venta'),
    ]
    
    # Opciones para el estado de la transacción
    ESTADO_CHOICES = [
        ('completada', 'Completada'),
        ('pendiente', 'Pendiente'),
        ('cancelada', 'Cancelada'),
    ]
    
    # Relaciones con otros modelos
    operador = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='transacciones_operadas',
        help_text='Usuario que realizó la operación'
    )
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.PROTECT, 
        related_name='transacciones',
        help_text='Cliente que realizó la transacción'
    )
    divisa_origen = models.ForeignKey(
        Moneda, 
        on_delete=models.PROTECT, 
        related_name='transacciones_origen',
        help_text='Divisa original de la transacción'
    )
    divisa_destino = models.ForeignKey(
        Moneda, 
        on_delete=models.PROTECT, 
        related_name='transacciones_destino',
        help_text='Divisa resultante de la transacción'
    )
    
    # Detalles de la transacción
    fecha = models.DateField(auto_now_add=True, help_text='Fecha de la transacción')
    hora = models.TimeField(auto_now_add=True, help_text='Hora de la transacción')
    monto_origen = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        help_text='Monto en la divisa original'
    )
    monto_destino = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        help_text='Monto en la divisa resultante'
    )
    tipo_cambio = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        help_text='Tipo de cambio aplicado a la operación'
    )
    comision = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        help_text='Porcentaje de comisión aplicado'
    )
    tipo_operacion = models.CharField(
        max_length=10, 
        choices=TIPO_OPERACION_CHOICES, 
        default='compra',
        help_text='Indica si es una operación de compra o venta'
    )
    estado = models.CharField(
        max_length=10, 
        choices=ESTADO_CHOICES, 
        default='pendiente',
        help_text='Estado actual de la transacción'
    )
    
    class Meta:
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
        permissions = [
            ('ver_todas_transacciones', 'Puede ver todas las transacciones'),
            ('gestionar_transacciones', 'Puede gestionar transacciones'),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_operacion_display()} - {self.cliente.nombre} - {self.fecha}"
    
    def get_total_comision(self):
        """Calcula el monto total de la comisión"""
        return (self.monto_origen * self.comision / 100)
````

### [apps.py](file:///home/josias/Documentos/proyectoIS/proyecto/transacciones/apps.py)

````python
from django.apps import AppConfig

class TransaccionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transacciones'
    verbose_name = 'Gestión de Transacciones'
````

### [__init__.py](file:///home/josias/Documentos/proyectoIS/proyecto/transacciones/__init__.py)

````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
# Este archivo puede estar vacío
````

### [settings.py](file:///home/josias/Documentos/proyectoIS/proyecto/proyecto/settings.py)

````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
````python
# ...existing code...

INSTALLED_APPS = [
    # ...existing code...
    'transacciones.apps.TransaccionesConfig',  # Añadir la nueva aplicación de transacciones
    # ...existing code...
]

# ...existing code...
````

### [views.py](file:///home/josias/Documentos/proyectoIS/proyecto/usuarios/views.py)

````python
````python
````python
````python
````python
````python
````python
````python
````python
# ...existing code...

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
from transacciones.models import Transaccion

@login_required
def historial_transacciones(request):
    """
    Vista para mostrar el historial de transacciones según los permisos del usuario.
    """
    # Parámetros de búsqueda y filtrado
    busqueda = request.GET.get('busqueda', '')
    tipo_operacion = request.GET.get('tipo_operacion', '')
    estado = request.GET.get('estado', '')
    
    # Base de la consulta según permisos
    if request.user.has_perm('transacciones.ver_todas_transacciones'):
        # Usuarios con permiso ven todas las transacciones
        transacciones = Transaccion.objects.all()
    else:
        # Usuarios normales ven solo las transacciones que ellos operaron
        transacciones = Transaccion.objects.filter(operador=request.user)
    
    # Aplicar filtros de búsqueda
    if busqueda:
        transacciones = transacciones.filter(
            Q(cliente__nombre__icontains=busqueda) |
            Q(cliente__docCliente__icontains=busqueda)
        )
    
    if tipo_operacion:
        transacciones = transacciones.filter(tipo_operacion=tipo_operacion)
        
    if estado:
        transacciones = transacciones.filter(estado=estado)
    
    # Ordenar por fecha descendente (más reciente primero)
    transacciones = transacciones.order_by('-fecha', '-hora')
    
    context = {
        'transacciones': transacciones,
        'busqueda': busqueda,
        'tipo_operacion': tipo_operacion,
        'estado': estado,
    }
    
    return render(request, 'usuarios/historial_transacciones.html', context)

# ...existing code...
````

### [urls.py](file:///home/josias/Documentos/proyectoIS/proyecto/usuarios/urls.py)

````python
# ...existing code...

urlpatterns = [
    # ...existing code...
    
    # Añadir la URL para el historial de transacciones
    path('historial-transacciones/', views.historial_transacciones, name='historial_transacciones'),
    
    # ...existing code...
]
````

### [historial_transacciones.html](file:///home/josias/Documentos/proyectoIS/proyecto/usuarios/templates/usuarios/historial_transacciones.html)

````html
````html
````html
````html
````html
````html
````html
````html
````html
````html
````html
````html
{% extends 'base.html' %}
{% load static %}

{% block title %}Historial de Transacciones - Global Exchange{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'claro/gestion.css' %}" media="(prefers-color-scheme: light)">
<link rel="stylesheet" href="{% static 'oscuro/gestion.css' %}" media="(prefers-color-scheme: dark)">
{% endblock %}

{% block content %}
<div class="contenido">
    <div class="gestion-cabecera">
        <h2>Historial de Transacciones</h2>
        {% if perms.transacciones.gestionar_transacciones %}
        <a href="#" class="btn-primario">
            Nueva Transacción
        </a>
        {% endif %}
    </div>
    <!-- Formulario de búsqueda con nuevo estilo -->
    <div class="zona-busqueda">
        <form method="get" class="busqueda-form">
            <div class="campo-busqueda">
                <input type="text" 
                       name="busqueda" 
                       class="texto-busqueda" 
                       value="{{ busqueda }}" 
                       placeholder="Buscar por cliente o documento">
            </div>
            <div class="campo-filtro">
                <select name="tipo_operacion" class="select-filtro">
                    <option value="">Tipo de operación</option>
                    <option value="compra" {% if tipo_operacion == 'compra' %}selected{% endif %}>Compra</option>
                    <option value="venta" {% if tipo_operacion == 'venta' %}selected{% endif %}>Venta</option>
                </select>
            </div>
            <div class="campo-filtro">
                <select name="estado" class="select-filtro">
                    <option value="">Estado</option>
                    <option value="completada" {% if estado == 'completada' %}selected{% endif %}>Completada</option>
                    <option value="pendiente" {% if estado == 'pendiente' %}selected{% endif %}>Pendiente</option>
                    <option value="cancelada" {% if estado == 'cancelada' %}selected{% endif %}>Cancelada</option>
                </select>
            </div>
            <div class="botones-busqueda">
                <button type="submit" class="btn-buscar">
                    Buscar
                </button>
                {% if busqueda or tipo_operacion or estado %}
                <a href="{% url 'usuarios:historial_transacciones' %}" class="btn-limpiar">
                    Limpiar
                </a>
                {% endif %}
            </div>
        </form>
    </div>

    <div class="zona-conteo">
        <div class="conteo-info">
            Total de transacciones: <span class="conteo">{{ transacciones|length }}</span>
            {% if busqueda or tipo_operacion or estado %}
                <span style="margin-left: 1rem; color: #6c757d;">
                    ({{ transacciones|length }} resultado{{ transacciones|length|pluralize }}
                    {% if busqueda %}para "{{ busqueda }}"{% endif %}
                    {% if tipo_operacion %}con operación {{ tipo_operacion }}{% endif %}
                    {% if estado %}en estado {{ estado }}{% endif %})
                </span>
            {% endif %}
        </div>
    </div>
    <table class="gestion-tabla">
        <thead>
            <tr>
                <th style="width: 10%">Fecha</th>
                <th style="width: 14%">Cliente</th>
                <th style="width: 14%">Operador</th>
                <th style="width: 20%">Divisas (Origen → Destino)</th>
                <th style="width: 14%">Montos</th>
                <th style="width: 10%">Tipo Cambio</th>
                <th style="width: 8%">Comisión</th>
                <th style="width: 10%">Estado</th>
            </tr>
        </thead>
        <tbody>
            {% for transaccion in transacciones %}
            <tr>
                <td>
                    {{ transaccion.fecha|date:"d/m/Y" }}<br>
                    <small>{{ transaccion.hora|time:"H:i" }}</small>
                </td>
                <td>
                    <strong>{{ transaccion.cliente.nombre }}</strong><br>
                    <small>{{ transaccion.cliente.get_tipoDocCliente_display }}: {{ transaccion.cliente.docCliente }}</small>
                </td>
                <td>
                    {{ transaccion.operador.get_full_name }}
                </td>
                <td>
                    <strong>{{ transaccion.divisa_origen.nombre }}</strong> → 
                    <strong>{{ transaccion.divisa_destino.nombre }}</strong><br>
                    <small>{{ transaccion.get_tipo_operacion_display }}</small>
                </td>
                <td>
                    <strong>Origen:</strong> {{ transaccion.monto_origen }} {{ transaccion.divisa_origen.codigo }}<br>
                    <strong>Destino:</strong> {{ transaccion.monto_destino }} {{ transaccion.divisa_destino.codigo }}
                </td>
                <td>
                    {{ transaccion.tipo_cambio }}
                </td>
                <td>
                    {{ transaccion.comision }}%
                </td>
                <td>
                    <span class="estado-{{ transaccion.estado|lower }}">
                        {{ transaccion.get_estado_display }}
                    </span>
                </td>
            </tr>
            {% empty %}
            <tr>
                <td colspan="8">
                    {% if busqueda or tipo_operacion or estado %}
                        No se encontraron transacciones que coincidan con los filtros aplicados.
                    {% else %}
                        No hay transacciones registradas.
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
````

### [0001_initial.py](file:///home/josias/Documentos/proyectoIS/proyecto/transacciones/migrations/0001_initial.py)

Cuando ejecutes `python manage.py makemigrations`, se generará un archivo como este:

````python
````python
````python
````python
````python
````python
````python
````python
````python
# Generated automatically with makemigrations
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clientes', '0001_initial'),  # Ajusta según la última migración de clientes
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('monedas', '0001_initial'),  # Ajusta según la última migración de monedas
    ]

    operations = [
        migrations.CreateModel(
            name='Transaccion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(auto_now_add=True, help_text='Fecha de la transacción')),
                ('hora', models.TimeField(auto_now_add=True, help_text='Hora de la transacción')),
                ('monto_origen', models.DecimalField(decimal_places=2, help_text='Monto en la divisa original', max_digits=15)),
                ('monto_destino', models.DecimalField(decimal_places=2, help_text='Monto en la divisa resultante', max_digits=15)),
                ('tipo_cambio', models.DecimalField(decimal_places=4, help_text='Tipo de cambio aplicado a la operación', max_digits=10)),
                ('comision', models.DecimalField(decimal_places=2, help_text='Porcentaje de comisión aplicado', max_digits=5)),
                ('tipo_operacion', models.CharField(choices=[('compra', 'Compra'), ('venta', 'Venta')], default='compra', help_text='Indica si es una operación de compra o venta', max_length=10)),
                ('estado', models.CharField(choices=[('completada', 'Completada'), ('pendiente', 'Pendiente'), ('cancelada', 'Cancelada')], default='pendiente', help_text='Estado actual de la transacción', max_length=10)),
                ('cliente', models.ForeignKey(help_text='Cliente que realizó la transacción', on_delete=django.db.models.deletion.PROTECT, related_name='transacciones', to='clientes.cliente')),
                ('divisa_destino', models.ForeignKey(help_text='Divisa resultante de la transacción', on_delete=django.db.models.deletion.PROTECT, related_name='transacciones_destino', to='monedas.moneda')),
                ('divisa_origen', models.ForeignKey(help_text='Divisa original de la transacción', on_delete=django.db.models.deletion.PROTECT, related_name='transacciones_origen', to='monedas.moneda')),
                ('operador', models.ForeignKey(help_text='Usuario que realizó la operación', on_delete=django.db.models.deletion.PROTECT, related_name='transacciones_operadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Transacción',
                'verbose_name_plural': 'Transacciones',
                'permissions': [('ver_todas_transacciones', 'Puede ver todas las transacciones'), ('gestionar_transacciones', 'Puede gestionar transacciones')],
            },
        ),
    ]
````

### [gestion.css](file:///home/josias/Documentos/proyectoIS/proyecto/static/claro/gestion.css)

Asegúrate de que el CSS tenga los estilos para los estados de transacción:

````css
/* ...existing code... */

/* Estilos para los estados de las transacciones */
.estado-completada {
    padding: 3px 8px;
    background-color: #e0f7e0;
    color: #28a745;
    border-radius: 4px;
    font-weight: 500;
}

.estado-pendiente {
    padding: 3px 8px;
    background-color: #fff3cd;
    color: #856404;
    border-radius: 4px;
    font-weight: 500;
}

.estado-cancelada {
    padding: 3px 8px;
    background-color: #f8d7da;
    color: #721c24;
    border-radius: 4px;
    font-weight: 500;
}

/* ...existing code... */
````

### [gestion.css](file:///home/josias/Documentos/proyectoIS/proyecto/static/oscuro/gestion.css)

````css
````css
````css
/* ...existing code... */

/* Estilos para los estados de las transacciones en modo oscuro */
.estado-completada {
    padding: 3px 8px;
    background-color: #225122;
    color: #8fff8f;
    border-radius: 4px;
    font-weight: 500;
}

.estado-pendiente {
    padding: 3px 8px;
    background-color: #4d4000;
    color: #ffdb70;
    border-radius: 4px;
    font-weight: 500;
}

.estado-cancelada {
    padding: 3px 8px;
    background-color: #471217;
    color: #f8d7da;
    border-radius: 4px;
    font-weight: 500;
}

/* ...existing code... */
````

## Pasos finales de implementación:

Una vez que hayas agregado estos archivos, necesitas:

1. Registrar los permisos en los roles existentes:
   - Asigna el permiso `transacciones.ver_todas_transacciones` a los roles administrativos
   - Asigna el permiso `transacciones.gestionar_transacciones` a los roles que pueden crear/modificar transacciones

2. Ejecutar las migraciones para crear la tabla de transacciones:
   ```
   python manage.py makemigrations transacciones
   python manage.py migrate
   ```

Con estos cambios, has implementado:
1. Un modelo de Transaccion con todos los campos solicitados
2. Una vista para mostrar el historial de transacciones según permisos del usuario
3. Un template con diseño consistente que muestra toda la información
4. Los permisos necesarios para gestionar quién puede ver todas las transacciones

Esta implementación utiliza los permisos de Django para controlar el acceso, lo que es compatible con el sistema de roles existente en tu aplicación.

Se realizaron cambios.

Josias-Esp: Crea un filtro tipo lista como "tipo operacion" en #file:historial_transacciones.html y salga una lista de los clientes que hayan realizado una operacion para filtrar el historial, si ningun cliente a realizado una operacin la lista se desplegara en blanco

GitHub Copilot: # Solución: Añadir filtro de clientes en el historial de transacciones

Voy a modificar el archivo historial_transacciones.html para añadir un filtro tipo lista que muestre los clientes que han realizado operaciones.

### [historial_transacciones.html](file:///home/josias/Documentos/proyectoIS/proyecto/usuarios/templates/usuarios/historial_transacciones.html)

````html
{% extends 'base.html' %}
{% load static %}

{% block title %}Historial de Transacciones - Global Exchange{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'claro/gestion.css' %}" media="(prefers-color-scheme: light)">
<link rel="stylesheet" href="{% static 'oscuro/gestion.css' %}" media="(prefers-color-scheme: dark)">
{% endblock %}

{% block content %}
<div class="contenido">
    <div class="gestion-cabecera">
        <h2>Historial de Transacciones</h2>
        <p class="subtitulo">
            Revisa el historial completo de transacciones realizadas en la casa de cambios
        </p>
    </div>
    <!-- Formulario de búsqueda con nuevo estilo -->
    <div class="zona-busqueda">
        <form method="get" class="busqueda-form">
            <div class="campo-busqueda">
                <input type="text" 
                       name="busqueda" 
                       class="texto-busqueda" 
                       value="{{ busqueda }}" 
                       placeholder="Buscar por cliente o documento">
            </div>
            <!-- Filtro por cliente -->
            <div class="campo-filtro">
                <select name="cliente_id" class="select-filtro">
                    <option value="">Todos los clientes</option>
                    {% for cliente in clientes_con_transacciones %}
                        <option value="{{ cliente.id }}" {% if cliente_id|stringformat:"s" == cliente.id|stringformat:"s" %}selected{% endif %}>
                            {{ cliente.nombre }}
                        </option>
                    {% endfor %}
                </select>
            </div>
            <div class="campo-filtro">
                <select name="tipo_operacion" class="select-filtro">
                    <option value="">Tipo de operación</option>
                    <option value="compra" {% if tipo_operacion == 'compra' %}selected{% endif %}>Compra</option>
                    <option value="venta" {% if tipo_operacion == 'venta' %}selected{% endif %}>Venta</option>
                </select>
            </div>
            <div class="campo-filtro">
                <select name="estado" class="select-filtro">
                    <option value="">Estado</option>
                    <option value="pagada" {% if estado == 'pagada' %}selected{% endif %}>Pagada</option>
                    <option value="pendiente" {% if estado == 'pendiente' %}selected{% endif %}>Pendiente</option>
                    <option value="cancelada" {% if estado == 'cancelada' %}selected{% endif %}>Cancelada</option>
                    <option value="anulada" {% if estado == 'anulada' %}selected{% endif %}>Anulada</option>
                </select>
            </div>
            <div class="botones-busqueda">
                <button type="submit" class="btn-buscar">
                    Buscar
                </button>
                {% if busqueda or tipo_operacion or estado or cliente_id %}
                <a href="{% url 'usuarios:historial_transacciones' %}" class="btn-limpiar">
                    Limpiar
                </a>
                {% endif %}
            </div>
        </form>
    </div>

    <div class="zona-conteo">
        <div class="conteo-info">
            Total de transacciones: <span class="conteo">{{ transacciones|length }}</span>
            {% if busqueda or tipo_operacion or estado or cliente_id %}
                <span style="margin-left: 1rem; color: #6c757d;">
                    ({{ transacciones|length }} resultado{{ transacciones|length|pluralize }}
                    {% if busqueda %}para "{{ busqueda }}"{% endif %}
                    {% if cliente_id %}del cliente seleccionado{% endif %}
                    {% if tipo_operacion %}con operación {{ tipo_operacion }}{% endif %}
                    {% if estado %}en estado {{ estado }}{% endif %})
                </span>
            {% endif %}
        </div>
    </div>
    <table class="gestion-tabla">
        <!-- ...existing code... -->
    </table>
</div>
{% endblock %}

{% block extra_js %}
<script>
    // Script adicional para el historial de transacciones si es necesario
</script>
{% endblock %}
````

### [views.py](file:///home/josias/Documentos/proyectoIS/proyecto/usuarios/views.py)

También necesitamos modificar la vista para incluir la lista de clientes con transacciones y el filtro por cliente:

````python
# ...existing code...

@login_required
def historial_transacciones(request):
    """
    Vista para mostrar el historial de transacciones según los permisos del usuario.
    """
    # Parámetros de búsqueda y filtrado
    busqueda = request.GET.get('busqueda', '')
    tipo_operacion = request.GET.get('tipo_operacion', '')
    estado = request.GET.get('estado', '')
    cliente_id = request.GET.get('cliente_id', '')
    
    # Base de la consulta según permisos
    if request.user.has_perm('transacciones.ver_todas_transacciones'):
        # Usuarios con permiso ven todas las transacciones
        transacciones = Transaccion.objects.all()
        # Obtener clientes distintos que han realizado transacciones
        clientes_con_transacciones = Cliente.objects.filter(
            transacciones__isnull=False
        ).distinct()
    else:
        # Usuarios normales ven solo las transacciones que ellos operaron
        transacciones = Transaccion.objects.filter(operador=request.user)
        # Obtener clientes distintos de las transacciones que ha operado este usuario
        clientes_con_transacciones = Cliente.objects.filter(
            transacciones__operador=request.user
        ).distinct()
    
    # Aplicar filtros de búsqueda
    if busqueda:
        transacciones = transacciones.filter(
            Q(cliente__nombre__icontains=busqueda) |
            Q(cliente__docCliente__icontains=busqueda)
        )
    
    # Filtrar por cliente específico
    if cliente_id:
        transacciones = transacciones.filter(cliente_id=cliente_id)
    
    if tipo_operacion:
        transacciones = transacciones.filter(tipo_operacion=tipo_operacion)
        
    if estado:
        transacciones = transacciones.filter(estado=estado)
    
    # Ordenar por fecha descendente (más reciente primero)
    transacciones = transacciones.order_by('-fecha', '-hora')
    
    context = {
        'transacciones': transacciones,
        'clientes_con_transacciones': clientes_con_transacciones,
        'busqueda': busqueda,
        'tipo_operacion': tipo_operacion,
        'estado': estado,
        'cliente_id': cliente_id,
    }
    
    return render(request, 'usuarios/historial_transacciones.html', context)

# ...existing code...
````

Con estos cambios, se añadirá un nuevo filtro desplegable para seleccionar un cliente específico que haya realizado transacciones. Si ningún cliente ha realizado operaciones, la lista se mostrará vacía con solo la opción "Todos los clientes". El filtro funciona de manera similar a los otros filtros ya existentes.

No olvides asegurarte de importar el modelo Cliente en el archivo views.py:

````python
# En el inicio del archivo views.py
from django.db.models import Q
from transacciones.models import Transaccion
from clientes.models import Cliente
````

Se realizaron cambios.