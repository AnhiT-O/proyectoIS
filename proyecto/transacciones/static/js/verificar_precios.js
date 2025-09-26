// Función para verificar cambios en precios
function verificarCambiosPrecios() {
    const monedaId = document.getElementById('moneda_id').value;
    if (!monedaId) return; // Si no hay moneda seleccionada, no verificar
    
    fetch(`/monedas/verificar-cambios/${monedaId}/`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.hubo_cambio) {
            Swal.fire({
                title: '¡Atención!',
                html: `Los precios de la moneda han cambiado:<br><br>
                    <b>Precio de Compra:</b><br>
                    Antes: ${data.valores_anteriores.precio_compra.toLocaleString('es')} Gs.<br>
                    Ahora: ${data.valores_actuales.precio_compra.toLocaleString('es')} Gs.<br><br>
                    <b>Precio de Venta:</b><br>
                    Antes: ${data.valores_anteriores.precio_venta.toLocaleString('es')} Gs.<br>
                    Ahora: ${data.valores_actuales.precio_venta.toLocaleString('es')} Gs.`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Continuar con nuevos precios',
                cancelButtonText: 'Cancelar operación'
            }).then((result) => {
                if (!result.isConfirmed) {
                    window.location.href = '/';
                }
            });
        }
    })
    .catch(error => console.error('Error:', error));
}

// Iniciar verificación periódica cada 5 segundos
setInterval(verificarCambiosPrecios, 5000);