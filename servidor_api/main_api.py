import sys
import os
import html

# Para poder importar database.py que está en la carpeta superior
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import database

from pydantic import BaseModel

app = FastAPI(title="ERP API de Inventario")

# Inicializar base de datos al arrancar (Asegura que existan las columnas nuevas)
@app.on_event("startup")
def startup_event():
    database.init_db()

# Modelos Pydantic para validar datos de entrada
class LoginRequest(BaseModel):
    username: str
    password: str

class ProductSchema(BaseModel):
    codigo: str
    nombre: str
    fabricante: str | None = None
    categoria: str | None = None
    descripcion: str | None = None
    precio_venta: float
    precio_compra: float | None = 0.0
    unidad: str | None = "UND"
    stock: int | None = 0
    stock_actual: int | None = 0
    stock_minimo: int = 5
    proveedor_nombre: str | None = None
    proveedor_id: int | None = None
    fecha_ingreso: str | None = None
    fecha_actualizacion_precio: str | None = None

class SaleItemSchema(BaseModel):
    producto_codigo: str
    cantidad: int
    precio_unitario: float
    factor: float | None = 1.0
    unidad_nombre: str | None = None

class SaleRequest(BaseModel):
    user_id: int
    session_id: int | None = None
    total: float
    metodo_pago: str
    tipo_comprobante: str
    cliente_nombre: str | None = "PÚBLICO EN GENERAL"
    cliente_documento: str | None = "00000000"
    monto_pagado: float
    vuelto: float
    items: list[SaleItemSchema]

class CustomerSchema(BaseModel):
    id: int | None = None
    documento: str
    nombre: str
    direccion: str | None = ""
    telefono: str | None = ""
    email: str | None = ""

@app.get("/clientes-eliminados")
def listar_clientes_eliminados():
    """Obtiene la lista de clientes en la papelera (últimos 3 días)"""
    try:
        clientes = database.get_deleted_customers()
        return [dict(c) for c in clientes]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/clientes/restaurar/{documento}")
def restaurar_cliente(documento: str):
    """Saca a un cliente de la papelera y lo vuelve a activar"""
    try:
        success = database.restore_customer(documento)
        if not success:
            raise HTTPException(status_code=400, detail="No se pudo restaurar el cliente.")
        return {"success": True, "message": "Cliente restaurado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class UserSchema(BaseModel):
    id: int | None = None
    username: str
    password: str | None = None
    role: str
    is_active: int = 1

class CashMovementSchema(BaseModel):
    user_id: int
    tipo: str  # INGRESO / RETIRO
    monto: float
    descripcion: str

class POItemSchema(BaseModel):
    codigo: str
    cantidad: int
    precio_compra: float

class POSchema(BaseModel):
    proveedor_nombre: str
    ruc_dni: str
    items: list[POItemSchema]
    po_data: dict | None = {}
    fecha_compra: str | None = None # Nueva fecha de compra opcional

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/compras/ordenes")
def listar_compras():
    """Obtiene la lista de todas las órdenes de compra"""
    try:
        orders = database.get_all_purchase_orders()
        return [dict(o) for o in orders]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/compras/ordenes/{id}")
def detalle_compra(id: int):
    """Obtiene los detalles de una orden específica"""
    try:
        order = database.get_purchase_order_by_id(id)
        if not order:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        items = database.get_purchase_order_details(id)
        return {
            "orden": dict(order),
            "items": [dict(i) for i in items]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compras/ordenes")
def crear_compra(req: POSchema):
    """Crea una nueva orden de compra"""
    try:
        # Preparar items en el formato que espera database.py: list de dicts
        items_list = [item.model_dump() for item in req.items]
        database.create_purchase_order(req.proveedor_nombre, req.ruc_dni, items_list, req.po_data)
        return {"success": True, "message": "Orden de compra creada correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/compras/ordenes/{id}/estado")
def cambiar_estado_compra(id: int, estado: str):
    """Actualiza el estado de una orden (RECIBIDA, CANCELADA, etc.)"""
    try:
        if estado == "RECIBIDA":
            database.receive_purchase_order(id)
        else:
            database.update_purchase_order_status(id, estado)
        return {"success": True, "message": f"Estado actualizado a {estado}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/usuarios")
def listar_usuarios():
    """Obtiene todos los usuarios registrados"""
    try:
        conn = database.get_connection()
        res = conn.execute("SELECT id, username, role, is_active FROM users ORDER BY username ASC").fetchall()
        conn.close()
        return [dict(r) for r in res]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/permisos")
def listar_todos_los_permisos():
    """Obtiene todos los permisos disponibles en el sistema"""
    try:
        perms = database.get_all_permissions()
        return [dict(p) for p in perms]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/usuarios/{id}/permisos")
def obtener_permisos_usuario(id: int):
    """Obtiene los nombres de los permisos asignados a un usuario"""
    try:
        # Reutilizamos get_user_permissions que devuelve un set de nombres
        perms = database.get_user_permissions(id)
        # También necesitamos los IDs para el formulario de guardado
        conn = database.get_connection()
        ids = conn.execute("SELECT permission_id FROM user_permissions WHERE user_id = ?", (id,)).fetchall()
        conn.close()
        return {
            "names": list(perms),
            "ids": [r['permission_id'] for r in ids]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/usuarios/{id}/permisos")
def actualizar_permisos_usuario(id: int, perm_ids: list[int]):
    """Actualiza los permisos asignados a un usuario"""
    try:
        database.update_user_permissions(id, perm_ids)
        return {"success": True, "message": "Permisos actualizados correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/usuarios")
def guardar_usuario(user: UserSchema):
    """Crea o actualiza un usuario"""
    try:
        # Si tiene ID, es actualización
        if user.id:
            database.update_user(user.id, user.username, user.password, user.role, user.is_active)
        else:
            # Si es nuevo, el password es obligatorio
            if not user.password:
                raise HTTPException(status_code=400, detail="La contraseña es obligatoria para nuevos usuarios")
            database.add_user(user.username, user.password, user.role)
        return {"success": True, "message": "Usuario guardado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ventas/{id}/ticket")
def obtener_ticket_html(id: int, format: str = "80mm"):
    """Genera el comprobante HTML profesional de ROLIK"""
    try:
        sale_raw, items = database.get_sale_full_details(id)
        if not sale_raw:
            raise HTTPException(status_code=404, detail="Venta no encontrada")
        
        sale = dict(sale_raw)
        width = "280px" if format == "80mm" else "750px"
        
        # Auditoría de anulación para el ticket
        void_watermark = ""
        if sale.get('status') == 'VOIDED':
            conn = database.get_connection()
            user_void = conn.execute("SELECT username FROM users WHERE id = ?", (sale.get('voided_by_user_id'),)).fetchone()
            void_by = user_void['username'] if user_void else "Admin"
            conn.close()
            
            void_watermark = f"""
            <div style="border: 4px solid #ef4444; color: #ef4444; padding: 15px; margin: 15px 0; text-align: center; border-radius: 10px; transform: rotate(-5deg); font-weight: bold;">
                <h1 style="margin: 0; font-size: 24px;">VENTA ANULADA</h1>
                <p style="margin: 5px 0 0 0; font-size: 11px; text-transform: uppercase;">
                    POR: {void_by} | MOTIVO: {sale.get('void_reason', 'No especificado')}
                </p>
            </div>
            """

        html = f"""
        <html>
        <head>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    width: {width}; 
                    font-size: 12px; 
                    padding: 5px; 
                    color: #000; 
                    line-height: 1.2;
                    margin: auto;
                }}
                .header-info {{ text-align: center; margin-bottom: 10px; }}
                .contact-info {{ font-size: 10px; color: #333; }}
                .text-center {{ text-align: center; }}
                .text-right {{ text-align: right; }}
                .border-top {{ border-top: 1px dashed #000; margin-top: 8px; padding-top: 8px; }}
                table.items {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                table.items th {{ text-align: left; border-bottom: 1px solid #000; padding: 3px 0; }}
                table.items td {{ padding: 5px 0; border-bottom: 1px solid #eee; }}
                .total-box {{ font-size: 1.2em; font-weight: bold; margin-top: 15px; text-align: right; border-top: 1px solid #000; padding-top: 5px; }}
                .footer-info {{ font-size: 10px; color: #444; margin-top: 10px; border: 1px solid #eee; padding: 5px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            {void_watermark}
            <div class="header-info">
                <h1 style="margin: 0; font-size: 20px; color: #000;">ROLIK</h1>
                <strong>RUC: 10440809320</strong><br>
                <div class="contact-info">
                    PQ IND. MADERA MZ A LT 26 - KM 15.5 ATE, LIMA<br>
                    Telf: 988352912 / 932326764 | Email: gmromel@live.com
                </div>
            </div>

            <div class="text-center border-top">
                <strong style="font-size: 1.2em;">{sale['tipo_comprobante']} ELECTRÓNICA</strong><br>
                <strong style="font-size: 1.1em;">{sale['correlativo']}</strong><br>
                Fecha: {sale['date']}
            </div>
            
            <div class="border-top">
                <strong>CLIENTE:</strong> {sale['cliente_nombre'] or "PÚBLICO EN GENERAL"}<br>
                <strong>DNI/RUC:</strong> {sale['cliente_documento'] or "00000000"}
            </div>

            <table class="items">
                <thead>
                    <tr>
                        <th>CANT</th>
                        <th>DESCRIPCIÓN</th>
                        <th class="text-right">TOTAL</th>
                    </tr>
                </thead>
                <tbody>
        """
        for item in items:
            sub = item['quantity'] * item['unit_price']
            # Acceso directo por nombre de columna compatible con sqlite3.Row
            u_venta = item['unidad_venta']
            unidad_desc = f"({u_venta})" if u_venta else ""
            html += f"""
                <tr>
                    <td>{item['quantity']}</td>
                    <td>{item['nombre']} <small style="display:block; font-size:9px; color:#555;">{unidad_desc}</small></td>
                    <td class="text-right">{sub:,.2f}</td>
                </tr>
            """
        
        html += f"""
                </tbody>
            </table>

            <div class="total-box">
                TOTAL: S/ {sale['total']:,.2f}
            </div>

            <div class="footer-info">
                <strong>MÉTODO:</strong> {sale['metodo_pago']}<br>
                <strong>PAGÓ CON:</strong> S/ {sale.get('monto_pagado', 0):,.2f}<br>
                <strong>VUELTO:</strong> S/ {sale.get('vuelto', 0):,.2f}
            </div>

            <div class="text-center" style="margin-top: 25px; font-weight: bold;">
                ¡GRACIAS POR SU PREFERENCIA!<br>
                <small>Representación impresa del comprobante electrónico.</small>
            </div>

            <!-- Botones de control (solo visibles en pantalla) -->
            <div style="margin-top: 30px; text-align: center;" class="no-print">
                <button onclick="window.print()" style="padding: 10px 20px; background: #22c55e; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">IMPRIMIR AHORA</button>
                <button onclick="window.close()" style="padding: 10px 20px; background: #64748b; color: white; border: none; border-radius: 5px; cursor: pointer; margin-left: 10px;">CERRAR VENTANA</button>
            </div>

            <style>
                @media print {{
                    .no-print {{ display: none !important; }}
                    body {{ margin: 0.5cm; }}
                }}
            </style>

            <script>
                window.onload = function() {{
                    // Pequeño retraso para asegurar que los estilos y logo carguen
                    setTimeout(() => {{
                        window.print();
                        // No cerramos automáticamente para evitar que se cancele la impresión
                    }}, 800);
                }}
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/caja/abrir")
def abrir_caja(req: dict):
    """Abre una nueva sesión de caja"""
    try:
        initial_fund = float(req.get('fondo_inicial', 0.0))
        user_id = int(req.get('user_id'))
        database.open_cash_session(initial_fund, user_id)
        return {"success": True, "message": "Caja abierta correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/caja/cerrar")
def cerrar_caja(req: dict):
    """Cierra la sesión de caja activa"""
    try:
        session = database.get_active_session()
        if not session:
            raise HTTPException(status_code=404, detail="No hay una sesión abierta")
        
        user_id = int(req.get('user_id'))
        summary = database.get_cash_session_summary(session['id'])
        total_sales = summary['total_general']
        
        database.close_cash_session(session['id'], total_sales, user_id)
        return {"success": True, "message": "Caja cerrada correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/caja/historial")
def historial_cajas():
    """Obtiene el historial de todas las sesiones de caja"""
    try:
        history = database.get_cash_sessions_history()
        return [dict(h) for h in history]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/caja/sesion-activa")
def obtener_caja_activa():
    """Obtiene la sesión de caja abierta"""
    session = database.get_active_session()
    if not session:
        return {"active": False}
    return {"active": True, "session": dict(session)}

@app.get("/caja/resumen")
def obtener_resumen_caja():
    """Obtiene el resumen detallado de la caja actual (Corte X)"""
    session = database.get_active_session()
    if not session:
        raise HTTPException(status_code=404, detail="No hay una sesión de caja abierta")
    
    summary = database.get_cash_session_summary(session['id'])
    return summary

@app.post("/caja/movimiento")
def registrar_movimiento_caja(req: CashMovementSchema):
    """Registra un ingreso o retiro manual de efectivo"""
    session = database.get_active_session()
    if not session:
        raise HTTPException(status_code=404, detail="No hay una sesión de caja abierta")
    
    try:
        database.add_cash_movement(session['id'], req.user_id, req.tipo, req.monto, req.descripcion)
        return {"success": True, "message": "Movimiento registrado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- MÓDULO DE REPORTES ---

@app.get("/reportes/dashboard")
def obtener_dashboard():
    """Resumen rápido para la pantalla principal de reportes"""
    try:
        stats = database.get_dashboard_stats()
        print(f"DEBUG STATS: {stats}") # Log para ver en la consola de Python
        
        low_stock = database.get_report_low_stock()
        top_prod = database.get_report_top_products(5)
        
        resp = {
            "sales_today": stats['sales_today'],
            "methods_today": stats['methods_today'],
            "total_clients": stats['total_clients'],
            "total_products": stats['total_products'],
            "alerta_stock": len(low_stock),
            "top_productos": [dict(p) for p in top_prod]
        }
        print(f"DEBUG RESPONSE: {resp}")
        return resp
    except Exception as e:
        print(f"ERROR DASHBOARD: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reportes/vendedores")
def obtener_reporte_vendedores():
    """Rendimiento de ventas por usuario"""
    res = database.get_report_sales_by_seller()
    return [dict(r) for r in res]

@app.get("/reportes/stock-bajo")
def obtener_reporte_stock_bajo():
    """Productos que necesitan reposición"""
    res = database.get_report_low_stock()
    return [dict(r) for r in res]

@app.get("/reportes/top-productos")
def obtener_top_productos(limit: int = 10):
    """Obtiene los N productos más vendidos"""
    try:
        res = database.get_report_top_products(limit)
        return [dict(r) for r in res]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reportes/kardex")
def obtener_kardex():
    """Obtiene el historial de movimientos de inventario (Kardex)"""
    try:
        res = database.get_report_kardex()
        return [dict(r) for r in res]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reportes/historial-ventas")
def obtener_historial_ventas(inicio: str | None = None, fin: str | None = None):
    """Historial detallado de transacciones (Recibos)"""
    try:
        res = database.get_sales_history(start_date=inicio, end_date=fin)
        
        # Enriquecer con tipo de comprobante y correlativo
        conn = database.get_connection()
        ventas_completas = []
        for v in res:
            v_dict = dict(v)
            extra = conn.execute("SELECT tipo_comprobante, correlativo, cliente_nombre, status FROM transactions WHERE id = ?", (v_dict['transaction_id'],)).fetchone()
            if extra:
                v_dict['comprobante'] = f"{extra['tipo_comprobante']} {extra['correlativo']}"
                v_dict['cliente'] = extra['cliente_nombre'] or "PÚBLICO EN GENERAL"
                v_dict['status'] = extra['status']
            ventas_completas.append(v_dict)
        conn.close()
        return ventas_completas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ventas/{id}/detalles")
def obtener_detalles_venta(id: int):
    """Obtiene toda la información de una venta e items"""
    try:
        sale_raw, items = database.get_sale_full_details(id)
        if not sale_raw:
            raise HTTPException(status_code=404, detail="Venta no encontrada")
        
        sale = dict(sale_raw)
        
        # Auditoría de anulación
        if sale.get('status') == 'VOIDED' and sale.get('voided_by_user_id'):
            conn = database.get_connection()
            user_void = conn.execute("SELECT username FROM users WHERE id = ?", (sale['voided_by_user_id'],)).fetchone()
            if user_void:
                sale['voided_by_username'] = user_void['username']
            conn.close()

        return {
            "venta": sale,
            "items": [dict(i) for i in items]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/ventas/{id}")
def actualizar_venta(id: int, req: SaleRequest):
    """Actualiza una venta existente"""
    try:
        cart_items = [(item.producto_codigo, item.cantidad, item.precio_unitario, item.factor, item.unidad_nombre) for item in req.items]
        payment_data = {
            "metodo_pago": req.metodo_pago,
            "tipo_comprobante": req.tipo_comprobante,
            "cliente_nombre": req.cliente_nombre,
            "cliente_documento": req.cliente_documento,
            "monto_pagado": req.monto_pagado,
            "vuelto": req.vuelto
        }
        database.update_sale(id, req.total, cart_items, payment_data)
        return {"success": True, "message": "Venta actualizada correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ventas")
def registrar_venta(req: SaleRequest):
    """Registra una venta en la base de datos con validación de stock"""
    try:
        # 1. Obtener o crear sesión de caja activa si no viene una
        session = database.get_active_session()
        if not session:
            # Si no hay caja abierta, la abrimos automáticamente por defecto para la web
            database.open_cash_session(0.0, req.user_id)
            session = database.get_active_session()
        
        # 2. Formatear items para la función record_sale
        # record_sale espera una lista de tuplas: (codigo, cantidad, precio, factor, unidad_nombre)
        cart_items = [(item.producto_codigo, item.cantidad, item.precio_unitario, item.factor, item.unidad_nombre) for item in req.items]
        
        # 3. Datos de pago
        payment_data = {
            "metodo_pago": req.metodo_pago,
            "tipo_comprobante": req.tipo_comprobante,
            "cliente_nombre": req.cliente_nombre,
            "cliente_documento": req.cliente_documento,
            "monto_pagado": req.monto_pagado,
            "vuelto": req.vuelto
        }
        
        # 4. Registrar en DB
        trans_id, correlativo = database.record_sale(
            session['id'], req.total, cart_items, req.user_id, payment_data
        )
        
        return {
            "success": True, 
            "transaction_id": trans_id, 
            "correlativo": correlativo,
            "message": "Venta registrada con éxito"
        }
    except ValueError as ve:
        # Errores de validación de stock o existencia se devuelven como 400
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/clientes/{documento}")
def buscar_cliente(documento: str):
    cliente = database.buscar_cliente_local(documento)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@app.get("/clientes-lista")
def listar_todos_los_clientes(search: str = ""):
    """Obtiene la lista de todos los clientes"""
    try:
        clientes = database.get_all_customers(search_term=search)
        return [dict(c) for c in clientes]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/clientes")
def guardar_cliente(cli: CustomerSchema):
    """Crea o actualiza un cliente"""
    try:
        database.add_or_update_customer(cli.model_dump())
        return {"success": True, "message": "Cliente guardado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/clientes/{documento}")
def eliminar_cliente(documento: str):
    """Elimina un cliente por su documento"""
    try:
        database.delete_customer(documento)
        return {"success": True, "message": "Cliente eliminado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/productos/proximo-codigo")
def proximo_codigo():
    """Retorna el siguiente código disponible para un producto"""
    try:
        return {"codigo": database.get_next_product_code()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/productos")
def guardar_producto(prod: ProductSchema):
    """Crea o actualiza un producto"""
    try:
        data = prod.model_dump()
        # Aseguramos compatibilidad: si viene stock_actual pero no stock, copiamos
        if (data.get('stock') is None or data.get('stock') == 0) and data.get('stock_actual') is not None:
            data['stock'] = data['stock_actual']
        
        database.add_or_update_product(data)
        return {"success": True, "message": "Producto guardado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/productos/{codigo}")
def actualizar_producto(codigo: str, product: ProductSchema):
    """Actualiza la información completa de un producto existente."""
    try:
        data = product.model_dump()
        data['codigo'] = codigo # Aseguramos que use el código de la URL
        
        # Aseguramos compatibilidad: si viene stock_actual pero no stock, copiamos
        if (data.get('stock') is None or data.get('stock') == 0) and data.get('stock_actual') is not None:
            data['stock'] = data['stock_actual']
            
        database.add_or_update_product(data)
        return {"success": True, "message": "Producto actualizado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/productos-eliminados")
def listar_productos_eliminados():
    """Obtiene la lista de productos en la papelera (últimos 3 días)"""
    try:
        productos = database.get_deleted_products()
        return [dict(p) for p in productos]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/productos/restaurar/{codigo}")
def restaurar_producto(codigo: str):
    """Saca un producto de la papelera y lo vuelve a activar"""
    try:
        success = database.restore_product(codigo)
        if not success:
            raise HTTPException(status_code=400, detail="No se pudo restaurar el producto.")
        return {"success": True, "message": "Producto restaurado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/productos/{codigo}")
def eliminar_producto(codigo: str):
    """Elimina un producto por su código con manejo de errores de integridad"""
    try:
        database.delete_product(codigo)
        return {"success": True, "message": "Producto eliminado correctamente"}
    except Exception as e:
        error_msg = str(e).lower()
        if "foreign key" in error_msg or "integrityerror" in error_msg:
            raise HTTPException(
                status_code=400, 
                detail="No se puede eliminar el producto porque tiene historial de ventas, compras o movimientos de inventario asociados. Se recomienda dejarlo con stock 0 o cambiar su nombre si ya no lo usará."
            )
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

@app.get("/proveedores-lista-completa")
def listar_proveedores_full():
    """Obtiene la lista de todos los proveedores con sus datos completos"""
    try:
        suppliers = database.get_all_suppliers_full()
        return [dict(s) for s in suppliers]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/proveedores/{id}")
def obtener_proveedor(id: int):
    """Obtiene un proveedor específico por su ID"""
    try:
        supplier = database.get_supplier_by_id(id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        return dict(supplier)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/proveedores/{id}")
def actualizar_proveedor(id: int, data: dict):
    """Actualiza la información de un proveedor"""
    try:
        success = database.update_supplier(id, data)
        if not success:
            raise HTTPException(status_code=400, detail="No se pudo actualizar el proveedor")
        return {"success": True, "message": "Proveedor actualizado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/proveedores-eliminados")
def listar_proveedores_eliminados():
    """Obtiene la lista de proveedores en la papelera"""
    try:
        suppliers = database.get_deleted_suppliers()
        return [dict(s) for s in suppliers]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/proveedores/restaurar/{id}")
def restaurar_proveedor(id: int):
    """Restaura un proveedor de la papelera"""
    try:
        success = database.restore_supplier(id)
        if not success:
            raise HTTPException(status_code=400, detail="No se pudo restaurar el proveedor.")
        return {"success": True, "message": "Proveedor restaurado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/proveedores/{id}")
def eliminar_proveedor(id: int):
    """Elimina un proveedor si no tiene compras asociadas"""
    try:
        database.delete_supplier(id)
        return {"success": True, "message": "Proveedor eliminado correctamente"}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/proveedores-full")
def crear_proveedor(data: dict):
    """Crea un nuevo proveedor con datos completos"""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO suppliers (nombre, ruc_dni, direccion, telefono, email)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data['nombre'].upper(),
            data.get('ruc_dni'),
            data.get('direccion', '').upper(),
            data.get('telefono'),
            data.get('email', '').lower()
        ))
        conn.commit()
        conn.close()
        return {"success": True, "message": "Proveedor creado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/proveedores")
def listar_proveedores():
    try:
        conn = database.get_connection()
        res = conn.execute("SELECT nombre FROM suppliers ORDER BY nombre ASC").fetchall()
        conn.close()
        return [r['nombre'] for r in res]
    except Exception as e:
        return []

@app.get("/proveedores-detalles")
def listar_proveedores_detalles():
    try:
        conn = database.get_connection()
        res = conn.execute("SELECT nombre, ruc_dni FROM suppliers ORDER BY nombre ASC").fetchall()
        conn.close()
        return [dict(r) for r in res]
    except Exception as e:
        return []

@app.post("/login")
def login(req: LoginRequest):
    """Verifica las credenciales del usuario usando la base de datos de escritorio"""
    try:
        user = database.authenticate_user(req.username, req.password)
        if not user:
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos, o usuario inactivo")
        
        # FastAPI no puede serializar un "set", lo convertimos a lista
        user['permissions'] = list(user['permissions'])
        
        return {
            "success": True, 
            "user": user,
            "message": f"Bienvenido {user['username']}"
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/configuracion/{key}")
def obtener_configuracion(key: str):
    """Obtiene un valor de configuración"""
    val = database.get_setting(key)
    return {"key": key, "value": val}

@app.post("/configuracion")
def guardar_configuracion(req: dict):
    """Guarda o actualiza una configuración"""
    try:
        key = req.get('key')
        value = req.get('value')
        if not key: raise HTTPException(status_code=400, detail="Falta la llave")
        database.update_setting(key, value)
        return {"success": True, "message": "Configuración actualizada"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido al Servidor del Inventario ROLIK"}

@app.get("/productos/{codigo}/unidades")
def obtener_unidades_producto(codigo: str):
    """Obtiene las presentaciones adicionales de un producto"""
    try:
        unidades = database.get_product_units(codigo)
        return [dict(u) for u in unidades]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/productos/{codigo}/unidades")
def agregar_unidad_producto(codigo: str, req: dict):
    """Agrega una nueva presentación (ej: Docena) a un producto"""
    try:
        nombre = req.get('nombre_unidad')
        factor = req.get('factor_conversion')
        precio = req.get('precio_venta')
        
        if not all([nombre, factor, precio]):
            raise HTTPException(status_code=400, detail="Faltan datos requeridos")
            
        success = database.add_product_unit(codigo, nombre, factor, precio)
        if not success:
            raise HTTPException(status_code=400, detail="No se pudo agregar la unidad")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/productos/unidades/{id}")
def eliminar_unidad_producto(id: int):
    """Elimina una presentación específica"""
    try:
        database.delete_product_unit(id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/productos")
def listar_productos(search: str = ""):
    """Obtiene los productos desde database.py"""
    try:
        # Reutilizamos tu función actual
        products = database.get_all_products_for_display(search_term=search)
        # Convertimos las filas de sqlite a diccionarios
        return [dict(p) for p in products]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/producto/{codigo}")
def obtener_producto(codigo: str):
    try:
        product = database.get_product(codigo)
        if not product:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return dict(product)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reportes/ventas-rango")
def obtener_ventas_rango(inicio: str, fin: str, metodo_pago: str = None):
    try:
        # Modificamos la llamada para pasar el método de pago si existe
        res = database.get_report_sales_by_range_filtered(inicio, fin, metodo_pago)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reportes/ventas-por-producto")
def obtener_ventas_por_producto(inicio: str, fin: str, metodo_pago: str = None):
    try:
        res = database.get_report_sales_by_product_filtered(inicio, fin, metodo_pago)
        return [dict(r) for r in res]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reportes/ventas-por-categoria")
def obtener_ventas_por_categoria(inicio: str, fin: str, metodo_pago: str = None):
    try:
        res = database.get_report_sales_by_category(inicio, fin, metodo_pago)
        return [dict(r) for r in res]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reportes/ventas-por-categoria/detalles")
def obtener_detalles_categoria(categoria: str, inicio: str, fin: str):
    try:
        res = database.get_report_sales_by_category_details(categoria, inicio, fin)
        return [dict(r) for r in res]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reportes/ventas-por-cliente")
def obtener_ventas_por_cliente(inicio: str, fin: str):
    try:
        res = database.get_report_sales_by_customer(inicio, fin)
        return [dict(r) for r in res]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ventas/{id}/anular")
def anular_venta(id: int, data: dict):
    """Anula una venta verificando permisos de auditoría"""
    user_id = data.get('user_id')
    reason = data.get('reason', 'Sin motivo especificado')
    
    if not user_id:
        raise HTTPException(status_code=400, detail="Se requiere identificación de usuario para anular.")
    
    # Verificación de permisos rigurosa
    user_perms = database.get_user_permissions(user_id)
    if 'sale.void' not in user_perms:
        raise HTTPException(status_code=403, detail="No tiene permisos para anular ventas. Contacte al administrador.")

    success, msg = database.void_sale(id, user_id, reason)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": msg}

@app.get("/productos/similares")
def buscar_similares(nombre: str):
    """Busca productos con nombres parecidos para evitar duplicados"""
    try:
        products = database.get_similar_products(nombre)
        return [dict(p) for p in products]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Iniciamos el servidor en el puerto 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
