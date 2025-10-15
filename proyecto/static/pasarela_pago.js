// Configuración de la pasarela de pago
const PASARELA_CONFIG = {
    BASE_URL: 'http://localhost:5500/pagos/',   // URL completa del proyecto pasarela
    API_URL: 'http://localhost:5500/pagos/api/crear-pago/', // API de la pasarela
    METODOS_PAGO: {
        'Billetera Electrónica': {
            'tigo': 'billetera/?tipo=tigo',
            'personal': 'billetera/?tipo=personal',
            'zimple': 'billetera/?tipo=zimple'
        },
        'Transferencia Bancaria': 'transferencia/'
    }
};


// Función para redirigir a la pasarela según el método
function redirigirAPasarela(metodoPago, datosTransaccion) {
    let url;
    if (metodoPago === 'Billetera Electrónica') {
        url = PASARELA_CONFIG.BASE_URL + PASARELA_CONFIG.METODOS_PAGO[metodoPago][datosTransaccion.billetera];
    } else {
        url = PASARELA_CONFIG.BASE_URL + PASARELA_CONFIG.METODOS_PAGO[metodoPago];
    }

    // Agregar datos de la transacción como parámetros
    const params = new URLSearchParams({
        monto: datosTransaccion.monto,
        moneda: datosTransaccion.moneda,
        tipo_operacion: datosTransaccion.tipo_operacion,
        cliente_id: datosTransaccion.cliente_id
    });
    
    window.location.href = `${url}?${params.toString()}`;
    
}

// Función para probar la conexión con la pasarela
function probarConexionPasarela() {
    console.log('Probando conexión con la pasarela...');
    
    // Datos de prueba
    const datosPrueba = {
        estado: 'exito',
        monto: 1000,
        tipo_pago: 'TIGO',
        usuario: '1234567'
    };

    fetch(PASARELA_CONFIG.API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(datosPrueba)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Respuesta recibida:', data);
        alert('Conexión exitosa con la pasarela. Ver consola para detalles.');
    })
    .catch(error => {
        console.error('Error de conexión:', error);
        alert('Error al conectar con la pasarela. Ver consola para detalles.');
    });
}

// Agregar botón de prueba si estamos en modo desarrollo
if (window.location.hostname === 'localhost') {
    document.addEventListener('DOMContentLoaded', function() {
        const botonPrueba = document.createElement('button');
        botonPrueba.textContent = 'Probar Conexión Pasarela';
        botonPrueba.onclick = probarConexionPasarela;
        botonPrueba.style.position = 'fixed';
        botonPrueba.style.bottom = '20px';
        botonPrueba.style.right = '20px';
        botonPrueba.style.zIndex = '1000';
        document.body.appendChild(botonPrueba);
    });
}