// reportes_script.js - Lógica para reportes avanzados en ROLIK ERP con búsqueda estricta

let currentReportType = '';
let selectedReceiptId = null;

document.addEventListener('DOMContentLoaded', () => {
    const hoy = new Date().toISOString().split('T')[0];
    document.getElementById('rep_start').value = hoy;
    document.getElementById('rep_end').value = hoy;

    document.getElementById('btn_apply_filter').addEventListener('click', () => {
        loadReportData();
    });
});

function showMenu() {
    document.getElementById('view_menu').classList.add('active-view');
    document.getElementById('view_report_detail').classList.remove('active-view');
    document.getElementById('view_title').innerText = "Reportes del Sistema";
}

function showReport(type) {
    currentReportType = type;
    document.getElementById('view_menu').classList.remove('active-view');
    document.getElementById('view_report_detail').classList.add('active-view');
    
    const searchInput = document.getElementById('report_search_input');
    searchInput.value = ""; // Limpiar al cambiar de reporte
    
    const filters = document.getElementById('report_filters');
    const grpAgrupar = document.getElementById('grp_agrupar_por');
    const grpOrdenar = document.getElementById('grp_ordenar_por');
    const grpMetodo = document.getElementById('grp_metodo_pago');
    const searchContainer = document.getElementById('report_search_container');
    const historialActions = document.getElementById('historial_actions');

    filters.style.display = 'flex';
    grpAgrupar.style.display = 'none';
    grpOrdenar.style.display = 'none';
    grpMetodo.style.display = 'block';
    searchContainer.style.display = 'none'; 
    historialActions.style.display = 'none';

    let title = "";
    switch(type) {
        case 'ventas_hoy':
            title = "Ventas del Día";
            filters.style.display = 'none';
            break;
        case 'ventas_rango':
            title = "Resumen de Ventas y Ganancias";
            break;
        case 'ventas_producto':
            title = "Detalle de Ventas por Producto";
            searchContainer.style.display = 'block';
            searchInput.placeholder = "Buscar por nombre de producto o SKU...";
            break;
        case 'ventas_categoria':
            title = "Ventas por Categoría";
            searchContainer.style.display = 'block';
            searchInput.placeholder = "Buscar categoría...";
            break;
        case 'ventas_cliente':
            title = "Compras por Cliente (Ranking)";
            grpMetodo.style.display = 'none';
            searchContainer.style.display = 'block';
            searchInput.placeholder = "Buscar por nombre de cliente o documento...";
            break;
        case 'top_productos':
            title = "Top 10 Productos Más Vendidos";
            filters.style.display = 'none';
            break;
        case 'bajo_stock':
            title = "Alerta de Stock Bajo";
            filters.style.display = 'none';
            break;
        case 'kardex':
            title = "Kardex de Inventario";
            filters.style.display = 'none';
            break;
        case 'historial_recibos':
            title = "Historial Detallado de Recibos";
            historialActions.style.display = 'flex';
            break;
        case 'ventas_vendedor':
            title = "Rendimiento por Vendedor";
            filters.style.display = 'none';
            break;
    }

    document.getElementById('view_title').innerText = title;
    loadSearchSuggestions(type);
    loadReportData();
}

async function loadSearchSuggestions(type) {
    const datalist = document.getElementById('report_search_suggestions');
    datalist.innerHTML = ""; 
    try {
        let items = [];
        if (type === 'ventas_cliente') {
            const customers = await (await fetch(`${API_URL}/clientes-lista`)).json();
            items = customers.map(c => c.nombre);
        } else if (type === 'ventas_producto') {
            const products = await (await fetch(`${API_URL}/productos`)).json();
            items = products.map(p => p.nombre);
        }
        items.forEach(item => {
            const option = document.createElement('option');
            option.value = item;
            datalist.appendChild(option);
        });
    } catch (error) { console.error("Sugerencias desactivadas:", error); }
}

async function loadReportData() {
    const start = document.getElementById('rep_start').value;
    const end = document.getElementById('rep_end').value;
    const metodo = document.getElementById('rep_metodo').value;
    const tbody = document.getElementById('report_tbody');
    const stats = document.getElementById('report_stats');

    tbody.innerHTML = '<tr><td colspan="10" class="loading">Cargando datos...</td></tr>';
    stats.style.display = 'none';

    try {
        let url = "";
        let data = null;

        switch(currentReportType) {
            case 'ventas_hoy':
                url = `${API_URL}/reportes/dashboard`;
                data = await (await fetch(url)).json();
                renderVentasHoy(data);
                break;
            case 'ventas_rango':
                url = `${API_URL}/reportes/ventas-rango?inicio=${start}&fin=${end}&metodo_pago=${metodo}`;
                data = await (await fetch(url)).json();
                renderVentasRango(data);
                break;
            case 'ventas_producto':
                url = `${API_URL}/reportes/ventas-por-producto?inicio=${start}&fin=${end}&metodo_pago=${metodo}`;
                data = await (await fetch(url)).json();
                renderVentasProducto(data);
                break;
            case 'ventas_categoria':
                url = `${API_URL}/reportes/ventas-por-categoria?inicio=${start}&fin=${end}&metodo_pago=${metodo}`;
                data = await (await fetch(url)).json();
                renderVentasCategoria(data);
                break;
            case 'ventas_cliente':
                url = `${API_URL}/reportes/ventas-por-cliente?inicio=${start}&fin=${end}`;
                data = await (await fetch(url)).json();
                renderVentasCliente(data);
                break;
            case 'top_productos':
                url = `${API_URL}/reportes/top-productos?limit=10`;
                data = await (await fetch(url)).json();
                renderTopProductos(data);
                break;
            case 'bajo_stock':
                url = `${API_URL}/reportes/stock-bajo`;
                data = await (await fetch(url)).json();
                renderBajoStock(data);
                break;
            case 'kardex':
                url = `${API_URL}/reportes/kardex`;
                data = await (await fetch(url)).json();
                renderKardex(data);
                break;
            case 'historial_recibos':
                url = `${API_URL}/reportes/historial-ventas?inicio=${start}&fin=${end}`;
                data = await (await fetch(url)).json();
                renderHistorialRecibos(data);
                break;
            case 'ventas_vendedor':
                url = `${API_URL}/reportes/vendedores`;
                data = await (await fetch(url)).json();
                renderVendedores(data);
                break;
        }
        // Aplicar filtro si el usuario ya escribió algo antes de cargar
        filterReportTable();
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="10" style="color:red">Error al procesar el reporte.</td></tr>';
    }
}

function renderVentasHoy(dash) {
    const stats = document.getElementById('report_stats');
    const methods = dash.methods_today || {};
    
    // Mapeo amigable
    const displayNames = {
        'EFECTIVO': '💸 Efectivo',
        'TRANSFERENCIA': '💳 Transferencia',
        'YAPE/PLIN': '📱 Yape / Plin',
        'TARJETA': '💳 Tarjeta (Transf.)'
    };

    // Construir desglose para mostrar en las stats o en una sección
    let methodsHtml = '';
    Object.keys(methods).forEach(m => {
        methodsHtml += `<div class="stat-card"><h3>${displayNames[m] || m}</h3><p class="value">S/ ${(methods[m] || 0).toFixed(2)}</p></div>`;
    });

    stats.innerHTML = `
        <div class="stat-card" style="background: var(--primary-color)">
            <h3>Total Ventas Hoy</h3>
            <p class="value">S/ ${(dash.sales_today || 0).toFixed(2)}</p>
        </div>
        ${methodsHtml}
        <div class="stat-card"><h3>Total Clientes</h3><p class="value">${dash.total_clients || 0}</p></div>
        <div class="stat-card"><h3>Productos en Alerta</h3><p class="value" style="color:#ef4444">${dash.alerta_stock || 0}</p></div>
    `;
    stats.style.display = 'grid';
    
    document.getElementById('report_thead').innerHTML = '<tr><th>Producto</th><th>Cantidad Vendida</th></tr>';
    document.getElementById('report_tbody').innerHTML = (dash.top_productos || []).map(p => `
        <tr data-nombre="${p.nombre}"><td>${p.nombre}</td><td><strong>${p.total_qty}</strong></td></tr>
    `).join('');
}

function renderVentasRango(data) {
    const stats = document.getElementById('report_stats');
    const resumen = data.resumen || { ingresos_brutos: 0, ganancia_estimada: 0, total_neto: 0 };
    stats.innerHTML = `
        <div class="stat-card"><h3>Ingresos Brutos</h3><p class="value">S/ ${(resumen.ingresos_brutos || 0).toFixed(2)}</p></div>
        <div class="stat-card"><h3>Utilidad Estimada</h3><p class="value" style="color:#10b981">S/ ${(resumen.ganancia_estimada || 0).toFixed(2)}</p></div>
        <div class="stat-card"><h3>Total Neto (Sin IGV)</h3><p class="value">S/ ${(resumen.total_neto || 0).toFixed(2)}</p></div>
    `;
    stats.style.display = 'grid';
    
    document.getElementById('report_thead').innerHTML = `
        <tr>
            <th>Resumen de Ingresos</th>
            <th>Monto Total (S/)</th>
        </tr>
    `;
    
    const metodos = data.por_metodo || {};
    // Mapeo amigable de nombres de métodos
    const displayNames = {
        'EFECTIVO': '💸 EFECTIVO',
        'TRANSFERENCIA': '💳 TRANSFERENCIA / BANCO',
        'YAPE/PLIN': '📱 YAPE / PLIN',
        'TARJETA': '💳 TARJETA (Transferencia)'
    };

    let html = '';
    let granTotal = 0;

    // Listamos los métodos específicos
    Object.keys(metodos).forEach(m => {
        const monto = metodos[m] || 0;
        granTotal += monto;
        html += `<tr><td>${displayNames[m] || m}</td><td><strong>S/ ${monto.toFixed(2)}</strong></td></tr>`;
    });

    // Añadimos fila de total al final de la tabla
    html += `<tr style="background: rgba(255,255,255,0.05); border-top: 2px solid var(--border-color);">
                <td><strong>TOTAL RECAUDADO</strong></td>
                <td><strong style="color: var(--success); font-size: 1.1em;">S/ ${granTotal.toFixed(2)}</strong></td>
             </tr>`;

    document.getElementById('report_tbody').innerHTML = html;
}

function renderVentasProducto(data) {
    document.getElementById('report_thead').innerHTML = `
        <tr><th>SKU</th><th>Producto</th><th>Cant.</th><th>Efectivo</th><th>Transferencia</th><th>Yape/Plin</th><th>Total</th><th>Utilidad</th></tr>
    `;
    document.getElementById('report_tbody').innerHTML = data.map(p => `
        <tr data-sku="${p.codigo || ''}" data-nombre="${p.nombre || ''}">
            <td><code>${p.codigo || 'N/A'}</code></td>
            <td><strong>${p.nombre || 'Sin Nombre'}</strong></td>
            <td>${p.cant_vendida || 0}</td>
            <td style="color:#10b981">S/ ${(p.efectivo || 0).toFixed(2)}</td>
            <td style="color:#3b82f6">S/ ${(p.transferencia || 0).toFixed(2)}</td>
            <td style="color:#a855f7">S/ ${(p.yape_plin || 0).toFixed(2)}</td>
            <td><strong>S/ ${(p.total_generado || 0).toFixed(2)}</strong></td>
            <td style="font-weight:bold; color:#10b981">S/ ${(p.margen_ganancia || 0).toFixed(2)}</td>
        </tr>
    `).join('');
}

function renderVentasCategoria(data) {
    document.getElementById('report_thead').innerHTML = `
        <tr><th>Categoría</th><th>Cant. Vendida</th><th>Efectivo</th><th>Transferencia</th><th>Yape/Plin</th><th>Total</th><th>Utilidad</th></tr>
    `;
    document.getElementById('report_tbody').innerHTML = data.map(c => `
        <tr onclick="drillDownCategory('${c.categoria}')" style="cursor:pointer" title="Clic para ver detalle de productos">
            <td><strong>${c.categoria || 'SIN CATEGORÍA'}</strong> <i class="fas fa-search-plus" style="font-size:10px; color:var(--accent-color)"></i></td>
            <td>${c.cant_vendida || 0}</td>
            <td style="color:#10b981">S/ ${(c.efectivo || 0).toFixed(2)}</td>
            <td style="color:#3b82f6">S/ ${(c.transferencia || 0).toFixed(2)}</td>
            <td style="color:#a855f7">S/ ${(c.yape_plin || 0).toFixed(2)}</td>
            <td><strong>S/ ${(c.total_generado || 0).toFixed(2)}</strong></td>
            <td style="font-weight:bold; color:#10b981">S/ ${(c.margen_ganancia || 0).toFixed(2)}</td>
        </tr>
    `).join('');
}

async function drillDownCategory(cat) {
    const start = document.getElementById('rep_start').value;
    const end = document.getElementById('rep_end').value;
    
    try {
        const res = await fetch(`${API_URL}/reportes/ventas-por-categoria/detalles?categoria=${encodeURIComponent(cat)}&inicio=${start}&fin=${end}`);
        const details = await res.json();
        
        // Usamos un modal para mostrar el detalle
        let modal = document.getElementById('category_detail_modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'category_detail_modal';
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-content" style="max-width: 800px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                        <h2 id="cat_modal_title">Detalle de Categoría</h2>
                        <button onclick="document.getElementById('category_detail_modal').style.display='none'" class="btn-secondary" style="padding:5px 10px;">&times;</button>
                    </div>
                    <div class="table-responsive">
                        <table>
                            <thead>
                                <tr><th>Código</th><th>Producto</th><th>Cant.</th><th>Total</th><th>Pago</th><th>Fecha</th></tr>
                            </thead>
                            <tbody id="cat_modal_body"></tbody>
                        </table>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }
        
        document.getElementById('cat_modal_title').innerText = `Productos vendidos en: ${cat}`;
        document.getElementById('cat_modal_body').innerHTML = details.map(d => `
            <tr>
                <td><code>${d.codigo}</code></td>
                <td>${d.nombre}</td>
                <td>${d.cant_vendida}</td>
                <td>S/ ${d.total_generado.toFixed(2)}</td>
                <td><small class="badge">${d.metodo_pago}</small></td>
                <td><small>${d.date.split(' ')[0]}</small></td>
            </tr>
        `).join('');
        
        modal.style.display = 'block';
    } catch (e) {
        alert("Error al obtener detalles de la categoría");
    }
}

function renderVentasCliente(data) {
    document.getElementById('report_thead').innerHTML = `<tr><th>Cliente</th><th>Documento</th><th>Compras</th><th>Total Invertido</th><th>Última</th></tr>`;
    document.getElementById('report_tbody').innerHTML = data.map(c => `
        <tr data-nombre="${c.nombre || ''}" data-sku="${c.documento || ''}">
            <td><strong>${c.nombre || 'Desconocido'}</strong></td>
            <td>${c.documento || '-'}</td>
            <td>${c.num_compras || 0}</td>
            <td><strong>S/ ${(c.total_comprado || 0).toFixed(2)}</strong></td>
            <td><small>${c.ultima_compra || '-'}</small></td>
        </tr>
    `).join('');
}

function renderTopProductos(data) {
    document.getElementById('report_thead').innerHTML = '<tr><th>#</th><th>Producto</th><th>Unidades</th></tr>';
    document.getElementById('report_tbody').innerHTML = data.map((p, i) => `
        <tr data-nombre="${p.nombre}"><td>${i+1}</td><td>${p.nombre}</td><td><strong>${p.total_qty}</strong></td></tr>
    `).join('');
}

function renderBajoStock(data) {
    document.getElementById('report_thead').innerHTML = '<tr><th>SKU</th><th>Producto</th><th>Stock</th><th>Min</th><th>Falta</th></tr>';
    document.getElementById('report_tbody').innerHTML = data.map(p => `
        <tr data-sku="${p.codigo}" data-nombre="${p.nombre}"><td><code>${p.codigo}</code></td><td>${p.nombre}</td><td style="color:#ef4444">${p.stock}</td><td>${p.stock_minimo}</td><td><span class="badge badge-red">${p.faltante}</span></td></tr>
    `).join('');
}

function renderKardex(data) {
    document.getElementById('report_thead').innerHTML = '<tr><th>Fecha</th><th>Tipo</th><th>SKU</th><th>Cant</th><th>Precio</th></tr>';
    document.getElementById('report_tbody').innerHTML = data.map(k => `
        <tr data-sku="${k.producto_codigo}"><td><small>${k.date}</small></td><td>${k.tipo}</td><td><code>${k.producto_codigo}</code></td><td>${k.cant}</td><td>S/ ${(k.precio || 0).toFixed(2)}</td></tr>
    `).join('');
}

function renderHistorialRecibos(data) {
    document.getElementById('report_thead').innerHTML = '<tr><th>ID</th><th>Fecha</th><th>Cliente</th><th>Total</th><th>Estado</th></tr>';
    document.getElementById('report_tbody').innerHTML = data.map(v => `
        <tr onclick="selectReceiptRow(this, ${v.transaction_id})" style="cursor:pointer" data-nombre="${v.cliente}" data-sku="${v.transaction_id}">
            <td>${v.transaction_id}</td><td><small>${v.transaction_date}</small></td><td>${v.cliente}</td><td><strong>S/ ${(v.transaction_total || 0).toFixed(2)}</strong></td><td>${v.status}</td>
        </tr>
    `).join('');
}

function renderVendedores(data) {
    document.getElementById('report_thead').innerHTML = '<tr><th>Vendedor</th><th>N° Ventas</th><th>Total (S/)</th></tr>';
    document.getElementById('report_tbody').innerHTML = data.map(v => `
        <tr data-nombre="${v.username}"><td><strong>${v.username}</strong></td><td>${v.num_ventas}</td><td><strong>S/ ${(v.total_vendido || 0).toFixed(2)}</strong></td></tr>
    `).join('');
}

function selectReceiptRow(row, id) {
    document.querySelectorAll('#report_tbody tr').forEach(r => r.classList.remove('selected-row'));
    row.classList.add('selected-row');
    selectedReceiptId = id;
}

async function viewSelectedReceipt() {
    if (!selectedReceiptId) return alert("Seleccione un recibo.");
    window.open(`${API_URL}/ventas/${selectedReceiptId}/ticket`, '_blank');
}

async function editSelectedReceipt() {
    if (!selectedReceiptId) return alert("Seleccione un recibo.");
    try {
        const data = await (await fetch(`${API_URL}/ventas/${selectedReceiptId}/detalles`)).json();
        const v = data.venta;
        document.getElementById('edit_sale_id').value = v.id;
        document.getElementById('edit_cliente_nombre').value = v.cliente_nombre || "";
        document.getElementById('edit_cliente_doc').value = v.cliente_documento || "";
        document.getElementById('edit_tipo_comp').value = v.tipo_comprobante;
        document.getElementById('edit_metodo').value = v.metodo_pago.replace('TARJETA', 'TRANSFERENCIA');
        document.getElementById('receipt_items_body').innerHTML = data.items.map(item => `
            <tr><td>${item.nombre}</td><td>${item.quantity}</td><td>S/ ${(item.unit_price || 0).toFixed(2)}</td><td>S/ ${(item.quantity * item.unit_price).toFixed(2)}</td></tr>
        `).join('');
        document.getElementById('receipt_total').innerText = (v.total || 0).toFixed(2);
        document.getElementById('receipt_modal').style.display = 'block';
        document.getElementById('btn_save_receipt').style.display = v.status === 'VOIDED' ? 'none' : 'inline-block';
        document.getElementById('receipt_modal_title').innerText = v.status === 'VOIDED' ? "Recibo (ANULADO)" : "Detalle de Recibo";
    } catch (error) { alert("Error al cargar detalles."); }
}

function closeReceiptModal() { document.getElementById('receipt_modal').style.display = 'none'; }

async function voidSelectedSale() {
    if (!selectedReceiptId) return alert("Seleccione un recibo.");
    const reason = prompt("Motivo de anulación:");
    if (!reason || !confirm("¿Anular recibo?")) return;
    try {
        const response = await fetch(`${API_URL}/ventas/${selectedReceiptId}/anular`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: localStorage.getItem('user_id'), reason: reason })
        });
        if (response.ok) { alert("✅ Anulado."); loadReportData(); }
        else { const err = await response.json(); alert("❌ Error: " + err.detail); }
    } catch (error) { alert("Error de conexión."); }
}

/**
 * FILTRADO ESTRICTO E INTELIGENTE
 * Solo muestra filas que coinciden con las palabras buscadas.
 * Prioriza los mejores resultados al inicio.
 */
function filterReportTable() {
    const input = document.getElementById('report_search_input');
    const query = input.value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
    const words = query.split(/\s+/).filter(w => w.length > 0);
    const tbody = document.getElementById('report_tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    if (words.length === 0) {
        rows.forEach(row => row.style.display = '');
        return;
    }

    const matches = [];

    rows.forEach(row => {
        // Obtenemos los datos de búsqueda de la fila
        const sku = (row.getAttribute('data-sku') || "").toLowerCase();
        const nombre = (row.getAttribute('data-nombre') || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        const pool = (sku + " " + nombre).trim();
        
        let score = 0;
        let matchesAll = true;

        words.forEach(word => {
            const idxNombre = nombre.indexOf(word);
            const idxSku = sku.indexOf(word);

            if (idxNombre !== -1 || idxSku !== -1) {
                // RANKING: Dar puntos por cercanía al inicio
                if (idxNombre !== -1) score += (3000 - idxNombre);
                if (idxSku !== -1) score += (1000 - idxSku);
                // Bonus por palabra exacta
                if (nombre === word || sku === word) score += 5000;
                if (nombre.startsWith(word)) score += 1000;
            } else {
                // Si una de las palabras buscadas NO está en la fila, se descarta
                matchesAll = false;
            }
        });

        if (matchesAll && pool.length > 0) {
            row.style.display = '';
            matches.push({ row, score });
        } else {
            row.style.display = 'none'; // ESTRICTO: Si no coincide, se oculta
        }
    });

    // REORDENAR FÍSICAMENTE: Los mejores resultados suben al tope
    matches.sort((a, b) => b.score - a.score);
    matches.forEach(m => tbody.appendChild(m.row));
}

function printFromModal() {
    const id = document.getElementById('edit_sale_id').value;
    window.open(`${API_URL}/ventas/${id}/ticket`, '_blank');
}
