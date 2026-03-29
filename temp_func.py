def add_or_update_product(product_data):
    """Añade o actualiza un producto, asegurando que las unidades asociadas no se borren."""
    conn = get_connection()
    cursor = conn.cursor()

    codigo = _clean_value(product_data.get('codigo'))
    unidad = _clean_value(product_data.get('unidad'))
    factor_base = get_unit_factor(unidad)
    
    # Convertimos el stock ingresado a unidades reales
    stock_ingresado = _clean_value(product_data.get('stock_actual') or product_data.get('stock'), 'float')
    stock_real = stock_ingresado * factor_base
    
    nuevo_precio_venta = _clean_value(product_data.get('precio_venta'), 'float')
    
    # 1. Verificar si existe
    cursor.execute("SELECT precio_venta, fecha_actualizacion_precio FROM products WHERE codigo = ?", (codigo,))
    row = cursor.fetchone()
    
    exists = row is not None
    fecha_precio = None
    if exists:
        precio_actual = row['precio_venta']
        fecha_precio = row['fecha_actualizacion_precio']
        if precio_actual != nuevo_precio_venta or not fecha_precio:
            fecha_precio = get_lima_time()
    else:
        fecha_precio = get_lima_time()

    # 2. Gestionar Proveedor
    proveedor_id = product_data.get('proveedor_id')
    if not proveedor_id:
        proveedor_nombre = _clean_value(product_data.get('proveedor_nombre'))
        if proveedor_nombre:
            cursor.execute("SELECT id FROM suppliers WHERE nombre = ?", (proveedor_nombre,))
            supplier_row = cursor.fetchone()
            if supplier_row:
                proveedor_id = supplier_row['id']
            else:
                cursor.execute("INSERT INTO suppliers (nombre) VALUES (?)", (proveedor_nombre,))
                proveedor_id = cursor.lastrowid
    
    if exists:
        # ACTUALIZACIÓN (Usamos UPDATE para proteger las llaves foráneas ON DELETE CASCADE)
        cursor.execute('''
            UPDATE products SET 
                nombre=?, fabricante=?, categoria=?, descripcion=?, precio_venta=?, 
                precio_compra=?, unidad=?, stock=?, stock_actual=?, stock_minimo=?, 
                proveedor_id=?, fecha_actualizacion_precio=?
            WHERE codigo=?
        ''', (
            _clean_value(product_data.get('nombre')), 
            _clean_value(product_data.get('fabricante')),
            _clean_value(product_data.get('categoria')), 
            _clean_value(product_data.get('descripcion')),
            nuevo_precio_venta, 
            _clean_value(product_data.get('precio_compra'), 'float'),
            unidad, 
            stock_real,
            stock_real,
            _clean_value(product_data.get('stock_minimo'), 'int') or 5, 
            proveedor_id, 
            fecha_precio,
            codigo
        ))
    else:
        # INSERCIÓN
        fecha_ingreso = product_data.get('fecha_ingreso') or get_lima_time()
        cursor.execute('''
            INSERT INTO products (
                codigo, nombre, fabricante, categoria, descripcion, precio_venta, 
                precio_compra, unidad, stock, stock_actual, stock_minimo, proveedor_id, 
                fecha_ingreso, fecha_actualizacion_precio
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            codigo, 
            _clean_value(product_data.get('nombre')), 
            _clean_value(product_data.get('fabricante')),
            _clean_value(product_data.get('categoria')), 
            _clean_value(product_data.get('descripcion')),
            nuevo_precio_venta, 
            _clean_value(product_data.get('precio_compra'), 'float'),
            unidad, 
            stock_real,
            stock_real,
            _clean_value(product_data.get('stock_minimo'), 'int') or 5, 
            proveedor_id, 
            fecha_ingreso,
            fecha_precio
        ))
    
    conn.commit()
    conn.close()
