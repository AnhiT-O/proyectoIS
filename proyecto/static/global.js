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

// Función para manejar botones de activar/seleccionar sin recargar página
function manejarBotonesActivar() {
    const botonesActivar = document.querySelectorAll('.btn-activar');
    
    botonesActivar.forEach(function(boton) {
        boton.addEventListener('click', function(event) {
            event.preventDefault(); // Prevenir el envío normal del formulario
            
            const form = boton.closest('form');
            if (!form) return;
            
            // Deshabilitar el botón temporalmente
            const textoOriginal = boton.innerHTML;
            boton.disabled = true;
            boton.innerHTML = 'Procesando...';
            
            // Preparar datos del formulario
            const formData = new FormData(form);
            const url = form.action || window.location.href;
            const method = form.method || 'POST';
            
            // Realizar petición AJAX
            fetch(url, {
                method: method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (response.ok) {
                    return response.json().catch(() => {
                        // Si no es JSON, recargar la página para mostrar la respuesta
                        window.location.reload();
                        return null;
                    });
                } else {
                    throw new Error('Error en la respuesta del servidor');
                }
            })
            .then(data => {
                if (data) {
                    // Manejar respuesta JSON
                    if (data.success) {
                        // Mostrar mensaje de éxito
                        mostrarAlerta('success', data.message || 'Acción realizada correctamente');
                        
                        // Actualizar la interfaz si es necesario
                        if (data.reload) {
                            setTimeout(() => window.location.reload(), 1500);
                        } else if (data.redirect) {
                            setTimeout(() => window.location.href = data.redirect, 1500);
                        } else {
                            // Actualizar el botón o el estado visual
                            actualizarEstadoBoton(boton, data);
                        }
                    } else {
                        mostrarAlerta('error', data.message || 'Error al realizar la acción');
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                mostrarAlerta('error', 'Error al procesar la solicitud');
            })
            .finally(() => {
                // Restaurar el botón
                boton.disabled = false;
                boton.innerHTML = textoOriginal;
            });
        });
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

