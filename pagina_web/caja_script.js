// caja_script.js - Lógica Avanzada para Gestión de Caja

let currentSession = null;

document.addEventListener('DOMContentLoaded', () => {
    updateSessionStatus();
});

async function updateSessionStatus() {
    try {
        const response = await fetch(`${API_URL}/caja/sesion-activa`);
        const data = await response.json();
        const statusBar = document.getElementById('cash_status_bar');
        const closeBtn = document.getElementById('btn_close_caja');

        if (data.active) {
            currentSession = data.session;
            const startDate = new Date(currentSession.open_date).toLocaleString();
            statusBar.innerHTML = `🟢 ESTADO: CAJA ABIERTA | Inicio: ${startDate}`;
            statusBar.style.color = '#10b981';
            if (closeBtn) {
                closeBtn.innerText = "Cerrar Caja (Corte Z)";
                closeBtn.onclick = handleCloseCaja;
            }
        } else {
            currentSession = null;
            statusBar.innerHTML = `🔴 ESTADO: CAJA CERRADA`;
            statusBar.style.color = '#ef4444';
            if (closeBtn) {
                closeBtn.innerText = "Abrir Nueva Caja";
                closeBtn.onclick = openOpenModal;
            }
        }
    } catch (error) { console.error(error); }
}

async function fetchResumen() {
    if (!currentSession) return alert("No hay una sesión de caja activa.");
    
    try {
        const response = await fetch(`${API_URL}/caja/resumen`);
        const data = await response.json();
        
        document.getElementById('empty_state').style.display = 'none';
        document.getElementById('history_content').style.display = 'none';
        document.getElementById('summary_content').style.display = 'block';

        document.getElementById('txt_inicial').textContent = `S/ ${data.inicial.toFixed(2)}`;
        
        // Resetear KPIs de métodos de pago
        let vEfectivo = 0, vYape = 0, vTransf = 0;
        const totalVentas = Object.values(data.ventas).reduce((a, b) => a + b, 0);
        document.getElementById('txt_ventas').textContent = `S/ ${totalVentas.toFixed(2)}`;

        const listVentas = document.getElementById('list_ventas');
        listVentas.innerHTML = "";
        
        for (const [metodo, monto] of Object.entries(data.ventas)) {
            const metUpper = metodo.toUpperCase();
            if (metUpper.includes('EFECTIVO')) vEfectivo += monto;
            else if (metUpper.includes('YAPE') || metUpper.includes('PLIN')) vYape += monto;
            else if (metUpper.includes('TARJETA') || metUpper.includes('TRANSF')) vTransf += monto;
            else {
                const div = document.createElement('div');
                div.className = "summary-item";
                div.innerHTML = `<span>${metodo}</span> <strong>S/ ${monto.toFixed(2)}</strong>`;
                listVentas.appendChild(div);
            }
        }

        // Asignar a tarjetas principales
        document.getElementById('txt_v_efectivo').textContent = `S/ ${vEfectivo.toFixed(2)}`;
        document.getElementById('txt_v_yape').textContent = `S/ ${vYape.toFixed(2)}`;
        document.getElementById('txt_v_transf').textContent = `S/ ${vTransf.toFixed(2)}`;
        
        // Efectivo en Caja = Inicial + Ventas Efectivo + Ingresos Manuales - Retiros Manuales
        const movNeto = (data.movimientos['INGRESO'] || 0) - (data.movimientos['RETIRO'] || 0);
        const efectivoCaja = data.inicial + vEfectivo + movNeto;
        document.getElementById('txt_efectivo_caja').textContent = `S/ ${efectivoCaja.toFixed(2)}`;

        const listMov = document.getElementById('list_movimientos');
        listMov.innerHTML = "";
        for (const [tipo, monto] of Object.entries(data.movimientos)) {
            const div = document.createElement('div');
            div.className = "summary-item";
            div.innerHTML = `<span style="color: ${tipo === 'INGRESO' ? '#22c55e' : '#ef4444'};">${tipo}</span> <strong>S/ ${monto.toFixed(2)}</strong>`;
            listMov.appendChild(div);
        }
    } catch (error) { console.error(error); }
}

async function handleCloseCaja() {
    if (!confirm("¿Estás seguro de que deseas cerrar la caja y realizar el Corte Z?")) return;

    try {
        const user = getLoggedInUser();
        const response = await fetch(`${API_URL}/caja/cerrar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: user.id })
        });

        if (response.ok) {
            alert("Caja cerrada correctamente. Se ha generado el Corte Z.");
            location.reload();
        } else {
            const err = await response.json();
            alert("Error: " + err.detail);
        }
    } catch (error) { alert("Error de conexión"); }
}

function openOpenModal() {
    document.getElementById('open_fondo').value = "0.00";
    document.getElementById('open_caja_modal').style.display = 'block';
}

function closeOpenModal() {
    document.getElementById('open_caja_modal').style.display = 'none';
}

async function confirmOpenCaja() {
    const fondo = parseFloat(document.getElementById('open_fondo').value) || 0;
    const user = getLoggedInUser();

    try {
        const response = await fetch(`${API_URL}/caja/abrir`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fondo_inicial: fondo, user_id: user.id })
        });

        if (response.ok) {
            alert("¡Caja abierta exitosamente!");
            location.reload();
        } else {
            const err = await response.json();
            alert("Error: " + err.detail);
        }
    } catch (error) { alert("Error de conexión"); }
}

async function loadHistory() {
    try {
        const response = await fetch(`${API_URL}/caja/historial`);
        const history = await response.json();
        
        document.getElementById('empty_state').style.display = 'none';
        document.getElementById('summary_content').style.display = 'none';
        document.getElementById('history_content').style.display = 'block';

        const tbody = document.getElementById('history_tbody');
        tbody.innerHTML = "";
        history.reverse().forEach(h => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${new Date(h.open_date).toLocaleString()}</td>
                <td>${h.close_date ? new Date(h.close_date).toLocaleString() : '---'}</td>
                <td>S/ ${h.initial_fund.toFixed(2)}</td>
                <td>S/ ${h.total_sales.toFixed(2)}</td>
                <td><span class="stock-badge ${h.status === 'OPEN' ? '' : 'stock-low'}">${h.status}</span></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) { console.error(error); }
}

// --- Movimientos Manuales ---
function openMovementModal(tipo) {
    if (!currentSession) return alert("Debes abrir la caja primero");
    document.getElementById('mov_tipo').value = tipo;
    document.getElementById('mov_title').textContent = tipo === 'INGRESO' ? "Nuevo Ingreso Manual" : "Nuevo Retiro Manual";
    document.getElementById('movement_form').reset();
    document.getElementById('movement_modal').style.display = "block";
}

function closeMovementModal() {
    document.getElementById('movement_modal').style.display = "none";
}

document.getElementById('movement_form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const user = getLoggedInUser();
    const movData = {
        user_id: user.id,
        tipo: document.getElementById('mov_tipo').value,
        monto: parseFloat(document.getElementById('mov_monto').value),
        descripcion: document.getElementById('mov_desc').value
    };

    try {
        const response = await fetch(`${API_URL}/caja/movimiento`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(movData)
        });

        if (response.ok) {
            closeMovementModal();
            fetchResumen();
            alert("Movimiento registrado");
        } else {
            const err = await response.json();
            alert("Error: " + err.detail);
        }
    } catch (error) { alert("Error de conexión"); }
});
