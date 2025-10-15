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

// Configuración de cuentas de Global Exchange
const CUENTAS_GLOBAL_EXCHANGE = {
    'Transferencia Bancaria': {
        banco: 'SUDAMERIS',
        cuenta: '12345',
        ruc: '1234567',
        titular: 'Global Exchange'
    },
    'Billetera Electrónica': {
        tigo: '*724#12345',
        personal: 'personal@globalexchange.com',
        zimple: 'zimple@globalexchange.com'
    }
};

// Función para procesar el pago e iniciar redirección
function procesarPago(datosTransaccion) {
    console.log('Procesando pago...', datosTransaccion);
    
    // Determinar tipo de pago y billetera si aplica
    let metodoPago;
    let billetera = '';
    
    if (datosTransaccion.medio_pago.includes('Tigo')) {
        metodoPago = 'Billetera Electrónica';
        billetera = 'tigo';
    } else if (datosTransaccion.medio_pago.includes('Personal')) {
        metodoPago = 'Billetera Electrónica';
        billetera = 'personal';
    } else if (datosTransaccion.medio_pago.includes('Zimple')) {
        metodoPago = 'Billetera Electrónica';
        billetera = 'zimple';
    } else {
        metodoPago = 'Transferencia Bancaria';
    }
    
    console.log('Redirigiendo a:', metodoPago, 'con billetera:', billetera);
    
    // Llamar a la función de redirección
    redirigirAPasarela(metodoPago, {
        ...datosTransaccion,
        billetera: billetera
    });
}

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
        cliente_id: datosTransaccion.cliente_id,
        token: datosTransaccion.token,  // Agregamos el token
        return_url: window.location.origin + '/operaciones/comprar/exito/' + datosTransaccion.token + '/'
    
    });
    
    // Redireccionar
    window.location.href = `${url}?${params.toString()}`;
}

// Función para verificar el pago
function verificarPago(datosPago, datosTransaccion) {
    // Verificar monto mínimo
    if (parseFloat(datosPago.monto) < parseFloat(datosTransaccion.monto_minimo)) {
        return {
            valido: false,
            mensaje: 'El monto pagado es menor al requerido'
        };
    }

    // Verificar cuenta destino según el medio de pago
    const cuentaCorrecta = datosTransaccion.medio_pago.includes('Billetera') ? 
        CUENTAS_GLOBAL_EXCHANGE['Billetera Electrónica'][datosPago.billetera] :
        CUENTAS_GLOBAL_EXCHANGE['Transferencia Bancaria'];

    if (datosPago.cuenta_destino !== cuentaCorrecta) {
        return {
            valido: false,
            mensaje: 'La cuenta de destino no coincide'
        };
    }

    return { 
        valido: true,
        mensaje: 'Pago verificado correctamente'
    };
}

// Función para procesar la respuesta de la pasarela
function procesarRespuestaPago(respuesta) {
    const datosTransaccion = JSON.parse(sessionStorage.getItem('datosTransaccion'));
    const returnUrl = sessionStorage.getItem('returnUrl');
    
    if (respuesta.estado === 'exito') {
        const verificacion = verificarPago(respuesta.datosPago, datosTransaccion);
        
        if (verificacion.valido) {
            // Actualizar estado de la transacción
            fetch('/api/transacciones/confirmar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    token: datosTransaccion.token,
                    datos_pago: respuesta.datosPago,
                    estado: 'Confirmada'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Redirigir a la página de éxito con estado confirmado
                    window.location.href = `/transacciones/exito/${datosTransaccion.token}/`;
                } else {
                    mostrarError('Error al confirmar el pago: ' + data.mensaje);
                }
            });
        } else {
            mostrarError(verificacion.mensaje);
        }
    } else {
        mostrarError('El pago no se completó correctamente');
    }
}

// Función para mostrar errores
function mostrarError(mensaje) {
    Swal.fire({
        title: 'Error en el pago',
        text: mensaje,
        icon: 'error',
        confirmButtonText: 'Intentar nuevamente'
    }).then(() => {
        window.location.href = sessionStorage.getItem('returnUrl');
    });
}

// Inicializar cuando el documento está listo
document.addEventListener('DOMContentLoaded', function() {
    // Verificar si hay una respuesta de la pasarela
    const estadoPago = sessionStorage.getItem('estadoPago');
    if (estadoPago) {
        const respuesta = JSON.parse(sessionStorage.getItem('respuestaPago') || '{}');
        procesarRespuestaPago(respuesta);
    }
});

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

// --- Escuchar retorno desde la pasarela ---
window.addEventListener('message', function(event) {
    // Verifica que venga del dominio esperado
    if (!event.origin.includes('localhost:5500')) return;

    const respuesta = event.data;
    console.log('Respuesta recibida desde pasarela:', respuesta);

    if (respuesta && respuesta.estado === 'exito') {
        sessionStorage.setItem('estadoPago', 'exito');
        sessionStorage.setItem('respuestaPago', JSON.stringify(respuesta));
        procesarRespuestaPago(respuesta);
    } else {
        mostrarError('El pago no fue completado o fue cancelado');
    }
});
