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
        alert('Redirigiendo a la página de venta de monedas...');
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