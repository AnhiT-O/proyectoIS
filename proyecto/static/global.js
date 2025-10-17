function toggleAdminMenu(event) {
    event.preventDefault();
    event.stopPropagation();
    
    const menu = document.getElementById('adminMenu');
    menu.classList.toggle('show');
}

// Cerrar el menú al hacer clic fuera de él
document.addEventListener('click', function(event) {
    const panelGestiones = document.querySelector('.panel-gestiones');
    const menu = document.getElementById('adminMenu');
    
    if (panelGestiones && menu && !panelGestiones.contains(event.target)) {
        menu.classList.remove('show');
    }
});

// Cerrar el menú al presionar Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const menu = document.getElementById('adminMenu');
        if (menu) {
            menu.classList.remove('show');
        }
        
        // También cerrar el pop-up de operaciones si está abierto
        const popup = document.getElementById('popup-operaciones');
        if (popup && popup.style.display === 'flex') {
            cerrarPopupOperaciones();
        }
    }
});

// Funciones para el pop-up de operaciones
function mostrarPopupOperaciones(event) {
    event.preventDefault();
    const popup = document.getElementById('popup-operaciones');
    if (popup) {
        popup.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Prevenir scroll del fondo
    }
}

function cerrarPopupOperaciones() {
    const popup = document.getElementById('popup-operaciones');
    if (popup) {
        popup.style.display = 'none';
        document.body.style.overflow = 'auto'; // Restaurar scroll
    }
}

function seleccionarOperacion(tipo) {
    if (tipo === 'comprar') {
        window.location.href = '/operaciones/comprar/';
    } else if (tipo === 'vender') {
        window.location.href = '/operaciones/vender/';
    }
    cerrarPopupOperaciones();
}

// Cerrar popup al hacer clic en el fondo
document.addEventListener('click', function(event) {
    const popup = document.getElementById('popup-operaciones');
    if (popup && event.target === popup) {
        cerrarPopupOperaciones();
    }
});

// Función para ocultar alertas automáticamente después de 5 segundos
function ocultarAlertasAutomaticamente() {
    const alertas = document.querySelectorAll('.zona-alertas .alerta-success, .zona-alertas .alerta-error, .zona-alertas .alerta-info, .zona-alertas .alerta-warning');
    
    alertas.forEach(function(alerta) {
        // Agregar animación de desvanecimiento después de 5 segundos
        setTimeout(function() {
            alerta.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
            alerta.style.opacity = '0';
            alerta.style.transform = 'translateY(-20px)';
            
            // Remover completamente el elemento después de la animación
            setTimeout(function() {
                if (alerta.parentNode) {
                    alerta.parentNode.removeChild(alerta);
                }
            }, 500);
        }, 5000);
    });
}

// Función para mostrar alertas dinámicamente
function mostrarAlerta(tipo, mensaje) {
    const zonaAlertas = document.querySelector('.zona-alertas') || crearZonaAlertas();
    
    const alerta = document.createElement('div');
    alerta.className = `alerta-${tipo}`;
    alerta.textContent = mensaje;
    
    zonaAlertas.appendChild(alerta);
    
    // Ocultar automáticamente después de 5 segundos
    setTimeout(() => {
        alerta.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
        alerta.style.opacity = '0';
        alerta.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
            if (alerta.parentNode) {
                alerta.parentNode.removeChild(alerta);
            }
        }, 500);
    }, 5000);
}

// Función para crear zona de alertas si no existe
function crearZonaAlertas() {
    const zonaAlertas = document.createElement('div');
    zonaAlertas.className = 'zona-alertas';
    document.body.appendChild(zonaAlertas);
    return zonaAlertas;
}

// Función para actualizar el estado visual del botón
function actualizarEstadoBoton(boton, data) {
    // Si el botón cambió de estado (ej: activar/desactivar)
    if (data.nuevo_estado !== undefined) {
        const form = boton.closest('form');
        const textoBoton = boton.textContent.trim();
        
        // Cambiar clase y texto del botón según el nuevo estado
        if (data.nuevo_estado === 'activo') {
            boton.className = boton.className.replace('btn-activar', 'btn-desactivar');
            boton.textContent = textoBoton.replace('Activar', 'Desactivar').replace('Desbloquear', 'Bloquear').replace('Seleccionar', 'Seleccionado');
        } else if (data.nuevo_estado === 'inactivo') {
            boton.className = boton.className.replace('btn-desactivar', 'btn-activar');
            boton.textContent = textoBoton.replace('Desactivar', 'Activar').replace('Bloquear', 'Desbloquear').replace('Seleccionado', 'Seleccionar');
        }
        
        // Actualizar campos hidden del formulario si existen
        const estadoInput = form.querySelector('input[name="cambiar_estado"]');
        const accionInput = form.querySelector('input[name="accion"]');
        
        if (estadoInput) {
            estadoInput.value = data.nuevo_estado === 'activo' ? 'desactivar' : 'activar';
        }
        
        if (accionInput && accionInput.value.includes('seleccionar')) {
            accionInput.value = data.nuevo_estado === 'activo' ? 'deseleccionar_medio' : 'seleccionar_medio';
        }
    }
}

// Ejecutar la función cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    ocultarAlertasAutomaticamente();
    manejarBotonesActivar();
});

