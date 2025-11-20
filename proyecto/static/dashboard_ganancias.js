// Variables globales
let graficoGanancias = null;
let datosActuales = [];
let rangoActual = 'mes';
let monedaActual = null;

// Colores del tema
const COLORES = {
    principal: '#667eea',
    secundario: '#8b5cf6',
    exito: '#10b981',
    fondo: 'rgba(102, 126, 234, 0.1)',
    grid: 'rgba(150, 150, 150, 0.2)'
};

// Función para inicializar el dashboard
function inicializarDashboard() {
    inicializarGrafico();
    cargarDatos(rangoActual, monedaActual);
    configurarEventos();
}

// Configurar eventos de los controles
function configurarEventos() {
    // Botones de filtro temporal
    const botonesFiltro = document.querySelectorAll('.btn-filtro');
    
    botonesFiltro.forEach(boton => {
        boton.addEventListener('click', function() {
            const nuevoRango = this.dataset.rango;
            
            // Actualizar botones activos
            botonesFiltro.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Cargar nuevos datos
            rangoActual = nuevoRango;
            cargarDatos(nuevoRango, monedaActual);
        });
    });
    
    // Selector de moneda
    const selectMoneda = document.getElementById('select-moneda');
    selectMoneda.addEventListener('change', function() {
        monedaActual = this.value || null;
        cargarDatos(rangoActual, monedaActual);
    });
}

// Inicializar el gráfico
function inicializarGrafico() {
    const ctx = document.getElementById('graficoGanancias').getContext('2d');
    
    graficoGanancias = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Ganancias (PYG)',
                    data: [],
                    borderColor: COLORES.principal,
                    backgroundColor: COLORES.fondo,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: COLORES.principal,
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
                    borderColor: COLORES.principal,
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
                            return 'Ganancia: ' + valor;
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
                            weight: 'bold',
                            size: 13
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
                        text: 'Ganancias en Guaraníes (PYG)',
                        font: {
                            weight: 'bold',
                            size: 13
                        }
                    },
                    grid: {
                        color: COLORES.grid
                    },
                    ticks: {
                        callback: function(value) {
                            return new Intl.NumberFormat('es-PY', {
                                style: 'currency',
                                currency: 'PYG',
                                minimumFractionDigits: 0
                            }).format(value);
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
function cargarDatos(rango, monedaId) {
    mostrarLoading(true);
    
    let url = `/reportes/api/ganancias/?rango=${rango}`;
    if (monedaId) {
        url += `&moneda_id=${monedaId}`;
    }
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Error al cargar los datos');
            }
            return response.json();
        })
        .then(data => {
            datosActuales = data;
            actualizarGrafico(data);
            actualizarEstadisticas(data);
            mostrarLoading(false);
        })
        .catch(error => {
            console.error('Error al cargar datos:', error);
            mostrarLoading(false);
            mostrarError('Error al cargar los datos de ganancias');
        });
}

// Actualizar el gráfico con nuevos datos
function actualizarGrafico(data) {
    const fechas = data.fechas || [];
    const ganancias = data.ganancias || [];
    
    graficoGanancias.data.labels = fechas;
    graficoGanancias.data.datasets[0].data = ganancias;
    
    graficoGanancias.update('smooth');
}

// Actualizar estadísticas
function actualizarEstadisticas(data) {
    // Ganancia total
    const gananciaTotal = data.ganancia_total || 0;
    document.getElementById('ganancia-total').textContent = formatearPrecio(gananciaTotal);
    
    // Período
    const periodoTexto = {
        'semana': 'Última semana',
        'mes': 'Último mes',
        '6meses': 'Últimos 6 meses',
        'año': 'Último año'
    };
    document.getElementById('periodo-actual').textContent = periodoTexto[rangoActual] || 'Último mes';
    
    // Moneda
    const monedaTexto = data.moneda || 'Todas';
    document.getElementById('moneda-actual').textContent = monedaTexto;
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
    alert(mensaje);
}
