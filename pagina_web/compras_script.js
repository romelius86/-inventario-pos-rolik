// compras_script.js - Lógica completa para Gestión de Compras ROLIK

let poItems = [];
let suppliersData = [];
let selectedProduct = null;

document.addEventListener('DOMContentLoaded', () => {
    fetchOrders();
    fetchSuppliers();
    
    // Cerrar lista de búsqueda al hacer clic fuera
    document.addEventListener('click', (e) => {
        const results = document.getElementById('po_search_results');
        if (results && !results.contains(e.target) && e.target.id !== 'item_search') {
            results.style.display = 'none';
        }
    });

    // Manejo del envío del formulario de compra
    const form = document.getElementById('order_form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (poItems.length === 0) return alert("Añade al menos un producto");

            const orderData = {
                proveedor_nombre: document.getElementById('o_proveedor').value,
                ruc_dni: document.getElementById('o_ruc').value,
                items: poItems.map(item => ({
                    codigo: item.codigo,
                    cantidad: item.cantidad,
                    precio_compra: item.precio_compra
                })),
                fecha_compra: document.getElementById('o_fecha_compra').value
            };

            try {
                const response = await fetch(`${API_URL}/compras/ordenes`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(orderData)
                });

                if (response.ok) {
                    closeOrderModal();
                    fetchOrders();
                    alert("¡Orden de compra generada con éxito!");
                } else {
                    const err = await response.json();
                    alert("Error: " + (err.detail || "No se pudo guardar la orden"));
                }
            } catch (error) { 
                console.error(error);
                alert("Error de conexión con el servidor"); 
            }
        });
    }

    // Manejo del formulario de producto rápido
    const qpForm = document.getElementById('quick_product_form');
    if (qpForm) {
        qpForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const productData = {
                codigo: document.getElementById('qp_codigo').value,
                nombre: document.getElementById('qp_nombre').value,
                categoria: document.getElementById('qp_categoria').value,
                unidad: document.getElementById('qp_unidad').value,
                precio_venta: parseFloat(document.getElementById('qp_precio_venta').value) || 0,
                precio_compra: 0,
                fabricante: document.getElementById('qp_fabricante').value,
                descripcion: document.getElementById('qp_descripcion').value,
                stock: 0,
                stock_minimo: 5
            };

            try {
                const response = await fetch(`${API_URL}/productos`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(productData)
                });

                if (response.ok) {
                    alert("¡Producto creado!");
                    selectedProduct = {
                        codigo: productData.codigo,
                        nombre: productData.nombre,
                        precio_compra: 0,
                        descripcion: productData.descripcion
                    };
                    document.getElementById('item_search').value = productData.nombre;
                    document.getElementById('item_price').value = "0.00";
                    document.getElementById('item_qty').value = 1;
                    
                    closeQuickProductModal();
                    document.getElementById('item_price').focus();
                    document.getElementById('item_price').select();
                } else {
                    const err = await response.json();
                    alert("Error: " + (err.detail || "No se pudo crear"));
                }
            } catch (error) { alert("Error de conexión"); }
        });
    }
});

// --- Funciones de Carga ---

async function fetchOrders() {
    const tbody = document.getElementById('orders_body');
    if (!tbody) return;
    try {
        const response = await fetch(`${API_URL}/compras/ordenes`);
        const orders = await response.json();
        renderOrders(orders);
    } catch (error) { console.error(error); }
}

function renderOrders(orders) {
    const tbody = document.getElementById('orders_body');
    if (!tbody) return;
    tbody.innerHTML = "";
    orders.forEach(o => {
        const tr = document.createElement('tr');
        const statusClass = `status-${o.estado.toLowerCase()}`;
        tr.innerHTML = `
            <td><code>${o.numero_oc}</code></td>
            <td>${o.fecha_pedido ? o.fecha_pedido.split(' ')[0] : '-'}</td>
            <td style="color: white; font-weight: 500;">${o.proveedor}</td>
            <td class="price">S/ ${o.total.toFixed(2)}</td>
            <td><span class="status-badge ${statusClass}">${o.estado}</span></td>
            <td><button class="action-btn edit-btn" onclick="viewOrderDetails(${o.id})"><i class="fas fa-eye"></i></button></td>
        `;
        tbody.appendChild(tr);
    });
}

async function fetchSuppliers() {
    try {
        const response = await fetch(`${API_URL}/proveedores-detalles`);
        suppliersData = await response.json();
        const select = document.getElementById('o_proveedor');
        if (select) {
            select.innerHTML = '<option value="">Selecciona Proveedor...</option>';
            suppliersData.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s.nombre;
                opt.textContent = s.nombre;
                select.appendChild(opt);
            });
        }
    } catch (error) { console.error(error); }
}

function updateRUC() {
    const name = document.getElementById('o_proveedor').value;
    const sup = suppliersData.find(s => s.nombre === name);
    document.getElementById('o_ruc').value = sup ? sup.ruc_dni : "";
}

// --- Búsqueda de Productos ---

async function searchProductsForPO(query) {
    const resultsDiv = document.getElementById('po_search_results');
    if (query.length < 2) {
        resultsDiv.style.display = 'none';
        return;
    }

    try {
        const response = await fetch(`${API_URL}/productos?search=${encodeURIComponent(query)}`);
        const products = await response.json();

        if (products.length > 0) {
            resultsDiv.innerHTML = '';
            products.forEach(p => {
                const div = document.createElement('div');
                div.style.padding = '10px 15px';
                div.style.cursor = 'pointer';
                div.style.borderBottom = '1px solid #334155';
                
                // Añadimos la descripción aquí para referencia
                const desc = p.descripcion ? `<div style="font-size:0.8em; color:#64748b; font-style:italic;">${p.descripcion}</div>` : '';
                
                div.innerHTML = `
                    <div style="font-weight:bold; color:white;">${p.nombre}</div>
                    ${desc}
                    <div style="font-size:0.85em; color:#94a3b8;">SKU: ${p.codigo} | Costo: S/ ${p.precio_compra.toFixed(2)}</div>
                `;
                div.onmouseover = () => div.style.background = '#334155';
                div.onmouseout = () => div.style.background = 'transparent';
                div.onclick = () => selectProductForPO(p);
                resultsDiv.appendChild(div);
            });
            resultsDiv.style.display = 'block';
        } else {
            resultsDiv.style.display = 'none';
        }
    } catch (error) { console.error(error); }
}

function selectProductForPO(p) {
    selectedProduct = p;
    document.getElementById('item_search').value = p.nombre;
    document.getElementById('item_price').value = p.precio_compra.toFixed(2);
    document.getElementById('item_qty').value = 1;
    document.getElementById('po_search_results').style.display = 'none';
    document.getElementById('item_qty').focus();
    document.getElementById('item_qty').select();
}

// --- Modales ---

function openOrderModal() {
    poItems = [];
    renderPOItems();
    selectedProduct = null;
    document.getElementById('order_form').reset();
    document.getElementById('o_fecha_compra').value = new Date().toISOString().split('T')[0];
    document.getElementById('order_modal').style.display = "block";
}

function closeOrderModal() {
    document.getElementById('order_modal').style.display = "none";
}

function openQuickProductModal() {
    document.getElementById('quick_product_form').reset();
    const current = document.getElementById('item_search').value;
    if (current) document.getElementById('qp_nombre').value = current;
    document.getElementById('quick_product_modal').style.display = "block";
}

function closeQuickProductModal() {
    document.getElementById('quick_product_modal').style.display = "none";
}

// --- Gestión de Items ---

async function addItemToOrder() {
    const queryInp = document.getElementById('item_search');
    const qtyInp = document.getElementById('item_qty');
    const priceInp = document.getElementById('item_price');

    const qty = parseInt(qtyInp.value);
    const price = parseFloat(priceInp.value);

    if (!selectedProduct && !queryInp.value) return alert("Selecciona un producto");
    if (!qty || qty <= 0) return alert("Cantidad inválida");

    let prod = selectedProduct;
    if (!prod) {
        const res = await fetch(`${API_URL}/productos?search=${encodeURIComponent(queryInp.value)}`);
        const results = await res.json();
        if (results.length > 0) prod = results[0];
        else return alert("Producto no encontrado. Use el botón 'NUEVO'.");
    }

    poItems.push({
        codigo: prod.codigo,
        nombre: prod.nombre,
        descripcion: prod.descripcion || '-',
        cantidad: qty,
        precio_compra: price
    });
    
    queryInp.value = "";
    qtyInp.value = "";
    priceInp.value = "";
    selectedProduct = null;
    renderPOItems();
    queryInp.focus();
}

function renderPOItems() {
    const tbody = document.getElementById('po_items_body');
    const totalSpan = document.getElementById('po_total');
    tbody.innerHTML = "";
    let total = 0;
    poItems.forEach((item, index) => {
        const sub = item.cantidad * item.precio_compra;
        total += sub;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${item.nombre}</strong><br><small>${item.codigo}</small></td>
            <td><small>${item.descripcion}</small></td>
            <td>${item.cantidad}</td>
            <td>S/ ${item.precio_compra.toFixed(2)}</td>
            <td>S/ ${sub.toFixed(2)}</td>
            <td><button type="button" onclick="removeItem(${index})" style="color:#ef4444; border:none; background:none; cursor:pointer;">&times;</button></td>
        `;
        tbody.appendChild(tr);
    });
    totalSpan.textContent = total.toFixed(2);
}

function removeItem(index) {
    poItems.splice(index, 1);
    renderPOItems();
}

// --- Detalles ---

async function viewOrderDetails(id) {
    try {
        const response = await fetch(`${API_URL}/compras/ordenes/${id}`);
        const data = await response.json();
        const o = data.orden;
        
        document.getElementById('det_info').innerHTML = `
            <p><strong>Número:</strong> ${o.numero_oc}</p>
            <p><strong>Proveedor:</strong> ${o.proveedor_nombre}</p>
            <p><strong>Total:</strong> S/ ${o.total.toFixed(2)}</p>
        `;
        
        const tbody = document.getElementById('det_items_body');
        tbody.innerHTML = "";
        data.items.forEach(i => {
            const tr = document.createElement('tr');
            const subtotal = i.cantidad * i.precio_compra_unitario;
            tr.innerHTML = `
                <td><strong>${i.nombre}</strong><br><small>${i.producto_codigo}</small></td>
                <td><small>${i.descripcion || '-'}</small></td>
                <td>${i.cantidad}</td>
                <td>S/ ${i.precio_compra_unitario.toFixed(2)}</td>
                <td>S/ ${subtotal.toFixed(2)}</td>
            `;
            tbody.appendChild(tr);
        });

        const actions = document.getElementById('det_actions');
        actions.innerHTML = '<button class="btn btn-secondary" onclick="closeDetailModal()">Cerrar</button>';
        if (o.estado === 'PENDIENTE') {
            actions.innerHTML += `<button class="btn btn-primary" onclick="changeStatus(${o.id}, 'RECIBIDA')" style="margin-left:10px;">RECIBIR</button>`;
        }

        document.getElementById('detail_modal').style.display = "block";
    } catch (e) { console.error(e); }
}

function closeDetailModal() {
    document.getElementById('detail_modal').style.display = "none";
}

async function changeStatus(id, estado) {
    if (!confirm(`¿Cambiar a ${estado}?`)) return;
    const res = await fetch(`${API_URL}/compras/ordenes/${id}/estado?estado=${estado}`, { method: 'PATCH' });
    if (res.ok) { closeDetailModal(); fetchOrders(); }
}
