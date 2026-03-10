// script.js - Lógica para Inventario ROLIK con Integración de Proveedores

let allInventory = [];

document.addEventListener('DOMContentLoaded', () => {
    fetchProducts();
    fetchSuppliersForSelect(); // Cargar proveedores para el modal
});

async function fetchProducts() {
    const tbody = document.getElementById('inventory_body');
    if (!tbody) return;
    
    try {
        const response = await fetch(`${API_URL}/productos`);
        allInventory = await response.json();
        renderInventory(allInventory);
    } catch (error) {
        console.error("Error cargando productos:", error);
        tbody.innerHTML = `<tr><td colspan="10" style="color:red">Error de conexión con la API.</td></tr>`;
    }
}

function renderInventory(products) {
    const tbody = document.getElementById('inventory_body');
    if (!tbody) return;
    tbody.innerHTML = "";

    products.forEach(p => {
        const tr = document.createElement('tr');

        // Lógica de conversión para visualización
        const unidadLabel = (p.unidad || 'unidad').toLowerCase();
        let factor = 1.0;
        if (unidadLabel.includes('millar')) factor = 1000.0;
        else if (unidadLabel.includes('ciento')) factor = 100.0;
        else if (unidadLabel.includes('docena')) factor = 12.0;

        const stockReal = parseFloat(p.stock_actual || 0);
        // Mostramos el stock en términos de la unidad mayor (ej: 0.999 millares)
        const stockVisual = (stockReal / factor).toFixed(3);
        
        const stockMinimo = parseFloat(p.stock_minimo || 5);
        const stockColor = stockReal <= (stockMinimo * factor) ? 'var(--danger)' : 'var(--success)';

        // El precio ya viene por la unidad mayor desde la DB
        const precioVal = parseFloat(p.precio_venta || 0);
        const precio = precioVal.toFixed(2);
        
        // Valor total del inventario basado en el precio de venta y stock real
        // Evitamos división por cero y manejamos valores nulos
        const valorTotal = factor > 0 ? (stockReal * (precioVal / factor)).toFixed(2) : "0.00";

        tr.innerHTML = `
            <td><code>${p.codigo}</code></td>
            <td><strong>${p.nombre}</strong><br><small style="color:var(--text-muted)">${p.fabricante || ''}</small></td>
            <td><span class="badge badge-blue">${p.categoria || 'Sin Cat.'}</span></td>
            <td>${p.unidad || 'unidad'}</td>
            <td>${p.proveedor_nombre || '-'}</td>
            <td style="text-align:center; font-weight:bold; color:${stockColor}">${parseFloat(stockVisual)}</td>
            <td style="text-align:center; color:var(--text-muted)">${stockMinimo}</td>
            <td>S/ ${precio}</td>
            <td><strong>S/ ${valorTotal}</strong></td>
            <td>
                <div style="display:flex; gap:5px;">
                    <button class="btn btn-secondary btn-units" title="Presentaciones y Precios" style="padding:5px 10px; background:#3b82f6;"><i class="fas fa-layer-group"></i></button>
                    <button class="btn btn-secondary" style="padding:5px 10px;" onclick="openProductModal('${p.codigo}')" title="Editar"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-secondary text-danger" style="padding:5px 10px;" onclick="deleteProduct('${p.codigo}')" title="Eliminar"><i class="fas fa-trash-alt"></i></button>
                </div>
            </td>
        `;
        
        const btnUnits = tr.querySelector('.btn-units');
        if (btnUnits) btnUnits.onclick = () => openUnitsModal(p.codigo, p.nombre);
        
        tbody.appendChild(tr);
    });
}

let currentProductUnitsCode = null;

async function openUnitsModal(codigo, nombre) {
    currentProductUnitsCode = codigo;
    document.getElementById('units_modal_title').innerText = `Presentaciones: ${nombre}`;
    document.getElementById('unit_form').reset();
    
    // Escuchador para autocompletar factor según nombre
    const nameInput = document.getElementById('u_nombre');
    const factorInput = document.getElementById('u_factor');
    nameInput.oninput = () => {
        const val = nameInput.value.toLowerCase().trim();
        if (val === 'millar') factorInput.value = 1000;
        else if (val === 'medio millar') factorInput.value = 500;
        else if (val === 'ciento') factorInput.value = 100;
        else if (val === 'medio ciento') factorInput.value = 50;
        else if (val === 'docena') factorInput.value = 12;
    };

    loadProductUnits();
    document.getElementById('units_modal').style.display = 'block';
}

async function loadProductUnits() {
    try {
        const res = await fetch(`${API_URL}/productos/${currentProductUnitsCode}/unidades`);
        const units = await res.json();
        const tbody = document.getElementById('units_tbody');
        tbody.innerHTML = units.map(u => `
            <tr>
                <td><strong>${u.nombre_unidad}</strong></td>
                <td>${u.factor_conversion} unidades</td>
                <td><strong>S/ ${u.precio_venta.toFixed(2)}</strong></td>
                <td>
                    <button onclick="deleteUnit(${u.id})" class="btn btn-secondary" style="padding:2px 8px; color:#ef4444;"><i class="fas fa-times"></i></button>
                </td>
            </tr>
        `).join('') || '<tr><td colspan="4" style="text-align:center">No hay presentaciones adicionales.</td></tr>';
    } catch (e) { console.error(e); }
}

async function saveNewUnit() {
    const data = {
        nombre_unidad: document.getElementById('u_nombre').value,
        factor_conversion: parseFloat(document.getElementById('u_factor').value),
        precio_venta: parseFloat(document.getElementById('u_precio').value)
    };

    try {
        const res = await fetch(`${API_URL}/productos/${currentProductUnitsCode}/unidades`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            document.getElementById('unit_form').reset();
            loadProductUnits();
        } else {
            const err = await res.json();
            alert("Error: " + (err.detail || "No se pudo guardar"));
        }
    } catch (e) { alert("Error de conexión"); }
}

async function deleteUnit(id) {
    if (!confirm("¿Eliminar esta presentación?")) return;
    try {
        await fetch(`${API_URL}/productos/unidades/${id}`, { method: 'DELETE' });
        loadProductUnits();
    } catch (e) { alert("Error al eliminar"); }
}
function filterInventory() {
    const query = document.getElementById('inventory_search').value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    const words = query.split(/\s+/).filter(w => w.length > 0);
    
    const tbody = document.getElementById('inventory_body');
    if (words.length === 0) {
        renderInventory(allInventory);
        return;
    }

    const scored = allInventory.map(p => {
        const sku = (p.codigo || "").toLowerCase();
        const nombre = (p.nombre || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        const categoria = (p.categoria || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        const searchPool = sku + " " + nombre + " " + categoria;
        
        let score = 0;
        let matchesAll = true;

        words.forEach(word => {
            if (searchPool.includes(word)) {
                if (nombre === word) score += 5000;
                if (nombre.startsWith(word)) score += 2000;
                if (categoria.includes(word)) score += 500;
                const pos = nombre.indexOf(word);
                if (pos !== -1) score += (500 - pos);
            } else {
                matchesAll = false;
            }
        });
        return { p, score, matchesAll };
    });

    const visible = scored.filter(s => s.matchesAll).sort((a, b) => b.score - a.score);
    renderInventory(visible.map(v => v.p));
}

async function fetchSuppliersForSelect() {
    try {
        const response = await fetch(`${API_URL}/proveedores-lista-completa`);
        const suppliers = await response.json();
        const select = document.getElementById('p_proveedor_id');
        if (!select) return;

        select.innerHTML = '<option value="">-- Sin Proveedor --</option>';
        suppliers.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.id;
            opt.textContent = s.nombre;
            select.appendChild(opt);
        });
    } catch (error) {
        console.error("Error cargando select proveedores:", error);
    }
}

function openProductModal(codigo = null) {
    const modal = document.getElementById('product_modal');
    const form = document.getElementById('product_form');
    const title = document.getElementById('modal_title');
    
    if (form) form.reset();
    
    if (codigo) {
        title.innerText = "Editar Producto";
        loadProductToForm(codigo);
    } else {
        title.innerText = "Añadir Nuevo Producto";
        document.getElementById('p_codigo').readOnly = false;
        // Obtenemos el próximo código automáticamente del servidor
        fetch(`${API_URL}/productos/proximo-codigo`)
            .then(res => res.json())
            .then(data => {
                if (data.codigo) {
                    document.getElementById('p_codigo').value = data.codigo;
                }
            })
            .catch(err => console.error("Error al obtener próximo código:", err));
    }
    
    modal.style.display = "block";
}

function closeProductModal() {
    document.getElementById('product_modal').style.display = "none";
}

async function loadProductToForm(codigo) {
    try {
        // Corregimos la ruta: antes decía /productos/${codigo}, ahora /producto/${codigo} 
        // según lo definido en el servidor.
        const response = await fetch(`${API_URL}/producto/${codigo}`);
        if (!response.ok) throw new Error("Producto no encontrado");
        
        const p = await response.json();
        
        document.getElementById('p_codigo').value = p.codigo || "";
        document.getElementById('p_nombre').value = p.nombre || "";
        document.getElementById('p_categoria').value = p.categoria || "";
        document.getElementById('p_proveedor_id').value = p.proveedor_id || "";
        document.getElementById('p_unidad').value = p.unidad || "unidad";
        document.getElementById('p_stock').value = p.stock_actual || 0;
        document.getElementById('p_stock_min').value = p.stock_minimo || 5;
        document.getElementById('p_precio').value = p.precio_venta || 0;
        document.getElementById('p_descripcion').value = p.descripcion || "";
        
        // Bloqueamos el código para edición
        document.getElementById('p_codigo').readOnly = true;
    } catch (error) {
        console.error("Error al cargar producto:", error);
        alert("Error al cargar datos del producto: " + error.message);
    }
}

document.getElementById('product_form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const isEdit = document.getElementById('p_codigo').readOnly;
    const productData = {
        codigo: document.getElementById('p_codigo').value,
        nombre: document.getElementById('p_nombre').value,
        categoria: document.getElementById('p_categoria').value,
        proveedor_id: document.getElementById('p_proveedor_id').value ? parseInt(document.getElementById('p_proveedor_id').value) : null,
        unidad: document.getElementById('p_unidad').value,
        stock_actual: parseFloat(document.getElementById('p_stock').value),
        stock_minimo: parseFloat(document.getElementById('p_stock_min').value),
        precio_venta: parseFloat(document.getElementById('p_precio').value),
        descripcion: document.getElementById('p_descripcion').value
    };

    try {
        const url = `${API_URL}/productos` + (isEdit ? `/${productData.codigo}` : '');
        const method = isEdit ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(productData)
        });

        if (response.ok) {
            closeProductModal();
            fetchProducts();
            alert("Producto guardado con éxito.");
        } else {
            const err = await response.json();
            let msg = "No se pudo guardar.";
            if (err.detail) {
                if (Array.isArray(err.detail)) {
                    msg = err.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join('\n');
                } else {
                    msg = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail);
                }
            }
            alert("Error: " + msg);
        }
    } catch (error) {
        alert("Error de conexión con el servidor.");
    }
});
async function deleteProduct(codigo) {
    if (!confirm(`¿Estás seguro de enviar el producto ${codigo} a la papelera? Podrás restaurarlo durante los próximos 3 días.`)) return;

    try {
        const response = await fetch(`${API_URL}/productos/${codigo}`, { method: 'DELETE' });
        if (response.ok) { fetchProducts(); }
        else { 
            const err = await response.json();
            alert("Error: " + (err.detail || "No se pudo eliminar.")); 
        }
    } catch (error) { alert("Error de conexión."); }
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
                    <h2>Papelera de Productos</h2>
                    <button onclick="document.getElementById('trash_modal').style.display='none'" class="btn-secondary" style="padding:5px 10px;">&times;</button>
                </div>
                
                <div style="background: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 8px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between;">
                    <span><i class="fas fa-clock"></i> Los productos se eliminan permanentemente después de:</span>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <input type="number" id="trash_days_input" style="width: 60px; padding: 5px; border-radius: 4px; border: 1px solid var(--accent-color); background: var(--bg-dark); color: white; text-align: center;">
                        <span>días</span>
                        <button onclick="saveTrashSettings()" class="btn btn-primary" style="padding: 5px 10px; font-size: 12px;">GUARDAR</button>
                    </div>
                </div>

                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr><th>Código</th><th>Producto</th><th>Eliminado el</th><th>Acción</th></tr>
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

        // Cargar productos eliminados
        const res = await fetch(`${API_URL}/productos-eliminados`);
        const products = await res.json();
        const tbody = document.getElementById('trash_tbody');
        tbody.innerHTML = products.map(p => `
            <tr>
                <td><code>${p.codigo}</code></td>
                <td>${p.nombre}</td>
                <td><small>${p.deleted_at}</small></td>
                <td>
                    <button onclick="restoreProduct('${p.codigo}')" class="btn btn-primary" style="padding: 5px 10px; font-size: 12px;">
                        <i class="fas fa-undo"></i> RESTAURAR
                    </button>
                </td>
            </tr>
        `).join('') || '<tr><td colspan="4" style="text-align:center">La papelera está vacía</td></tr>';
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

async function restoreProduct(codigo) {
    try {
        const res = await fetch(`${API_URL}/productos/restaurar/${codigo}`, { method: 'POST' });
        if (res.ok) {
            alert("Producto restaurado");
            document.getElementById('trash_modal').style.display = 'none';
            fetchProducts();
        } else { alert("No se pudo restaurar"); }
    } catch (e) { alert("Error de conexión"); }
}


async function exportToExcel() {
    window.open(`${API_URL}/inventario/excel`, '_blank');
}
