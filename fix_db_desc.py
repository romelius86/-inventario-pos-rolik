import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "erp_system.db")

def fix():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN descripcion TEXT")
        print("Columna 'descripcion' añadida exitosamente.")
    except sqlite3.OperationalError:
        print("La columna 'descripcion' ya existe.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix()
