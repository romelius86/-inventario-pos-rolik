import sqlite3
from datetime import datetime

DB_NAME = "erp_system.db"

def get_connection():
    """Obtiene una conexión a la base de datos."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Devuelve filas como diccionarios
    return conn

def init_db():
    """Inicializa la base de datos creando las tablas solo si no existen."""
    conn = get_connection()
    cursor = conn.cursor()

    # Tabla de Proveedores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            ruc_dni TEXT,
            direccion TEXT,
            telefono TEXT,
            email TEXT
        )
    ''')

    # Añadir columnas a suppliers si no existen
    for col, col_type in [("ruc_dni", "TEXT"), ("direccion", "TEXT"), ("telefono", "TEXT"), ("email", "TEXT")]:
        try:
            cursor.execute(f"ALTER TABLE suppliers ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError: pass

    # Tabla de Productos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            codigo TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            fabricante TEXT,
            categoria TEXT,
            descripcion TEXT,
            precio_venta REAL DEFAULT 0.0,
            precio_compra REAL DEFAULT 0.0,
            unidad TEXT,
            stock INTEGER DEFAULT 0,
            stock_minimo INTEGER DEFAULT 5,
            proveedor_id INTEGER,
            fecha_ingreso TIMESTAMP,
            FOREIGN KEY (proveedor_id) REFERENCES suppliers(id)
        )
    ''')

    # Tabla de Órdenes de Compra
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_oc TEXT UNIQUE,
            proveedor_id INTEGER,
            fecha_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_llegada TIMESTAMP,
            fecha_estimada DATE,
            estado TEXT DEFAULT 'PENDIENTE',
            condicion_pago TEXT,
            lugar_entrega TEXT,
            responsable_recibe TEXT,
            tipo_entrega TEXT,
            subtotal REAL DEFAULT 0.0,
            igv REAL DEFAULT 0.0,
            total REAL DEFAULT 0.0,
            FOREIGN KEY (proveedor_id) REFERENCES suppliers(id)
        )
    ''')

    # Añadir nuevas columnas a purchase_orders si no existen
    new_po_cols = [
        ("numero_oc", "TEXT UNIQUE"), ("fecha_estimada", "DATE"), 
        ("condicion_pago", "TEXT"), ("lugar_entrega", "TEXT"), 
        ("responsable_recibe", "TEXT"), ("tipo_entrega", "TEXT"), 
        ("subtotal", "REAL DEFAULT 0.0"), ("igv", "REAL DEFAULT 0.0"), 
        ("total", "REAL DEFAULT 0.0")
    ]
    for col, col_type in new_po_cols:
        try:
            cursor.execute(f"ALTER TABLE purchase_orders ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError: pass
    
    # Detalle de Órdenes de Compra
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchase_order_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER,
            producto_codigo TEXT,
            cantidad INTEGER,
            precio_compra_unitario REAL,
            FOREIGN KEY (pedido_id) REFERENCES purchase_orders(id),
            FOREIGN KEY (producto_codigo) REFERENCES products(id)
        )
    ''')

    # Tablas de Ventas y Caja
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cash_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            open_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            close_date TIMESTAMP,
            initial_fund REAL DEFAULT 0.0,
            total_sales REAL DEFAULT 0.0,
            status TEXT DEFAULT 'OPEN'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_id INTEGER,
            total REAL,
            metodo_pago TEXT, -- Efectivo, Tarjeta, Yape, Mixto, etc.
            tipo_comprobante TEXT, -- Boleta, Factura, Ticket
            correlativo TEXT, -- B001-00001, etc.
            monto_pagado REAL DEFAULT 0.0,
            vuelto REAL DEFAULT 0.0,
            user_id INTEGER,
            FOREIGN KEY (session_id) REFERENCES cash_sessions(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Añadir columnas si no existen (migración)
    for col, col_type in [
        ("metodo_pago", "TEXT"), ("tipo_comprobante", "TEXT"), 
        ("correlativo", "TEXT"), ("monto_pagado", "REAL"), 
        ("vuelto", "REAL"), ("cliente_nombre", "TEXT"), 
        ("cliente_documento", "TEXT"), ("cliente_direccion", "TEXT"),
        ("cliente_telefono", "TEXT"), ("cliente_email", "TEXT")
    ]:
        try:
            cursor.execute(f"ALTER TABLE transactions ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError: pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaction_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER,
            producto_codigo TEXT,
            quantity INTEGER,
            unit_price REAL,
            FOREIGN KEY (transaction_id) REFERENCES transactions(id),
            FOREIGN KEY (producto_codigo) REFERENCES products(codigo)
        )
    ''')
    
    # Tabla de Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'seller')),
            is_active INTEGER NOT NULL DEFAULT 1
        )
    ''')

    # Crear usuarios por defecto si no existen
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('vendedor', 'vendedor123', 'seller')")

    # Añadir columna is_active a users si no existe
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")
    except sqlite3.OperationalError:
        pass # La columna ya existe

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_discount_enabled INTEGER NOT NULL DEFAULT 0") # Nuevo campo
        cursor.execute("ALTER TABLE users ADD COLUMN max_discount_percentage INTEGER NOT NULL DEFAULT 0") # Nuevo campo
        cursor.execute("ALTER TABLE users ADD COLUMN commission_rate REAL NOT NULL DEFAULT 0.0") # Nuevo campo
    except sqlite3.OperationalError:
        pass # La columna ya existe

    # Añadir columna user_id a transactions si no existe
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER REFERENCES users(id)")
    except sqlite3.OperationalError:
        pass

    # Añadir columnas opened_by_user_id y closed_by_user_id a cash_sessions si no existen
    try:
        cursor.execute("ALTER TABLE cash_sessions ADD COLUMN opened_by_user_id INTEGER REFERENCES users(id)")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE cash_sessions ADD COLUMN closed_by_user_id INTEGER REFERENCES users(id)")
    except sqlite3.OperationalError:
        pass

    # Tabla de Comisiones Ganadas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commissions_earned (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            transaction_id INTEGER NOT NULL,
            commission_amount REAL NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (transaction_id) REFERENCES transactions(id)
        )
    ''')

    # Tabla de Clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            documento TEXT UNIQUE,
            nombre TEXT,
            direccion TEXT,
            telefono TEXT,
            email TEXT
        )
    ''')

    # --- Permisos ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_permissions (
            user_id INTEGER,
            permission_id INTEGER,
            PRIMARY KEY (user_id, permission_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
        )
    ''')

    # Poblar tabla de permisos si está vacía
    cursor.execute("SELECT COUNT(*) FROM permissions")
    if cursor.fetchone()[0] == 0:
        all_permissions = [
            ('user.view', 'Ver la lista de usuarios'),
            ('user.create', 'Crear nuevos usuarios'),
            ('user.edit', 'Editar usuarios existentes'),
            ('user.delete', 'Eliminar usuarios'),
            ('user.manage_permissions', 'Asignar permisos a usuarios'),
            ('product.view', 'Ver inventario'),
            ('product.create', 'Crear nuevos productos'),
            ('product.edit', 'Editar productos'),
            ('product.delete', 'Eliminar productos'),
            ('product.import', 'Importar productos desde archivo'),
            ('purchase_order.view', 'Ver órdenes de compra'),
            ('purchase_order.create', 'Crear órdenes de compra'),
            ('purchase_order.receive', 'Marcar órdenes de compra como recibidas'),
            ('pos.use', 'Usar el punto de venta'),
            ('pos.apply_discount', 'Aplicar descuentos en el POS'),
            ('cash.manage', 'Abrir y cerrar caja'),
            ('report.view.sales', 'Ver reporte de ventas'),
            ('report.view.cash', 'Ver reporte de caja'),
            ('report.view.commissions', 'Ver reporte de comisiones')
        ]
        cursor.executemany("INSERT INTO permissions (name, description) VALUES (?, ?)", all_permissions)

        # Asignar todos los permisos al usuario 'admin' por defecto
        admin_user = cursor.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
        if admin_user:
            permissions_ids = cursor.execute("SELECT id FROM permissions").fetchall()
            user_perms_to_insert = [(admin_user['id'], perm_id['id']) for perm_id in permissions_ids]
            cursor.executemany("INSERT INTO user_permissions (user_id, permission_id) VALUES (?, ?)", user_perms_to_insert)
        
    conn.commit()
    conn.close()

# --- Funciones de Usuarios ---
def authenticate_user(username, password):
    """Verifica si el usuario y la contraseña son correctos y si está activo.
       Devuelve un diccionario con los datos del usuario, incluyendo un set de sus permisos.
    """
    conn = get_connection()
    user = conn.execute("SELECT id, username, role, is_active, is_discount_enabled, max_discount_percentage, commission_rate FROM users WHERE username = ? AND password = ? AND is_active = 1", (username, password)).fetchone()
    
    if user:
        user_data = dict(user)
        user_data['permissions'] = get_user_permissions(user_data['id'])
        conn.close()
        return user_data
    
    conn.close()
    return None

def get_all_users():
    """Devuelve la lista de todos los usuarios, incluyendo su estado, configuración de descuento y tasa de comisión."""
    conn = get_connection()
    users = conn.execute("SELECT id, username, role, is_active, is_discount_enabled, max_discount_percentage, commission_rate FROM users").fetchall()
    conn.close()
    return users

def get_user_by_id(user_id):
    """Obtiene un usuario específico por su ID, incluyendo su configuración de descuento y tasa de comisión."""
    conn = get_connection()
    user = conn.execute("SELECT id, username, role, is_active, is_discount_enabled, max_discount_percentage, commission_rate FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

def add_user(username, password, role, is_discount_enabled=0, max_discount_percentage=0, commission_rate=0.0):
    """Crea un nuevo usuario (activo por defecto) con configuración de descuento y tasa de comisión."""
    conn = get_connection()
    try:
        conn.execute("INSERT INTO users (username, password, role, is_discount_enabled, max_discount_percentage, commission_rate) VALUES (?, ?, ?, ?, ?, ?)", (username, password, role, is_discount_enabled, max_discount_percentage, commission_rate))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_user(user_id, username, role, is_discount_enabled, max_discount_percentage, commission_rate):
    """Actualiza el nombre de usuario, el rol, la configuración de descuento y la tasa de comisión."""
    conn = get_connection()
    try:
        conn.execute("UPDATE users SET username = ?, role = ?, is_discount_enabled = ?, max_discount_percentage = ?, commission_rate = ? WHERE id = ?", (username, role, is_discount_enabled, max_discount_percentage, commission_rate, user_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # El nuevo username ya existe
    finally:
        conn.close()

def update_user_password(user_id, new_password):
    """Actualiza la contraseña de un usuario."""
    conn = get_connection()
    conn.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, user_id))
    conn.commit()
    conn.close()

def get_all_permissions():
    """Obtiene todos los permisos disponibles en el sistema."""
    conn = get_connection()
    permissions = conn.execute("SELECT id, name, description FROM permissions ORDER BY name").fetchall()
    conn.close()
    return permissions

def get_user_permissions(user_id):
    """Obtiene los nombres de todos los permisos asignados a un usuario."""
    conn = get_connection()
    perms = conn.execute("""
        SELECT p.name
        FROM user_permissions up
        JOIN permissions p ON up.permission_id = p.id
        WHERE up.user_id = ?
    """, (user_id,)).fetchall()
    conn.close()
    return {p['name'] for p in perms} # Devuelve un set para búsquedas rápidas

def update_user_permissions(user_id, permission_ids_to_set):
    """Actualiza los permisos de un usuario, reemplazando los existentes."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Borrar todos los permisos actuales del usuario
        cursor.execute("DELETE FROM user_permissions WHERE user_id = ?", (user_id,))
        
        # 2. Insertar los nuevos permisos
        if permission_ids_to_set:
            data_to_insert = [(user_id, perm_id) for perm_id in permission_ids_to_set]
            cursor.executemany("INSERT INTO user_permissions (user_id, permission_id) VALUES (?, ?)", data_to_insert)
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def set_user_active_status(user_id, is_active):
    """Activa o desactiva un usuario."""
    conn = get_connection()
    conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if is_active else 0, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    """Elimina un usuario por ID."""
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

# --- Funciones de Caja y Ventas ---
def get_active_session():
    """Obtiene la sesión de caja activa, si existe."""
    conn = get_connection()
    session = conn.execute("SELECT * FROM cash_sessions WHERE status = 'OPEN' ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return session

def open_cash_session(initial_fund, user_id):
    """Inicia una nueva sesión de caja."""
    conn = get_connection()
    conn.execute("INSERT INTO cash_sessions (initial_fund, status, opened_by_user_id) VALUES (?, 'OPEN', ?)", (initial_fund, user_id))
    conn.commit()
    conn.close()

def close_cash_session(session_id, total_sales, user_id):
    """Cierra la sesión de caja activa."""
    conn = get_connection()
    conn.execute("UPDATE cash_sessions SET close_date = CURRENT_TIMESTAMP, total_sales = ?, status = 'CLOSED', closed_by_user_id = ? WHERE id = ?",
                   (total_sales, user_id, session_id))
    conn.commit()
    conn.close()

def get_sales_for_session(session_id):
    """Calcula el total de ventas para una sesión."""
    conn = get_connection()
    total = conn.execute("SELECT SUM(total) FROM transactions WHERE session_id = ?", (session_id,)).fetchone()[0]
    conn.close()
    return total or 0.0

def get_all_purchase_orders():
    """Obtiene un resumen de todas las órdenes de compra con formato de ID robusto."""
    conn = get_connection()
    orders = conn.execute("""
        SELECT po.id, s.nombre as proveedor, po.fecha_pedido, po.estado, po.total, po.numero_oc
        FROM purchase_orders po
        JOIN suppliers s ON po.proveedor_id = s.id
        ORDER BY po.fecha_pedido DESC
    """).fetchall()
    conn.close()
    return orders

def generar_nuevo_numero_oc():
    """Genera un número de orden correlativo con formato OC-AAAA-0001."""
    anio = datetime.now().year
    conn = get_connection()
    # Contamos cuántas órdenes existen para ese año
    count = conn.execute("SELECT COUNT(*) FROM purchase_orders WHERE numero_oc LIKE ?", (f"OC-{anio}-%",)).fetchone()[0]
    conn.close()
    return f"OC-{anio}-{(count + 1):04d}"

def get_purchase_order_details(order_id):
    """Obtiene los detalles (productos) de una orden de compra específica."""
    conn = get_connection()
    details = conn.execute("""
        SELECT pod.*, p.nombre, p.unidad
        FROM purchase_order_details pod
        JOIN products p ON pod.producto_codigo = p.codigo
        WHERE pod.pedido_id = ?
    """, (order_id,)).fetchall()
    conn.close()
    return details

def create_purchase_order(proveedor_nombre, ruc_dni, items, po_data=None):
    """Crea una nueva orden de compra con validaciones estrictas y cálculos automáticos."""
    # VALIDACIONES BÁSICAS
    if not ruc_dni or not ruc_dni.isdigit() or len(ruc_dni) != 11:
        raise ValueError("El RUC debe tener exactamente 11 dígitos numéricos.")
    
    if not items:
        raise ValueError("No se puede crear una orden sin productos.")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Gestionar el Proveedor (y su RUC)
        cursor.execute("SELECT id FROM suppliers WHERE nombre = ?", (proveedor_nombre,))
        supplier = cursor.fetchone()
        if not supplier:
            cursor.execute("INSERT INTO suppliers (nombre, ruc_dni) VALUES (?, ?)", (proveedor_nombre, ruc_dni))
            proveedor_id = cursor.lastrowid
        else:
            proveedor_id = supplier['id']
            # Actualizamos el RUC si ha cambiado o no existía
            cursor.execute("UPDATE suppliers SET ruc_dni = ? WHERE id = ?", (ruc_dni, proveedor_id))

        # 2. Cálculos Financieros
        subtotal = 0.0
        for item in items:
            # item = (codigo, cantidad, precio_unitario)
            cant = float(item[1])
            prec = float(item[2])
            if cant <= 0 or prec <= 0:
                raise ValueError(f"Cantidad y precio deben ser mayores a cero. Error en item: {item[0]}")
            subtotal += (cant * prec)
        
        igv = round(subtotal * 0.18, 2)
        total = round(subtotal + igv, 2)

        # 3. Crear la Orden Principal
        po_data = po_data or {}
        numero_oc = generar_nuevo_numero_oc()
        
        cursor.execute('''
            INSERT INTO purchase_orders (
                proveedor_id, numero_oc, estado, fecha_estimada, condicion_pago, 
                lugar_entrega, responsable_recibe, subtotal, igv, total
            ) VALUES (?, ?, 'PENDIENTE', ?, ?, ?, ?, ?, ?, ?)
        ''', (
            proveedor_id, numero_oc,
            po_data.get('fecha_estimada'), 
            po_data.get('condicion_pago'), 
            po_data.get('lugar_entrega'),
            po_data.get('responsable_recibe'),
            subtotal, igv, total
        ))
        order_id = cursor.lastrowid

        # 4. Insertar Detalles
        for item in items:
            cursor.execute("""
                INSERT INTO purchase_order_details (pedido_id, producto_codigo, cantidad, precio_compra_unitario)
                VALUES (?, ?, ?, ?)
            """, (order_id, item[0], item[1], item[2]))
        
        conn.commit()
        return order_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_purchase_order_by_id(order_id):
    """Obtiene toda la información de una orden de compra."""
    conn = get_connection()
    order = conn.execute("""
        SELECT po.*, s.nombre as proveedor_nombre, s.ruc_dni, s.direccion, s.telefono, s.email
        FROM purchase_orders po
        JOIN suppliers s ON po.proveedor_id = s.id
        WHERE po.id = ?
    """, (order_id,)).fetchone()
    conn.close()
    return order

def update_purchase_order_status(order_id, new_status):
    """Actualiza el estado de una orden de compra."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if new_status == "RECIBIDA":
            # Si se marca como recibida, actualizar stock automáticamente
            receive_purchase_order(order_id)
        else:
            cursor.execute("UPDATE purchase_orders SET estado = ? WHERE id = ?", (new_status, order_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def receive_purchase_order(order_id):
    """Marca una orden como 'RECIBIDO' y actualiza el stock de los productos."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Obtener todos los productos de la orden
        details = conn.execute("SELECT producto_codigo, cantidad FROM purchase_order_details WHERE pedido_id = ?", (order_id,)).fetchall()
        
        # 2. Actualizar el stock para cada producto
        for item in details:
            cursor.execute("UPDATE products SET stock = stock + ? WHERE codigo = ?", (item['cantidad'], item['producto_codigo']))

        # 3. Marcar la orden como recibida y registrar la fecha de llegada
        cursor.execute("UPDATE purchase_orders SET estado = 'RECIBIDO', fecha_llegada = CURRENT_TIMESTAMP WHERE id = ?", (order_id,))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def generar_correlativo_comprobante(tipo):
    """Genera el correlativo siguiente según el tipo (B=Boleta, F=Factura, T=Ticket)."""
    prefijos = {"BOLETA": "B001", "FACTURA": "F001", "TICKET": "T001"}
    prefijo = prefijos.get(tipo.upper(), "T001")
    
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM transactions WHERE tipo_comprobante = ?", (tipo.upper(),)).fetchone()[0]
    conn.close()
    
    return f"{prefijo}-{(count + 1):06d}"

def record_sale(session_id, total, cart_items, user_id, payment_data=None):
    """Registra una venta con datos del cliente, métodos de pago y comprobante."""
    payment_data = payment_data or {}
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Generar correlativo si es necesario
        tipo_comp = payment_data.get('tipo_comprobante', 'TICKET').upper()
        correlativo = generar_correlativo_comprobante(tipo_comp)

        # 1. Registrar la transacción con datos del cliente
        cursor.execute("""
            INSERT INTO transactions (
                session_id, total, user_id, metodo_pago, tipo_comprobante, 
                correlativo, monto_pagado, vuelto, cliente_nombre, cliente_documento
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, total, user_id, 
            payment_data.get('metodo_pago', 'EFECTIVO'),
            tipo_comp, correlativo,
            payment_data.get('monto_pagado', total),
            payment_data.get('vuelto', 0.0),
            payment_data.get('cliente_nombre', 'PÚBLICO EN GENERAL'),
            payment_data.get('cliente_documento', '00000000')
        ))
        transaction_id = cursor.lastrowid
        
        # 2. Detalles y Stock
        for item in cart_items:
            # item = (producto_codigo, quantity, unit_price)
            cursor.execute("INSERT INTO transaction_details (transaction_id, producto_codigo, quantity, unit_price) VALUES (?, ?, ?, ?)", (transaction_id, item[0], item[1], item[2]))
            cursor.execute("UPDATE products SET stock = stock - ? WHERE codigo = ?", (item[1], item[0]))

        # 3. Comisiones
        seller = get_user_by_id(user_id)
        if seller and seller['commission_rate'] > 0:
            cursor.execute("INSERT INTO commissions_earned (user_id, transaction_id, commission_amount) VALUES (?, ?, ?)", (user_id, transaction_id, total * seller['commission_rate']))
            
        conn.commit()
        return transaction_id, correlativo
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_commissions_history(user_id=None, start_date=None, end_date=None):
    """Obtiene el historial de comisiones ganadas, opcionalmente filtrado por usuario y rango de fechas."""
    conn = get_connection()
    query = """
        SELECT
            ce.id AS commission_id,
            ce.date AS commission_date,
            ce.commission_amount,
            u.username AS seller_name,
            t.id AS transaction_id,
            t.total AS transaction_total
        FROM commissions_earned ce
        JOIN users u ON ce.user_id = u.id
        JOIN transactions t ON ce.transaction_id = t.id
        WHERE 1=1
    """
    params = []

    if user_id:
        query += " AND ce.user_id = ?"
        params.append(user_id)
    if start_date:
        query += " AND ce.date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND ce.date <= ?"
        params.append(end_date)
    
    query += " ORDER BY ce.date DESC"
    commissions = conn.execute(query, params).fetchall()
    conn.close()
    return commissions

def get_sales_history(user_id=None, start_date=None, end_date=None):
    """Obtiene el historial de ventas, opcionalmente filtrado por usuario y rango de fechas."""
    conn = get_connection()
    query = """
        SELECT
            t.id AS transaction_id,
            t.date AS transaction_date,
            t.total AS transaction_total,
            u.username AS seller_name
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        WHERE 1=1
    """
    params = []

    if user_id:
        query += " AND t.user_id = ?"
        params.append(user_id)
    if start_date:
        query += " AND t.date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND t.date <= ?"
        params.append(end_date)
    
    query += " ORDER BY t.date DESC"
    sales = conn.execute(query, params).fetchall()
    conn.close()
    return sales

def get_cash_sessions_history(user_id=None, start_date=None, end_date=None):
    """Obtiene el historial de sesiones de caja, opcionalmente filtrado por usuario y rango de fechas."""
    conn = get_connection()
    query = """
        SELECT
            cs.id AS session_id,
            cs.open_date,
            cs.close_date,
            cs.initial_fund,
            cs.total_sales,
            cs.status,
            u_open.username AS opened_by_username,
            u_close.username AS closed_by_username
        FROM cash_sessions cs
        LEFT JOIN users u_open ON cs.opened_by_user_id = u_open.id
        LEFT JOIN users u_close ON cs.closed_by_user_id = u_close.id
        WHERE 1=1
    """
    params = []

    if user_id:
        # Buscar sesiones donde el user_id abrió o cerró la caja
        query += " AND (cs.opened_by_user_id = ? OR cs.closed_by_user_id = ?)"
        params.append(user_id)
        params.append(user_id) # Se usa dos veces para la condición OR
    if start_date:
        query += " AND cs.open_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND cs.open_date <= ?"
        params.append(end_date)
    
    query += " ORDER BY cs.open_date DESC"
    sessions = conn.execute(query, params).fetchall()
    conn.close()
    return sessions

# --- Nuevas Funciones de Gestión ---

# --- MÓDULO DE REPORTES AVANZADOS ---

def get_report_daily_sales():
    """Obtiene el resumen de ventas del día actual por método de pago."""
    conn = get_connection()
    # Fecha de hoy en formato YYYY-MM-DD
    hoy = datetime.now().strftime('%Y-%m-%d')
    
    query = """
        SELECT 
            COUNT(id) as total_transacciones,
            SUM(total) as monto_total,
            SUM(CASE WHEN metodo_pago = 'EFECTIVO' THEN total ELSE 0 END) as efectivo,
            SUM(CASE WHEN metodo_pago = 'TARJETA' THEN total ELSE 0 END) as tarjeta,
            SUM(CASE WHEN metodo_pago NOT IN ('EFECTIVO', 'TARJETA') THEN total ELSE 0 END) as otros
        FROM transactions 
        WHERE date(date) = ?
    """
    res = conn.execute(query, (hoy,)).fetchone()
    conn.close()
    return res

def get_report_sales_by_range(start_date, end_date):
    """Ventas detalladas por rango con cálculo de utilidad/ganancia."""
    conn = get_connection()
    query = """
        SELECT 
            SUM(t.total) as ingresos_brutos,
            SUM(t.total / 1.18 * 0.18) as total_igv,
            SUM(t.total / 1.18) as total_neto,
            SUM((td.unit_price - p.precio_compra) * td.quantity) as ganancia_estimada
        FROM transactions t
        JOIN transaction_details td ON t.id = td.transaction_id
        JOIN products p ON td.producto_codigo = p.codigo
        WHERE date(t.date) BETWEEN ? AND ?
    """
    res = conn.execute(query, (start_date, end_date)).fetchone()
    conn.close()
    return res

def get_report_sales_by_product(start_date, end_date):
    """Lista de productos vendidos con su rentabilidad en un periodo."""
    conn = get_connection()
    query = """
        SELECT 
            p.nombre,
            SUM(td.quantity) as cant_vendida,
            SUM(td.unit_price * td.quantity) as total_generado,
            SUM((td.unit_price - p.precio_compra) * td.quantity) as margen_ganancia
        FROM transaction_details td
        JOIN products p ON td.producto_codigo = p.codigo
        JOIN transactions t ON td.transaction_id = t.id
        WHERE date(t.date) BETWEEN ? AND ?
        GROUP BY p.codigo
        ORDER BY total_generado DESC
    """
    res = conn.execute(query, (start_date, end_date)).fetchall()
    conn.close()
    return res

def get_report_top_products(limit=10):
    """Obtiene los 10 productos más vendidos por cantidad."""
    conn = get_connection()
    query = """
        SELECT p.nombre, SUM(td.quantity) as total_qty
        FROM transaction_details td
        JOIN products p ON td.producto_codigo = p.codigo
        GROUP BY p.codigo
        ORDER BY total_qty DESC
        LIMIT ?
    """
    res = conn.execute(query, (limit,)).fetchall()
    conn.close()
    return res

def get_report_low_stock():
    """Productos que están por debajo de su stock mínimo."""
    conn = get_connection()
    query = """
        SELECT codigo, nombre, stock, stock_minimo, (stock_minimo - stock) as faltante
        FROM products 
        WHERE stock <= stock_minimo
        ORDER BY stock ASC
    """
    res = conn.execute(query).fetchall()
    conn.close()
    return res

def get_report_kardex():
    """Reporte de movimientos consolidado con ID de referencia."""
    conn = get_connection()
    query = """
        SELECT t.id as ref_id, t.date, 'SALIDA (VENTA)' as tipo, td.producto_codigo, td.quantity as cant, td.unit_price as precio
        FROM transaction_details td
        JOIN transactions t ON td.transaction_id = t.id
        
        UNION ALL
        
        SELECT po.id as ref_id, po.fecha_pedido as date, 'ENTRADA (COMPRA)' as tipo, pod.producto_codigo, pod.cantidad as cant, pod.precio_compra_unitario as precio
        FROM purchase_order_details pod
        JOIN purchase_orders po ON pod.pedido_id = po.id
        
        ORDER BY date DESC
    """
    res = conn.execute(query).fetchall()
    conn.close()
    return res

def buscar_cliente_local(documento):
    """Busca un cliente en la tabla dedicada de clientes."""
    conn = get_connection()
    try:
        res = conn.execute("SELECT nombre, direccion, telefono, email FROM customers WHERE documento = ?", (documento,)).fetchone()
        conn.close()
        return dict(res) if res else None
    except Exception:
        conn.close()
        return None

def get_all_customers(search_term=""):
    """Devuelve la lista de clientes, opcionalmente filtrada."""
    conn = get_connection()
    try:
        if search_term:
            query = "SELECT * FROM customers WHERE nombre LIKE ? OR documento LIKE ? ORDER BY nombre ASC"
            res = conn.execute(query, (f"%{search_term}%", f"%{search_term}%")).fetchall()
        else:
            res = conn.execute("SELECT * FROM customers ORDER BY nombre ASC").fetchall()
        conn.close()
        return res
    except Exception:
        conn.close()
        return []

def delete_customer(documento):
    """Elimina un cliente de la base de datos."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM customers WHERE documento = ?", (documento,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def add_or_update_customer(data):
    """Guarda o actualiza la información completa de un cliente."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO customers (documento, nombre, direccion, telefono, email)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(documento) DO UPDATE SET
                nombre=excluded.nombre,
                direccion=excluded.direccion,
                telefono=excluded.telefono,
                email=excluded.email
        ''', (
            str(data['documento']), 
            str(data['nombre']).upper(), 
            str(data.get('direccion') or '').upper(), 
            str(data.get('telefono') or ''), 
            str(data.get('email') or '').lower()
        ))
        conn.commit()
    except Exception as e:
        print(f"Error al guardar cliente: {e}")
    finally:
        conn.close()

def get_sale_full_details(transaction_id):
    """Obtiene toda la información de una venta, sus items y pago para reconstruir el recibo."""
    conn = get_connection()
    # 1. Datos de cabecera
    sale = conn.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,)).fetchone()
    if not sale:
        conn.close()
        return None, None
    
    # 2. Detalles de productos
    items = conn.execute("""
        SELECT p.codigo, p.nombre, td.quantity, td.unit_price, p.fabricante, p.unidad, p.stock
        FROM transaction_details td
        JOIN products p ON td.producto_codigo = p.codigo
        WHERE td.transaction_id = ?
    """, (transaction_id,)).fetchall()
    
    conn.close()
    return sale, items

def update_sale(transaction_id, total, cart_items, payment_data):
    """Actualiza una venta existente, revierte stock anterior y aplica el nuevo."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. REVERTIR STOCK ANTERIOR
        old_items = cursor.execute("SELECT producto_codigo, quantity FROM transaction_details WHERE transaction_id = ?", (transaction_id,)).fetchall()
        for item in old_items:
            cursor.execute("UPDATE products SET stock = stock + ? WHERE codigo = ?", (item['quantity'], item['producto_codigo']))
        
        # 2. LIMPIAR DETALLES ANTERIORES
        cursor.execute("DELETE FROM transaction_details WHERE transaction_id = ?", (transaction_id,))

        # 3. ACTUALIZAR CABECERA DE LA TRANSACCIÓN
        cursor.execute("""
            UPDATE transactions 
            SET total = ?, metodo_pago = ?, tipo_comprobante = ?, 
                monto_pagado = ?, vuelto = ?, cliente_nombre = ?, cliente_documento = ?
            WHERE id = ?
        """, (
            total, payment_data['metodo_pago'], payment_data['tipo_comprobante'],
            payment_data['monto_pagado'], payment_data['vuelto'],
            payment_data['cliente_nombre'], payment_data['cliente_documento'],
            transaction_id
        ))

        # 4. INSERTAR NUEVOS DETALLES Y DESCONTAR NUEVO STOCK
        for item in cart_items:
            # item = (producto_codigo, quantity, unit_price)
            cursor.execute("INSERT INTO transaction_details (transaction_id, producto_codigo, quantity, unit_price) VALUES (?, ?, ?, ?)", (transaction_id, item[0], item[1], item[2]))
            cursor.execute("UPDATE products SET stock = stock - ? WHERE codigo = ?", (item[1], item[0]))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_report_sales_by_seller():
    """Ventas totales acumuladas por cada usuario/vendedor."""
    conn = get_connection()
    query = """
        SELECT u.username, COUNT(t.id) as num_ventas, SUM(t.total) as total_vendido
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        GROUP BY u.id
        ORDER BY total_vendido DESC
    """
    res = conn.execute(query).fetchall()
    conn.close()
    return res

def get_product(codigo):
    """Obtiene un producto específico por su código, incluyendo el nombre del proveedor."""
    conn = get_connection()
    # Unir con la tabla de proveedores para obtener el nombre en lugar de solo el ID
    product = conn.execute("""
        SELECT p.*, s.nombre as proveedor_nombre 
        FROM products p 
        LEFT JOIN suppliers s ON p.proveedor_id = s.id 
        WHERE p.codigo = ?
    """, (codigo,)).fetchone()
    conn.close()
    return product

def get_product_by_name(nombre):
    """Obtiene un producto específico por su nombre exacto."""
    conn = get_connection()
    product = conn.execute("""
        SELECT p.*, s.nombre as proveedor_nombre 
        FROM products p 
        LEFT JOIN suppliers s ON p.proveedor_id = s.id 
        WHERE p.nombre = ?
    """, (nombre,)).fetchone()
    conn.close()
    return product

def delete_product(codigo):
    """Elimina un producto de la base de datos."""
    conn = get_connection()
    conn.execute("DELETE FROM products WHERE codigo = ?", (codigo,))
    conn.commit()
    conn.close()

def add_or_update_product(product_data):
    """Añade o actualiza un producto en la base de datos desde el formulario de la UI."""
    conn = get_connection()
    cursor = conn.cursor()

    # Gestionar el proveedor
    proveedor_id = None
    proveedor_nombre = _clean_value(product_data.get('proveedor_nombre'))
    if proveedor_nombre:
        cursor.execute("SELECT id FROM suppliers WHERE nombre = ?", (proveedor_nombre,))
        supplier_row = cursor.fetchone()
        if supplier_row:
            proveedor_id = supplier_row['id']
        else:
            cursor.execute("INSERT INTO suppliers (nombre) VALUES (?)", (proveedor_nombre,))
            proveedor_id = cursor.lastrowid
    
    fecha_ingreso = product_data.get('fecha_ingreso') or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    params = (
        _clean_value(product_data.get('codigo')), 
        _clean_value(product_data.get('nombre')), 
        _clean_value(product_data.get('fabricante')),
        _clean_value(product_data.get('categoria')), 
        _clean_value(product_data.get('descripcion')),
        _clean_value(product_data.get('precio_venta'), 'float'), 
        _clean_value(product_data.get('precio_compra'), 'float'),
        _clean_value(product_data.get('unidad')), 
        _clean_value(product_data.get('stock'), 'int'),
        _clean_value(product_data.get('stock_minimo'), 'int') or 5, 
        proveedor_id, 
        fecha_ingreso
    )
    
    cursor.execute('''
        INSERT OR REPLACE INTO products (
            codigo, nombre, fabricante, categoria, descripcion, precio_venta, 
            precio_compra, unidad, stock, stock_minimo, proveedor_id, fecha_ingreso
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', params)
    
    conn.commit()
    conn.close()

def get_all_products_for_display(search_term: str = "", sort_by: str = "nombre_asc"):
    """
    Obtiene productos para la tabla principal con búsqueda inteligente por palabras.
    """
    conn = get_connection()
    
    sort_map = {
        "nombre_asc": "p.nombre ASC",
        "nombre_desc": "p.nombre DESC",
        "stock_asc": "p.stock ASC",
        "stock_desc": "p.stock DESC",
    }
    order_clause = sort_map.get(sort_by, "p.nombre ASC")

    base_query = f"""
        SELECT 
            p.codigo, p.nombre, p.categoria, p.fabricante, p.descripcion,
            p.precio_venta, p.precio_compra, p.unidad, p.stock, p.stock_minimo,
            p.fecha_ingreso, s.nombre as proveedor,
            (p.stock * p.precio_compra) as importe_inventario
        FROM products p
        LEFT JOIN suppliers s ON p.proveedor_id = s.id
    """
    
    params = []
    if search_term:
        # Dividimos el término en palabras para una búsqueda más flexible
        words = search_term.split()
        conditions = []
        for word in words:
            # Cada palabra debe estar presente en nombre, código o descripción
            conditions.append("(p.nombre LIKE ? OR p.codigo LIKE ? OR p.descripcion LIKE ?)")
            params.extend([f"%{word}%", f"%{word}%", f"%{word}%"])
        
        base_query += " WHERE " + " AND ".join(conditions)
    
    base_query += f" ORDER BY {order_clause}"
    
    products = conn.execute(base_query, params).fetchall()
    conn.close()
    return products

def add_product_from_import(product_data):
    """Añade o actualiza un producto desde la importación de Excel."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Asegurar que el proveedor exista y obtener su ID
    proveedor_id = None
    if product_data.get('proveedor'):
        proveedor_id = add_supplier(product_data['proveedor'])

    # Construir la tupla de datos en el orden correcto
    data_tuple = (
        product_data.get('Codigo'),
        product_data.get('NOMBRE'),
        product_data.get('FABRICANTE'),
        product_data.get('categoria'),
        product_data.get('DESCRIPCIÓN'),
        float(product_data.get('P.Venta articulo', 0.0)),
        float(product_data.get('Precio Compra', 0.0)),
        product_data.get('unidad'),
        int(product_data.get('STOCK EN ALMACEN', 0)),
        int(product_data.get('stock_minimo', 5)), # Valor por defecto
        proveedor_id,
        product_data.get('FECHA INGRESO')
    )

    # Usar INSERT OR REPLACE para añadir o actualizar si el código ya existe
    cursor.execute('''
        INSERT OR REPLACE INTO products (
            codigo, nombre, fabricante, categoria, descripcion, 
            precio_venta, precio_compra, unidad, stock, stock_minimo, proveedor_id, fecha_ingreso
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data_tuple)
    
    conn.commit()
    conn.close()

def _clean_value(value, value_type='str'):
    """Limpia y convierte un valor, manejando errores."""
    if value is None:
        return 0.0 if value_type == 'float' else (0 if value_type == 'int' else "")
    
    if value_type in ['float', 'int']:
        if isinstance(value, (int, float)):
            return value
        
        # Eliminar símbolos de moneda, espacios, comas de miles
        cleaned_str = "".join(filter(lambda char: char in '0123456789.', str(value)))
        try:
            if value_type == 'float':
                return float(cleaned_str)
            else: # int
                return int(float(cleaned_str)) # Convertir a float primero por si hay decimales
        except (ValueError, TypeError):
            return 0.0 if value_type == 'float' else 0
    
    return str(value)

def add_product_from_flexible_import(product_data):
    """
    Prepara un diccionario de datos de producto para ser insertado en la base de datos.
    No realiza la conexión, solo prepara los datos.
    """
    fecha_ingreso = product_data.get('fecha_ingreso')
    if fecha_ingreso:
        if isinstance(fecha_ingreso, (datetime, sqlite3.Date)):
            fecha_ingreso = fecha_ingreso.strftime("%Y-%m-%d %H:%M:%S")
        else:
            try:
                fecha_ingreso = datetime.strptime(str(fecha_ingreso).split(" ")[0], "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                fecha_ingreso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        fecha_ingreso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "codigo": _clean_value(product_data.get('codigo')),
        "nombre": _clean_value(product_data.get('nombre')),
        "fabricante": _clean_value(product_data.get('fabricante')),
        "categoria": _clean_value(product_data.get('categoria')),
        "descripcion": _clean_value(product_data.get('descripcion')),
        "precio_venta": _clean_value(product_data.get('precio_venta'), 'float'),
        "precio_compra": _clean_value(product_data.get('precio_compra'), 'float'),
        "unidad": _clean_value(product_data.get('unidad')),
        "stock": _clean_value(product_data.get('stock'), 'int'),
        "stock_minimo": _clean_value(product_data.get('stock_minimo'), 'int') or 5,
        "proveedor_nombre": _clean_value(product_data.get('proveedor_nombre')),
        "fecha_ingreso": fecha_ingreso
    }

def bulk_add_products(products):
    """
    Añade o actualiza una lista de productos en una única transacción para mayor eficiencia.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Cache para proveedores para no consultar la BD en cada fila
    supplier_cache = {}

    try:
        for p_data in products:
            proveedor_id = None
            proveedor_nombre = p_data.get('proveedor_nombre')
            
            if proveedor_nombre:
                if proveedor_nombre in supplier_cache:
                    proveedor_id = supplier_cache[proveedor_nombre]
                else:
                    cursor.execute("SELECT id FROM suppliers WHERE nombre = ?", (proveedor_nombre,))
                    supplier_row = cursor.fetchone()
                    if supplier_row:
                        proveedor_id = supplier_row['id']
                    else:
                        cursor.execute("INSERT INTO suppliers (nombre) VALUES (?)", (proveedor_nombre,))
                        proveedor_id = cursor.lastrowid
                    supplier_cache[proveedor_nombre] = proveedor_id

            params = (
                p_data['codigo'], p_data['nombre'], p_data['fabricante'], p_data['categoria'], 
                p_data['descripcion'], p_data['precio_venta'], p_data['precio_compra'], 
                p_data['unidad'], p_data['stock'], p_data['stock_minimo'], 
                proveedor_id, p_data['fecha_ingreso']
            )

            cursor.execute('''
                INSERT OR REPLACE INTO products (
                    codigo, nombre, fabricante, categoria, descripcion, 
                    precio_venta, precio_compra, unidad, stock, stock_minimo, proveedor_id, fecha_ingreso
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', params)
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e # Re-lanza la excepción para que la UI la capture
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
