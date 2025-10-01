// JavaScript para el simulador de conversiones de monedas

document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const botonesOperacion = document.querySelectorAll('[data-operacion]');
    const formulario = document.getElementById('simulador-form');
    const resultadoDiv = document.getElementById('resultado');
    const medioPagoSelect = document.getElementById('medio_pago');
    const medioCobroSelect = document.getElementById('medio_cobro');
    const monedaSelect = document.getElementById('moneda');
    const montoInput = document.getElementById('monto');
    
    // Campo oculto para almacenar la operación seleccionada
    let operacionSeleccionada = 'compra';
    
    // Configuración inicial
    inicializarSimulador();
    
    function inicializarSimulador() {
        // Configurar botones de operación
        configurarBotonesOperacion();
        
        // Configurar opciones iniciales de medios
        actualizarOpcionesMedios();
        
        // Agregar event listeners para resetear resultado
        agregarListenersReseteo();
        
        // Agregar event listener para el envío del formulario
        formulario.addEventListener('submit', manejarEnvioFormulario);
    }
    
    function configurarBotonesOperacion() {
        botonesOperacion.forEach(boton => {
            boton.addEventListener('click', function() {
                const operacion = this.getAttribute('data-operacion');
                seleccionarOperacion(operacion);
            });
        });
    }
    
    function seleccionarOperacion(operacion) {
        operacionSeleccionada = operacion;
        
        // Actualizar campo oculto
        const operacionInput = document.getElementById('operacion');
        if (operacionInput) {
            operacionInput.value = operacion;
        }
        
        // Actualizar estilos de botones
        botonesOperacion.forEach(boton => {
            const operacionBoton = boton.getAttribute('data-operacion');
            if (operacionBoton === operacion) {
                boton.classList.remove('btn-secundario');
                boton.classList.add('btn-primario');
            } else {
                boton.classList.remove('btn-primario');
                boton.classList.add('btn-secundario');
            }
        });
        
        // Actualizar opciones de medios según la operación
        actualizarOpcionesMedios();
        
        // Resetear resultado
        resetearResultado();
    }
    
    function actualizarOpcionesMedios() {
        if (operacionSeleccionada === 'compra') {
            actualizarMedioPago([
                { value: 'no_recargo', text: 'Efectivo/Cheque/Transferencia' },
                { value: '{"brand": "VISA"}', text: 'Tarjeta de Crédito Visa' },
                { value: '{"brand": "MASTERCARD"}', text: 'Tarjeta de Crédito Mastercard' },
                { value: 'Tigo Money', text: 'Tigo Money' },
                { value: 'Billetera Personal', text: 'Billetera Personal' },
                { value: 'Zimple', text: 'Zimple' }
            ]);
            
            actualizarMedioCobro([
                { value: 'no_recargo', text: 'Efectivo' }
            ]);
        } else if (operacionSeleccionada === 'venta') {
            if (monedaSelect.options[monedaSelect.selectedIndex]?.text === 'Dólar estadounidense') {
                actualizarMedioPago([
                    { value: 'no_recargo', text: 'Efectivo' },
                    { value: '{"brand": "VISA"}', text: 'Tarjeta de Crédito Visa' },
                    { value: '{"brand": "MASTERCARD"}', text: 'Tarjeta de Crédito Mastercard' },
                ]);
            } else {
                actualizarMedioPago([
                    { value: 'no_recargo', text: 'Efectivo' }
                ]);
            }
            
            actualizarMedioCobro([
                { value: 'no_recargo', text: 'Efectivo/Transferencia' },
                { value: '{"tipo_billetera": "Tigo Money"}', text: 'Tigo Money' },
                { value: '{"tipo_billetera": "Billetera Personal"}', text: 'Billetera Personal' },
                { value: '{"tipo_billetera": "Zimple"}', text: 'Zimple' }
            ]);
        }
    }
    
    function actualizarMedioPago(opciones) {
        medioPagoSelect.innerHTML = '';
        opciones.forEach(opcion => {
            const option = document.createElement('option');
            option.value = opcion.value;
            option.textContent = opcion.text;
            medioPagoSelect.appendChild(option);
        });
    }
    
    function actualizarMedioCobro(opciones) {
        medioCobroSelect.innerHTML = '';
        opciones.forEach(opcion => {
            const option = document.createElement('option');
            option.value = opcion.value;
            option.textContent = opcion.text;
            medioCobroSelect.appendChild(option);
        });
    }
    
    function agregarListenersReseteo() {
        // Resetear resultado cuando cambien los valores del formulario
        const campos = [monedaSelect, montoInput, medioPagoSelect, medioCobroSelect];
        
        campos.forEach(campo => {
            if (campo) {
                campo.addEventListener('change', resetearResultado);
                campo.addEventListener('input', resetearResultado);
            }
            if (monedaSelect) {
                monedaSelect.addEventListener('change', actualizarOpcionesMedios);
                monedaSelect.addEventListener('input', actualizarOpcionesMedios);
            }
        });
    }
    
    function resetearResultado() {
        if (resultadoDiv) {
            resultadoDiv.innerHTML = '&nbsp;';
        }
        
        // Limpiar errores de validación previos
        limpiarErroresValidacion();
    }
    
    function limpiarErroresValidacion() {
        const errores = formulario.querySelectorAll('.form-errores');
        errores.forEach(error => {
            error.style.display = 'none';
        });
        
        const campos = formulario.querySelectorAll('.form-control');
    }
    
    function manejarEnvioFormulario(event) {
        event.preventDefault();
        
        // Mostrar indicador de carga solo si pasa la validación
        mostrarCargando();
        
        // Preparar datos del formulario
        const formData = new FormData(formulario);
        
        // Enviar petición AJAX
        fetch(formulario.action || window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                mostrarResultado(data);
            } else {
                mostrarErrores(data.errors || { __all__: [data.error || 'Error desconocido'] });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarErrorGeneral('Error de conexión. Inténtelo nuevamente.');
        });
    }
    
    function mostrarErrorCampo(campo, mensaje) {
        
        // Buscar contenedor de errores existente o crear uno nuevo
        const contenedorCampo = campo.closest('.form-campo');
        let contenedorErrores = contenedorCampo.querySelector('.form-errores');
        
        if (!contenedorErrores) {
            contenedorErrores = document.createElement('div');
            contenedorErrores.className = 'form-errores';
            contenedorCampo.appendChild(contenedorErrores);
        }
        
        contenedorErrores.innerHTML = `<div class="mensaje-error">${mensaje}</div>`;
        contenedorErrores.style.display = 'block';
    }
    
    function mostrarCargando() {
        if (resultadoDiv) {
            resultadoDiv.innerHTML = 'Calculando...';
        }
    }
    
    function ocultarCargando() {
        // El resultado se mostrará en mostrarResultado o mostrarErrorGeneral
    }

    function formatNumber(num) {
        return String(num).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }
    
    function mostrarResultado(data) {
        if (!resultadoDiv) return;
        
        let resultadoHTML = `
            <div style="text-align: left;">
                <small>Precio base: ${formatNumber(data.cotizacion_base)} Gs.</small><br>
        `;
        
        if (data.beneficio_segmento > 0) {
            resultadoHTML += `<small>Beneficio por segmento: ${formatNumber(data.beneficio_segmento)}</small><br>`;
        }
        
        if (data.monto_recargo_pago > 0) {
            resultadoHTML += `<small>Recargo por medio de pago: ${formatNumber(data.monto_recargo_pago)} Gs.</small><br>`;
        }
        
        if (data.monto_recargo_cobro > 0) {
            resultadoHTML += `<small>Recargo por medio de cobro: ${formatNumber(data.monto_recargo_cobro)} Gs.</small><br>`;
        }
        
        if (operacionSeleccionada === 'compra') {
            resultadoHTML += `
                    <br>
                    <span style="font-size: 1.1em; font-weight: bold; color: #2c5530;">
                        Costo: ${formatNumber(data.monto_final)} Gs.
                    </span>
                </div>
            `;
        }
        else {
            resultadoHTML += `
                    <br>
                    <span style="font-size: 1.1em; font-weight: bold; color: #2c5530;">
                        Cobro: ${formatNumber(data.monto_final)} Gs.
                    </span>
                </div>
            `;
        }
        
        resultadoDiv.innerHTML = resultadoHTML;
    }
    
    function mostrarErrores(errores) {
        // Limpiar errores previos y resetear resultado
        limpiarErroresValidacion();
        resetearResultado();
        
        // Mostrar errores específicos de campos
        Object.keys(errores).forEach(campo => {
            const mensajes = errores[campo];
            if (Array.isArray(mensajes) && mensajes.length > 0) {
                if (campo === '__all__' || campo === 'non_field_errors') {
                    mostrarErrorGeneral(mensajes[0]);
                } else {
                    const campoElement = document.getElementById(campo) || document.querySelector(`[name="${campo}"]`);
                    if (campoElement) {
                        mostrarErrorCampo(campoElement, mensajes[0]);
                    } else {
                        mostrarErrorGeneral(mensajes[0]);
                    }
                }
            }
        });
    }
    
    function mostrarErrorGeneral(mensaje) {
        if (resultadoDiv) {
            resultadoDiv.innerHTML = `<span style="color: #d32f2f;">Error: ${mensaje}</span>`;
        }
    }
});