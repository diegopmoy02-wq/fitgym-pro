// Sistema de Gimnasio - JavaScript Principal

// Auto-cerrar alertas después de 5 segundos
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Validación de formularios
(function() {
    'use strict';
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
})();

// Confirmación de eliminación
function confirmarEliminacion(mensaje) {
    return confirm(mensaje || '¿Estás seguro de que deseas eliminar este registro?');
}

// Búsqueda en tablas
function filtrarTabla(inputId, tablaId) {
    const input = document.getElementById(inputId);
    const filter = input.value.toUpperCase();
    const table = document.getElementById(tablaId);
    const tr = table.getElementsByTagName('tr');

    for (let i = 1; i < tr.length; i++) {
        let td = tr[i].getElementsByTagName('td');
        let mostrar = false;
        
        for (let j = 0; j < td.length; j++) {
            if (td[j]) {
                const txtValue = td[j].textContent || td[j].innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {
                    mostrar = true;
                    break;
                }
            }
        }
        
        tr[i].style.display = mostrar ? '' : 'none';
    }
}

// Formatear números como moneda
function formatearMoneda(numero) {
    return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN'
    }).format(numero);
}

// Formatear fechas
function formatearFecha(fecha) {
    return new Date(fecha).toLocaleDateString('es-MX', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Mostrar notificación toast
function mostrarToast(mensaje, tipo = 'info') {
    const toastContainer = document.getElementById('toastContainer') || crearToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${tipo} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${mensaje}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

function crearToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}

// Validar email
function validarEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Validar teléfono
function validarTelefono(telefono) {
    const re = /^[0-9]{10}$/;
    return re.test(telefono);
}

// Cargar datos con AJAX
function cargarDatos(url, callback) {
    fetch(url)
        .then(response => response.json())
        .then(data => callback(data))
        .catch(error => {
            console.error('Error:', error);
            mostrarToast('Error al cargar los datos', 'danger');
        });
}

// Actualizar estadísticas en tiempo real
function actualizarEstadisticas() {
    cargarDatos('/api/estadisticas', function(stats) {
        document.getElementById('miembros_activos').textContent = stats.miembros_activos;
        document.getElementById('membresias_activas').textContent = stats.membresias_activas;
        document.getElementById('asistencias_hoy').textContent = stats.asistencias_hoy;
        document.getElementById('ingresos_mes').textContent = formatearMoneda(stats.ingresos_mes);
    });
}

// Exportar tabla a CSV
function exportarTablaCSV(tablaId, nombreArchivo) {
    const tabla = document.getElementById(tablaId);
    let csv = [];
    const filas = tabla.querySelectorAll('tr');
    
    for (let i = 0; i < filas.length; i++) {
        const fila = [];
        const cols = filas[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            fila.push(cols[j].innerText);
        }
        
        csv.push(fila.join(','));
    }
    
    descargarCSV(csv.join('\n'), nombreArchivo);
}

function descargarCSV(csv, nombreArchivo) {
    const csvFile = new Blob([csv], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.download = nombreArchivo;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

// Imprimir página
function imprimirPagina() {
    window.print();
}

console.log('Sistema de Gimnasio - JavaScript cargado correctamente');