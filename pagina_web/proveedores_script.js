// proveedores_script.js - Lógica para Gestión de Proveedores en ROLIK ERP

let allSuppliers = [];

document.addEventListener('DOMContentLoaded', () => {
    fetchSuppliers();
    setupFormListener();
});

async function fetchSuppliers() {
    const tbody = document.getElementById('suppliers_body');
    if (!tbody) return;
    
    try {
        const response = await fetch(`${API_URL}/proveedores-lista-completa`);
        allSuppliers = await response.json();
        renderSuppliers(allSuppliers);
    } catch (error) {
        console.error(error);
        tbody.innerHTML = `<tr><td colspan="6" class="loading" style="color: red;">Error de conexión con la API.</td></tr>`;
    }
}

function renderSuppliers(suppliers) {
    const tbody = document.getElementById('suppliers_body');
    if (!tbody) return;
    tbody.innerHTML = "";
    
    if (suppliers.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="loading">No se encontraron proveedores registrados.</td></tr>`;
        return;
    }

    suppliers.forEach(s => {
        const tr = document.createElement('tr');
        
        let actionsHtml = `<div style="display: flex; gap: 5px;">`;
        if (hasPermission('product.edit')) { 
            actionsHtml += `<button class="action-btn edit-btn" onclick="openSupplierModal(${s.id})" title="Editar"><i class="fas fa-edit"></i></button>`;
        }
        if (hasPermission('product.delete')) {
            actionsHtml += `<button class="action-btn delete-btn" onclick="deleteSupplier(${s.id}, '${s.nombre}')" title="Eliminar"><i class="fas fa-trash-alt"></i></button>`;
        }
        actionsHtml += `</div>`;

        tr.innerHTML = `
            <td><strong>${s.nombre}</strong></td>
            <td><code>${s.ruc_dni || '-'}</code></td>
            <td>${s.telefono || '-'}</td>
            <td>${s.email || '-'}</td>
            <td><small style="color: var(--text-muted);">${s.direccion || '-'}</small></td>
            <td>${actionsHtml}</td>
        `;
        tbody.appendChild(tr);
    });
}

function filterSuppliers() {
    const query = document.getElementById('supplier_search').value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    const filtered = allSuppliers.filter(s => {
        const nombre = s.nombre.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        const ruc = (s.ruc_dni || "").toLowerCase();
        const email = (s.email || "").toLowerCase();
        return nombre.includes(query) || ruc.includes(query) || email.includes(query);
    });
    renderSuppliers(filtered);
}

function openSupplierModal(id = null) {
    const modal = document.getElementById('supplier_modal');
    const form = document.getElementById('supplier_form');
    const title = document.getElementById('modal_title');
    
    if (form) form.reset();
    document.getElementById('s_id').value = "";
    
    if (id) {
        if (title) title.innerText = "Editar Proveedor";
        loadSupplierData(id);
    } else {
        if (title) title.innerText = "Nuevo Proveedor";
    }
    
    if (modal) modal.style.display = "block";
}

function closeSupplierModal() {
    const modal = document.getElementById('supplier_modal');
    if (modal) modal.style.display = "none";
}

async function loadSupplierData(id) {
    try {
        const response = await fetch(`${API_URL}/proveedores/${id}`);
        const s = await response.json();
        
        document.getElementById('s_id').value = s.id;
        document.getElementById('s_nombre').value = s.nombre;
        document.getElementById('s_ruc_dni').value = s.ruc_dni || "";
        document.getElementById('s_telefono').value = s.telefono || "";
        document.getElementById('s_email').value = s.email || "";
        document.getElementById('s_direccion').value = s.direccion || "";
    } catch (error) {
        alert("Error al cargar datos del proveedor");
    }
}

function setupFormListener() {
    const form = document.getElementById('supplier_form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const id = document.getElementById('s_id').value;
            const supplierData = {
                nombre: document.getElementById('s_nombre').value,
                ruc_dni: document.getElementById('s_ruc_dni').value,
                telefono: document.getElementById('s_telefono').value,
                email: document.getElementById('s_email').value,
                direccion: document.getElementById('s_direccion').value
            };

            try {
                let url = `${API_URL}/proveedores-full`;
                let method = 'POST';

                if (id) {
                    url = `${API_URL}/proveedores/${id}`;
                    method = 'PUT';
                }

                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(supplierData)
                });

                if (response.ok) {
                    closeSupplierModal();
                    fetchSuppliers();
                    alert("Proveedor guardado correctamente");
                } else {
                    const err = await response.json();
                    alert("Error: " + (err.detail || "No se pudo guardar"));
                }
            } catch (error) {
                alert("Error de conexión con el servidor");
            }
        });
    }
}

async function deleteSupplier(id, nombre) {
    if (!confirm(`¿Estás seguro de enviar al proveedor "${nombre}" a la papelera? Podrás restaurarlo durante los próximos días configurados.`)) return;

    try {
        const response = await fetch(`${API_URL}/proveedores/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            fetchSuppliers();
        } else {
            const err = await response.json();
            alert("Error: " + (err.detail || "No se pudo eliminar."));
        }
    } catch (error) {
        alert("Error de conexión con el servidor.");
    }
}

async function openTrashModal() {
    let modal = document.getElementById('trash_modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'trash_modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 800px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <h2>Papelera de Proveedores</h2>
                    <button onclick="document.getElementById('trash_modal').style.display='none'" class="btn-secondary" style="padding:5px 10px;">&times;</button>
                </div>

                <div style="background: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 8px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between;">
                    <span><i class="fas fa-clock"></i> Los proveedores se eliminan permanentemente después de:</span>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <input type="number" id="trash_days_input" style="width: 60px; padding: 5px; border-radius: 4px; border: 1px solid var(--accent-color); background: var(--bg-dark); color: white; text-align: center;">
                        <span>días</span>
                        <button onclick="saveTrashSettings()" class="btn btn-primary" style="padding: 5px 10px; font-size: 12px;">GUARDAR</button>
                    </div>
                </div>

                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr><th>Nombre</th><th>RUC</th><th>Eliminado el</th><th>Acción</th></tr>
                        </thead>
                        <tbody id="trash_tbody"></tbody>
                    </table>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    try {
        // Cargar configuración de días
        const configRes = await fetch(`${API_URL}/configuracion/trash_retention_days`);
        const config = await configRes.json();
        document.getElementById('trash_days_input').value = config.value || 3;

        const res = await fetch(`${API_URL}/proveedores-eliminados`);
        const suppliers = await res.json();
        const tbody = document.getElementById('trash_tbody');
        tbody.innerHTML = suppliers.map(s => `
            <tr>
                <td><strong>${s.nombre}</strong></td>
                <td>${s.ruc_dni || 'N/A'}</td>
                <td><small>${s.deleted_at}</small></td>
                <td>
                    <button onclick="restoreSupplier(${s.id})" class="btn btn-primary" style="padding: 5px 10px; font-size: 12px;">
                        <i class="fas fa-undo"></i> RESTAURAR
                    </button>
                </td>
            </tr>
        `).join('') || '<tr><td colspan="4" style="text-align:center">La papelera de proveedores está vacía</td></tr>';
        modal.style.display = 'block';
    } catch (e) { alert("Error al cargar la papelera"); }
}

async function saveTrashSettings() {
    const days = document.getElementById('trash_days_input').value;
    try {
        const res = await fetch(`${API_URL}/configuracion`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: 'trash_retention_days', value: days })
        });
        if (res.ok) alert("Configuración guardada. Los cambios aplicarán en la próxima eliminación.");
    } catch (e) { alert("Error al guardar configuración"); }
}

async function restoreSupplier(id) {
    try {
        const res = await fetch(`${API_URL}/proveedores/restaurar/${id}`, { method: 'POST' });
        if (res.ok) {
            alert("Proveedor restaurado con éxito.");
            document.getElementById('trash_modal').style.display = 'none';
            fetchSuppliers();
        } else { alert("No se pudo restaurar el proveedor."); }
    } catch (e) { alert("Error de conexión"); }
}

