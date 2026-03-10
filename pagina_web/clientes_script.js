// clientes_script.js - Lógica para Clientes con Papelera de Reciclaje

document.addEventListener('DOMContentLoaded', () => {
    fetchClientes();
    
    // Configurar el formulario
    const form = document.getElementById('cliente_form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            guardarCliente();
        });
    }

    // Cerrar modales al hacer clic fuera
    window.onclick = function(event) {
        const clienteModal = document.getElementById('cliente_modal');
        const trashModal = document.getElementById('trash_modal');
        if (event.target == clienteModal) closeClienteModal();
        if (event.target == trashModal) closeTrashModal();
    }
});

let currentClienteId = null;

async function fetchClientes() {
    const search = document.getElementById('cliente_search').value;
    const tbody = document.getElementById('clientes_body');
    
    try {
        const response = await fetch(`${API_URL}/clientes-lista?search=${encodeURIComponent(search)}`);
        const clientes = await response.json();
        renderClientes(clientes);
    } catch (error) {
        if (tbody) tbody.innerHTML = `<tr><td colspan="6" class="error">Error al conectar con el servidor</td></tr>`;
    }
}

function renderClientes(clientes) {
    const tbody = document.getElementById('clientes_body');
    if (!tbody) return;
    tbody.innerHTML = "";
    
    if (clientes.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="loading">No se encontraron clientes activos.</td></tr>`;
        return;
    }

    clientes.forEach(c => {
        const tr = document.createElement('tr');
        
        let actionsHtml = `<div style="display: flex; gap: 5px;">`;
        if (hasPermission('user.edit')) { 
            actionsHtml += `<button class="action-btn edit-btn" onclick="openClienteModal('${c.documento}')" title="Editar"><i class="fas fa-user-edit"></i></button>`;
        }
        if (hasPermission('user.delete')) {
            actionsHtml += `<button class="action-btn delete-btn" onclick="confirmarEliminar('${c.documento}', '${c.nombre}')" title="Mover a Papelera"><i class="fas fa-trash"></i></button>`;
        }
        actionsHtml += `</div>`;

        tr.innerHTML = `
            <td><code>${c.documento}</code></td>
            <td><strong>${c.nombre}</strong></td>
            <td>${c.telefono || '-'}</td>
            <td>${c.email || '-'}</td>
            <td><small style="color: var(--text-muted);">${c.direccion || '-'}</small></td>
            <td>${actionsHtml}</td>
        `;
        tbody.appendChild(tr);
    });
}

function openClienteModal(documento = null) {
    const modal = document.getElementById('cliente_modal');
    const form = document.getElementById('cliente_form');
    const title = document.getElementById('modal_title');
    
    if (form) form.reset();
    currentClienteId = null;
    document.getElementById('c_documento').disabled = false;
    
    if (documento) {
        title.innerText = "Editar Cliente";
        loadClienteData(documento);
    } else {
        title.innerText = "Nuevo Cliente";
    }
    
    modal.style.display = "block";
}

function closeClienteModal() {
    const modal = document.getElementById('cliente_modal');
    if (modal) modal.style.display = "none";
}

async function loadClienteData(documento) {
    try {
        const response = await fetch(`${API_URL}/clientes/${documento}`);
        const c = await response.json();
        
        currentClienteId = c.id;
        document.getElementById('c_documento').value = c.documento;
        document.getElementById('c_nombre').value = c.nombre;
        document.getElementById('c_direccion').value = c.direccion || "";
        document.getElementById('c_telefono').value = c.telefono || "";
        document.getElementById('c_email').value = c.email || "";
    } catch (error) {
        alert("Error al cargar datos del cliente");
    }
}

async function guardarCliente() {
    const clienteData = {
        id: currentClienteId,
        documento: document.getElementById('c_documento').value,
        nombre: document.getElementById('c_nombre').value,
        direccion: document.getElementById('c_direccion').value,
        telefono: document.getElementById('c_telefono').value,
        email: document.getElementById('c_email').value
    };

    try {
        const response = await fetch(`${API_URL}/clientes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(clienteData)
        });

        if (response.ok) {
            closeClienteModal();
            fetchClientes();
        } else {
            const err = await response.json();
            alert("Error: " + (err.detail || "No se pudo guardar"));
        }
    } catch (error) {
        alert("Error de conexión");
    }
}

function confirmarEliminar(documento, nombre) {
    if (confirm(`¿Estás seguro de mover a ${nombre} a la papelera?\nPodrás restaurarlo durante los próximos 3 días.`)) {
        eliminarCliente(documento);
    }
}

async function eliminarCliente(documento) {
    try {
        const response = await fetch(`${API_URL}/clientes/${documento}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            fetchClientes();
        } else {
            alert("Error al eliminar cliente");
        }
    } catch (error) {
        alert("Error de conexión");
    }
}

// Lógica de Papelera
function openTrashModal() {
    const modal = document.getElementById('trash_modal');
    modal.style.display = "block";
    fetchClientesEliminados();
}

function closeTrashModal() {
    const modal = document.getElementById('trash_modal');
    modal.style.display = "none";
}

async function fetchClientesEliminados() {
    const tbody = document.getElementById('trash_body');
    tbody.innerHTML = `<tr><td colspan="4" class="loading">Buscando en papelera...</td></tr>`;
    
    try {
        const response = await fetch(`${API_URL}/clientes-eliminados`);
        const clientes = await response.json();
        
        tbody.innerHTML = "";
        if (clientes.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding: 20px;">La papelera está vacía.</td></tr>`;
            return;
        }

        clientes.forEach(c => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><code>${c.documento}</code></td>
                <td>${c.nombre}</td>
                <td><small>${c.deleted_at}</small></td>
                <td>
                    <button class="btn btn-primary" style="padding: 5px 10px; font-size: 12px;" onclick="restaurarCliente('${c.documento}')">
                        <i class="fas fa-undo"></i> RESTAURAR
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="4" class="error">Error al cargar papelera</td></tr>`;
    }
}

async function restaurarCliente(documento) {
    try {
        const response = await fetch(`${API_URL}/clientes/restaurar/${documento}`, {
            method: 'POST'
        });

        if (response.ok) {
            fetchClientesEliminados(); // Actualizar papelera
            fetchClientes(); // Actualizar lista principal
            alert("Cliente restaurado correctamente");
        } else {
            alert("No se pudo restaurar el cliente");
        }
    } catch (error) {
        alert("Error de conexión");
    }
}
