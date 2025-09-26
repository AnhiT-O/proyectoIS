// Función para verificar cambios en los precios
function verificarCambiosPrecios(monedaId) {
    fetch(`/transacciones/operaciones/verificar-cambios/${transaccionId}/`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.hubo_cambio && data.primera_operacion) {
            // Mostrar alerta con Sweet Alert 2
            Swal.fire({
                title: '¡Atención!',
                html: `Los precios han cambiado:<br><br>
                      <strong>Precio de Compra:</strong><br>
                      Anterior: ${data.precios_anteriores.compra.toLocaleString()} Gs.<br>
                      Actual: ${data.precios_actuales.compra.toLocaleString()} Gs.<br><br>
                      <strong>Precio de Venta:</strong><br>
                      Anterior: ${data.precios_anteriores.venta.toLocaleString()} Gs.<br>
                      Actual: ${data.precios_actuales.venta.toLocaleString()} Gs.`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Continuar con nuevos precios',
                cancelButtonText: 'Cancelar operación'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Actualizar precios iniciales en sesión
                    actualizarPreciosIniciales(monedaId);
                } else {
                    // Redirigir al inicio
                    window.location.href = '/';
                }
            });
        }
    });
}

// Función para actualizar precios iniciales
function actualizarPreciosIniciales(monedaId) {
    fetch(`/monedas/actualizar-precios/${monedaId}/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    });
}

// Iniciar verificación cada 5 segundos
function iniciarVerificacion(monedaId) {
    setInterval(() => verificarCambiosPrecios(monedaId), 5000);
}