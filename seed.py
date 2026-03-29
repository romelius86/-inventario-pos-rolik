import database

# Inicializar DB si no existe
database.init_db()

# Añadir algunos productos de prueba si la tabla está vacía
products = database.get_all_products()
if not products:
    database.add_product("Coca Cola 500ml", 50, 1.50, 0.80)
    database.add_product("Pan de Caja", 20, 2.50, 1.20)
    database.add_product("Leche 1L", 30, 1.80, 1.10)
    database.add_product("Arroz 1kg", 100, 1.20, 0.70)
    print("Datos de prueba añadidos.")
else:
    print("La base de datos ya tiene información.")
