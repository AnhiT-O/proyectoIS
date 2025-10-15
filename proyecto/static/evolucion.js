// Variables globales
let graficoEvolucion = null;
let datosActuales = [];
let rangoActual = 'mes';
let monedaConfig = {};

// Colores del tema
const COLORES = {
    violetaOscuro: '#667eea',    // Para compra
    violetaClaro: '#8b5cf6',     // Para venta
    fondo: 'rgba(102, 126, 234, 0.1)',
    grid: 'rgba(150, 150, 150, 0.2)'
};

// Función para inicializar con datos de la moneda
function inicializarEvolucion(monedaId, monedaNombre, monedaSimbolo) {
    monedaConfig = {
        id: monedaId,
        nombre: monedaNombre,
        simbolo: monedaSimbolo
    };
    
    inicializarGrafico();
    cargarDatos(rangoActual);
    configurarEventos();
}

// Configurar eventos de los botones de filtro
function configurarEventos() {
    const botonesFiltro = document.querySelectorAll('.btn-filtro');
    
    botonesFiltro.forEach(boton => {
        boton.addEventListener('click', function() {
            const nuevoRango = this.dataset.rango;
            
            // Actualizar botones activos
            botonesFiltro.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Cargar nuevos datos
            rangoActual = nuevoRango;
            cargarDatos(nuevoRango);
        });
    });
}

// Inicializar el gráfico
function inicializarGrafico() {
    const ctx = document.getElementById('graficoEvolucion').getContext('2d');
    
    graficoEvolucion = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Precio Compra',
                    data: [],
                    borderColor: COLORES.violetaOscuro,
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.4,
                    pointBackgroundColor: COLORES.violetaOscuro,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 8
                },
                {
                    label: 'Precio Venta',
                    data: [],
                    borderColor: COLORES.violetaClaro,
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.4,
                    pointBackgroundColor: COLORES.violetaClaro,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 8
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: COLORES.violetaOscuro,
                    borderWidth: 1,
                    displayColors: true,
                    callbacks: {
                        title: function(context) {
                            return 'Fecha: ' + context[0].label;
                        },
                        label: function(context) {
                            const valor = new Intl.NumberFormat('es-PY', {
                                style: 'currency',
                                currency: 'PYG',
                                minimumFractionDigits: 0
                            }).format(context.parsed.y);
                            return context.dataset.label + ': ' + valor;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Fecha',
                        font: {
                            weight: 'bold'
                        }
                    },
                    grid: {
                        color: COLORES.grid
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Valor en Guaraníes (PYG)',
                        font: {
                            weight: 'bold'
                        }
                    },
                    grid: {
                        color: COLORES.grid
                    },
                    ticks: {
                        callback: function(value) {
                            return new Intl.NumberFormat('es-PY').format(value);
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

// Cargar datos del servidor
function cargarDatos(rango) {
    mostrarLoading(true);
    
    fetch(`/monedas/${monedaConfig.id}/api-evolucion/?rango=${rango}`)
        .then(response => response.json())
        .then(data => {
            datosActuales = data.datos;
            actualizarGrafico(data.datos);
            actualizarTabla(data.datos);
            actualizarEstadisticas(data.datos);
            mostrarLoading(false);
        })
        .catch(error => {
            console.error('Error al cargar datos:', error);
            mostrarLoading(false);
            mostrarError('Error al cargar los datos de evolución');
        });
}

// Actualizar el gráfico con nuevos datos
function actualizarGrafico(datos) {
    const fechas = datos.map(d => d.fecha);
    const preciosCompra = datos.map(d => d.precio_compra);
    const preciosVenta = datos.map(d => d.precio_venta);
    
    graficoEvolucion.data.labels = fechas;
    graficoEvolucion.data.datasets[0].data = preciosCompra;
    graficoEvolucion.data.datasets[1].data = preciosVenta;
    
    graficoEvolucion.update('smooth');
}

// Actualizar la tabla con nuevos datos
function actualizarTabla(datos) {
    const tbody = document.getElementById('tabla-datos');
    tbody.innerHTML = '';
    
    // Mostrar datos en orden descendente (más recientes primero)
    const datosOrdenados = [...datos].reverse();
    
    datosOrdenados.forEach(dato => {
        const fila = document.createElement('tr');
        fila.innerHTML = `
            <td>${dato.fecha}</td>
            <td class="precio-compra">${formatearPrecio(dato.precio_compra)}</td>
            <td class="precio-venta">${formatearPrecio(dato.precio_venta)}</td>
        `;
        tbody.appendChild(fila);
    });
}

// Actualizar estadísticas
function actualizarEstadisticas(datos) {
    if (datos.length === 0) return;
    
    const datosOrdenados = [...datos].sort((a, b) => new Date(a.fecha_iso) - new Date(b.fecha_iso));
    const primero = datosOrdenados[0];
    const ultimo = datosOrdenados[datosOrdenados.length - 1];
    
    // Precios actuales
    document.getElementById('precio-actual-compra').textContent = formatearPrecio(ultimo.precio_compra);
    document.getElementById('precio-actual-venta').textContent = formatearPrecio(ultimo.precio_venta);
}

// Formatear precio
function formatearPrecio(precio) {
    return new Intl.NumberFormat('es-PY', {
        style: 'currency',
        currency: 'PYG',
        minimumFractionDigits: 0
    }).format(precio);
}

// Mostrar/ocultar loading
function mostrarLoading(mostrar) {
    const overlay = document.getElementById('loading-overlay');
    overlay.style.display = mostrar ? 'flex' : 'none';
}

// Mostrar error
function mostrarError(mensaje) {
    // Aquí podrías usar un sistema de notificaciones más sofisticado
    alert(mensaje);
}