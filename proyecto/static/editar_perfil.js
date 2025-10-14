// === FUNCIONES DE EDITAR PERFIL ===

function togglePasswordChange() {
    const zonaPassword = document.getElementById('zona-cambio-password');
    const btnCambiar = document.querySelector('.btn-cambiar-password');
    
    if (zonaPassword.style.display === 'none') {
        zonaPassword.style.display = 'block';
        btnCambiar.style.display = 'none'; // Ocultar el botón cuando se despliegan los campos
    }
}

function cancelPasswordChange() {
    const zonaPassword = document.getElementById('zona-cambio-password');
    const btnCambiar = document.querySelector('.btn-cambiar-password');
    
    zonaPassword.style.display = 'none';
    btnCambiar.style.display = 'inline-block'; // Mostrar el botón de nuevo al cancelar
    
    // Limpiar campos
    const newPassword1 = document.querySelector('[name="new_password1"]');
    const newPassword2 = document.querySelector('[name="new_password2"]');
    if (newPassword1) newPassword1.value = '';
    if (newPassword2) newPassword2.value = '';
    
    // Limpiar mensajes de error
    const errorsInPasswordSection = zonaPassword.querySelectorAll('.form-errores');
    errorsInPasswordSection.forEach(errorDiv => {
        errorDiv.style.display = 'none';
    });
    
    // Restablecer visibilidad de contraseñas a oculta
    const passwordFields = zonaPassword.querySelectorAll('input[type="password"], input[type="text"]');
    passwordFields.forEach(field => {
        if (field.name && field.name.includes('new_password')) {
            const button = field.nextElementSibling;
            if (field.type === 'text') {
                field.type = 'password';
                const icon = button.querySelector('.material-icons');
                if (icon) {
                    icon.textContent = 'visibility';
                }
                button.classList.remove('active');
            }
        }
    });
}

function togglePasswordVisibility(fieldId, button) {
    const field = document.getElementById(fieldId);
    const icon = button.querySelector('.material-icons');
    
    // Determinar el nuevo estado
    const showPassword = field.type === 'password';
    
    // Aplicar el mismo estado a ambos campos de contraseña
    const passwordFields = document.querySelectorAll('[name="new_password1"], [name="new_password2"]');
    
    passwordFields.forEach(currentField => {
        const currentButton = currentField.nextElementSibling;
        const currentIcon = currentButton.querySelector('.material-icons');
        
        if (showPassword) {
            currentField.type = 'text';
            currentIcon.textContent = 'visibility_off';
            currentButton.classList.add('active');
        } else {
            currentField.type = 'password';
            currentIcon.textContent = 'visibility';
            currentButton.classList.remove('active');
        }
    });
}

function toggleRolesDropdown() {
    const dropdown = document.getElementById('roles-dropdown');
    const button = document.querySelector('.btn-roles');
    const icon = button.querySelector('.material-icons');
    
    if (dropdown.style.display === 'none' || dropdown.style.display === '') {
        dropdown.style.display = 'block';
        button.classList.add('expanded');
        icon.style.transform = 'rotate(180deg)';
    } else {
        dropdown.style.display = 'none';
        button.classList.remove('expanded');
        icon.style.transform = 'rotate(0deg)';
    }
}

// === INICIALIZACIÓN ===
document.addEventListener('DOMContentLoaded', function() {
    // Si hay errores en los campos de contraseña, mostrar la sección automáticamente
    const passwordErrors = document.querySelectorAll('#zona-cambio-password .form-errores');
    if (passwordErrors.length > 0) {
        togglePasswordChange();
    }
    
    // Cerrar dropdown de roles al hacer clic fuera
    document.addEventListener('click', function(event) {
        const rolesSection = document.querySelector('.roles-section');
        const dropdown = document.getElementById('roles-dropdown');
        const button = document.querySelector('.btn-roles');
        
        if (rolesSection && !rolesSection.contains(event.target)) {
            if (dropdown && dropdown.style.display === 'block') {
                dropdown.style.display = 'none';
                button.classList.remove('expanded');
                const icon = button.querySelector('.material-icons');
                if (icon) {
                    icon.style.transform = 'rotate(0deg)';
                }
            }
        }
    });
});