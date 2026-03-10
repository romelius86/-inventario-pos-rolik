// common.js - Lógica compartida para seguridad y permisos
const API_URL = "http://127.0.0.1:8000";

// --- UTILIDADES ---

function formatCurrency(amount) {
    return "S/ " + parseFloat(amount).toFixed(2);
}

function debounce(func, timeout = 300) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => { func.apply(this, args); }, timeout);
    };
}

/**
 * Renderiza una tabla genérica
 * @param {Array} data - Lista de objetos a mostrar
 * @param {Array} columns - Configuración de columnas [{label: 'Nombre', key: 'nombre', formatter: val => val}]
 * @param {string} containerId - ID del <tbody> donde se insertarán las filas
 */
function renderTable(data, columns, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = "";
    
    if (data.length === 0) {
        container.innerHTML = `<tr><td colspan="${columns.length}" style="text-align:center; padding:20px; color:var(--text-muted);">No se encontraron registros.</td></tr>`;
        return;
    }

    data.forEach(item => {
        const tr = document.createElement('tr');
        columns.forEach(col => {
            const td = document.createElement('td');
            let value = item[col.key];
            if (col.formatter) value = col.formatter(value, item);
            td.innerHTML = value !== undefined ? value : "";
            if (col.style) td.style = col.style;
            tr.appendChild(td);
        });
        container.appendChild(tr);
    });
}

function getLoggedInUser() {
    const stored = sessionStorage.getItem('user');
    if (!stored) return null;
    return JSON.parse(stored);
}

function hasPermission(permission) {
    const user = getLoggedInUser();
    if (!user) return false;
    
    // Los admins suelen tener todos los permisos en sistemas ERP
    if (user.role === 'admin') return true;
    
    if (!user.permissions) return false;
    
    // Permisos que no existen en DB pero queremos controlar
    if (permission === 'dashboard.view') return true; // Todos ven el dashboard
    if (permission === 'customer.view') return true;  // Basado en main.py, todos ven clientes
    
    return user.permissions.includes(permission);
}

function checkAccess() {
    const user = getLoggedInUser();
    if (!user && !window.location.href.includes('login.html')) {
        window.location.href = 'login.html';
        return;
    }
    
    // Al cargar el DOM, aplicar visibilidad de menú
    document.addEventListener('DOMContentLoaded', () => {
        applyPermissions();
        updateUserDisplay();
    });
}

function updateUserDisplay() {
    const user = getLoggedInUser();
    if (!user) return;
    
    const nameEl = document.getElementById('user_name_display');
    const roleEl = document.getElementById('user_role_display');
    if (nameEl) nameEl.textContent = user.username;
    if (roleEl) roleEl.textContent = user.role.toUpperCase();
    
    const logoutBtn = document.querySelector('.logout-btn');
    if (logoutBtn) {
        logoutBtn.onclick = () => {
            sessionStorage.removeItem('user');
            window.location.href = 'login.html';
        };
    }
}

function applyPermissions() {
    // Lista de mapeo: ID de elemento -> Permiso requerido
    const permissionMap = {
        'nav_dashboard': 'dashboard.view', // Generalmente todos ven dashboard
        'nav_pos': 'pos.use',
        'nav_inventory': 'product.view',
        'nav_clients': 'customer.view',
        'nav_purchases': 'purchase_order.view',
        'nav_cash': 'cash.manage',
        'nav_reports': 'report.view.sales',
        'nav_users': 'user.view'
    };

    for (const [id, perm] of Object.entries(permissionMap)) {
        const el = document.getElementById(id);
        if (el && !hasPermission(perm)) {
            el.style.display = 'none';
        }
    }

    // Botones de acción específicos
    const actionButtons = {
        'btn_new_product': 'product.create',
        'btn_new_customer': 'customer.create', // Asumido
        'btn_new_order': 'purchase_order.create',
        'btn_new_user': 'user.create'
    };

    for (const [id, perm] of Object.entries(actionButtons)) {
        const btn = document.getElementById(id);
        if (btn && !hasPermission(perm)) {
            btn.style.display = 'none';
        }
    }
}

// Ejecutar chequeo de inmediato
if (!window.location.href.includes('login.html')) {
    const user = getLoggedInUser();
    if (!user) {
        window.location.href = 'login.html';
    }
}

// Lógica para Menú Hamburguesa (Responsive)
document.addEventListener('DOMContentLoaded', () => {
    const header = document.querySelector('header');
    if (header && !document.querySelector('.menu-toggle')) {
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'menu-toggle';
        toggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
        toggleBtn.onclick = () => {
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) sidebar.classList.toggle('active');
        };
        header.prepend(toggleBtn);
    }

    // Cerrar sidebar al hacer clic en el contenido principal (en móviles)
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.addEventListener('click', () => {
            const sidebar = document.querySelector('.sidebar');
            if (sidebar && sidebar.classList.contains('active') && window.innerWidth <= 768) {
                sidebar.classList.remove('active');
            }
        });
    }
});
