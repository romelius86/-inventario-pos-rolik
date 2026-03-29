import database
import os
from datetime import datetime

DB_FILE = "erp_system.db"

def run_tests():
    print("--- INICIANDO TEST DE LA APLICACIÓN ---")

    # Asegurarnos de que no haya una base de datos antigua
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Base de datos antigua '{DB_FILE}' eliminada.")

    # 1. Inicializar la base de datos
    database.init_db()
    print("Paso 1: Base de datos inicializada.")

    # 2. Probar CREAR (Create)
    test_product_1 = {
        "codigo": "TEST-001",
        "nombre": "Producto de Prueba 1",
        "precio_venta": 100.0,
        "stock": 50
    }
    database.add_or_update_product(test_product_1)
    print("Paso 2: Intentando crear producto TEST-001...")

    # 3. Probar LEER (Read)
    retrieved_product = database.get_product("TEST-001")
    assert retrieved_product is not None, "Fallo en LEER: El producto no se encontró después de crearlo."
    assert retrieved_product['nombre'] == "Producto de Prueba 1", "Fallo en LEER: El nombre del producto no coincide."
    print("Paso 3: Producto TEST-001 leído correctamente.")

    # 4. Probar ACTUALIZAR (Update)
    updated_product_data = {
        "codigo": "TEST-001",
        "nombre": "Producto de Prueba Actualizado",
        "precio_venta": 120.5,
        "stock": 45
    }
    database.add_or_update_product(updated_product_data)
    print("Paso 4: Intentando actualizar producto TEST-001...")

    retrieved_updated_product = database.get_product("TEST-001")
    assert retrieved_updated_product['nombre'] == "Producto de Prueba Actualizado", "Fallo en ACTUALIZAR: El nombre no se actualizó."
    assert retrieved_updated_product['precio_venta'] == 120.5, "Fallo en ACTUALIZAR: El precio no se actualizó."
    assert retrieved_updated_product['stock'] == 45, "Fallo en ACTUALIZAR: El stock no se actualizó."
    print("Paso 4: Producto TEST-001 actualizado y verificado correctamente.")

    # 5. Probar ELIMINAR (Delete)
    database.delete_product("TEST-001")
    print("Paso 5: Intentando eliminar producto TEST-001...")

    deleted_product = database.get_product("TEST-001")
    assert deleted_product is None, "Fallo en ELIMINAR: El producto todavía existe después de ser eliminado."
    print("Paso 5: Producto TEST-001 eliminado y verificado correctamente.")

    print("\n--- ¡TODAS LAS PRUEBAS DEL CRUD PASARON CON ÉXITO! ---")
    print("El núcleo de la base de datos es funcional.")

if __name__ == "__main__":
    run_tests()
