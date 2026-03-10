// usuarios_script.js - Lógica para Usuarios

document.addEventListener('DOMContentLoaded', () => {
    fetchUsers();
});

async function fetchUsers() {
    try {
        const response = await fetch(`${API_URL}/usuarios`);
        const users = await response.json();
        renderUsers(users);
    } catch (error) { console.error(error); }
}

function renderUsers(users) {
    const tbody = document.getElementById('users_body');
    if (!tbody) return;
    tbody.innerHTML = "";
    
    users.forEach(u => {
        const tr = document.createElement('tr');
        // El admin no necesita que le asignen permisos, ya los tiene todos
        const permBtn = u.role !== 'admin' ? 
            `<button class="action-btn" style="background:#3b82f6; color:white;" onclick="openPermissionsModal(${u.id}, '${u.username}')" title="Permisos"><i class="fas fa-key"></i></button>` : '';

        tr.innerHTML = `
            <td><strong style="color: white;">${u.username}</strong></td>
            <td>${u.role === 'admin' ? '<i class="fas fa-crown" style="color: gold;"></i> Admin' : '<i class="fas fa-user"></i> Vendedor'}</td>
            <td>${u.is_active ? '<span class="stock-badge">ACTIVO</span>' : '<span class="stock-badge stock-low">INACTIVO</span>'}</td>
            <td>
                <div style="display: flex; gap: 5px;">
                    <button class="action-btn edit-btn" onclick='editUser(${JSON.stringify(u).replace(/'/g, "&apos;")})' title="Editar"><i class="fas fa-user-edit"></i></button>
                    ${permBtn}
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function openUserModal() {
    const form = document.getElementById('user_form');
    const modal = document.getElementById('user_modal');
    const title = document.getElementById('user_modal_title');
    const pass = document.getElementById('u_password');

    if (form) form.reset();
    document.getElementById('u_id').value = "";
    if (title) title.innerText = "Nuevo Usuario";
    if (pass) pass.required = true;
    if (modal) modal.style.display = "block";
}

function closeUserModal() {
    const modal = document.getElementById('user_modal');
    if (modal) modal.style.display = "none";
}

function editUser(user) {
    document.getElementById('u_id').value = user.id;
    document.getElementById('u_username').value = user.username;
    document.getElementById('u_role').value = user.role;
    document.getElementById('u_active').value = user.is_active;
    const pass = document.getElementById('u_password');
    if (pass) pass.required = false;
    const title = document.getElementById('user_modal_title');
    if (title) title.innerText = "Editar Usuario";
    const modal = document.getElementById('user_modal');
    if (modal) modal.style.display = "block";
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('user_form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const userData = {
                id: document.getElementById('u_id').value ? parseInt(document.getElementById('u_id').value) : null,
                username: document.getElementById('u_username').value,
                password: document.getElementById('u_password').value || null,
                role: document.getElementById('u_role').value,
                is_active: parseInt(document.getElementById('u_active').value)
            };

            try {
                const response = await fetch(`${API_URL}/usuarios`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(userData)
                });

                if (response.ok) {
                    closeUserModal();
                    fetchUsers();
                    alert("Usuario guardado");
                } else {
                    const err = await response.json();
                    alert("Error: " + err.detail);
                }
            } catch (error) { alert("Error de conexión"); }
        });
    }
});

// --- Lógica de Permisos ---

let allPermissions = [];

async function openPermissionsModal(userId, username) {
    document.getElementById('perm_user_id').value = userId;
    document.getElementById('perm_modal_title').innerText = `Permisos para: ${username}`;
    
    const listDiv = document.getElementById('permissions_list');
    listDiv.innerHTML = "<p class='loading'>Cargando permisos...</p>";
    
    try {
        // 1. Obtener todos los permisos si no los tenemos
        if (allPermissions.length === 0) {
            const res = await fetch(`${API_URL}/permisos`);
            allPermissions = await res.json();
        }
        
        // 2. Obtener permisos del usuario
        const resUser = await fetch(`${API_URL}/usuarios/${userId}/permisos`);
        const userData = await resUser.json();
        const userPermIds = userData.ids;
        
        // 3. Renderizar lista
        listDiv.innerHTML = "";
        allPermissions.forEach(p => {
            const isChecked = userPermIds.includes(p.id) ? 'checked' : '';
            const item = document.createElement('div');
            item.style.display = "flex";
            item.style.alignItems = "center";
            item.style.gap = "10px";
            item.style.padding = "8px";
            item.style.borderBottom = "1px solid #334155";
            
            item.innerHTML = `
                <input type="checkbox" class="perm-check" value="${p.id}" ${isChecked} style="width: 20px; height: 20px;">
                <div style="flex-grow: 1;">
                    <div style="font-weight: 600; font-size: 14px; color: white;">${p.name}</div>
                    <div style="font-size: 12px; color: var(--text-muted);">${p.description || ''}</div>
                </div>
            `;
            listDiv.appendChild(item);
        });
        
        document.getElementById('permissions_modal').style.display = "block";
    } catch (error) {
        console.error(error);
        alert("Error al cargar permisos");
    }
}

function closePermissionsModal() {
    document.getElementById('permissions_modal').style.display = "none";
}

async function saveUserPermissions() {
    const userId = document.getElementById('perm_user_id').value;
    const checkboxes = document.querySelectorAll('.perm-check:checked');
    const selectedIds = Array.from(checkboxes).map(cb => parseInt(cb.value));
    
    try {
        const response = await fetch(`${API_URL}/usuarios/${userId}/permisos`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(selectedIds)
        });
        
        if (response.ok) {
            alert("Permisos actualizados correctamente");
            closePermissionsModal();
        } else {
            alert("Error al guardar permisos");
        }
    } catch (error) {
        console.error(error);
        alert("Error de conexión");
    }
}
