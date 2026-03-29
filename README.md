# ERP Consola TUI - Sistema de Gestión Moderno para CMD

Este sistema ha sido diseñado siguiendo los principios de alto rendimiento y estabilidad.

## Características Técnicas
- **Interfaz:** TUI (Terminal User Interface) usando `Textual`.
- **Base de Datos:** SQLite (local).
- **Consumo de CPU:** ~0% en reposo.
- **Estabilidad:** Arquitectura asíncrona basada en eventos.

## Módulos
1. **Inventario:** Gestión completa de productos.
2. **Compras:** Entrada de stock rápida.
3. **Punto de Venta (POS):** Optimizado para teclado, incluye ticket de venta.
4. **Caja:** Control de flujo de dinero por sesión.

## Instrucciones para compilar a .exe

Para convertir este proyecto en un único archivo ejecutable portable, ejecuta el siguiente comando en tu terminal:

```bash
pyinstaller --onefile --name "SistemaERP" main.py
```

El archivo ejecutable se generará en la carpeta `dist/`.

---
*Desarrollado con Python y Textual.*
