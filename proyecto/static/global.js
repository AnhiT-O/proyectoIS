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
    }
});