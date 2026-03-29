@echo off
title Generador de ERP Consola
echo ====================================================
echo   PREPARANDO ENTORNO Y GENERANDO ARCHIVO .EXE
echo ====================================================
echo.
echo 1. Instalando librerias necesarias...
py -m pip install textual rich pyinstaller openpyxl
echo.
echo 2. Creando base de datos inicial (si es necesario)...
py seed.py
echo.
echo 3. Compilando el programa usando ERP_Consola.spec (esto puede tardar un minuto)...
py -m PyInstaller ERP_Consola.spec
echo.
echo ====================================================
echo   PROCESO TERMINADO!
echo.
echo   Busca tu programa en la carpeta "dist"
echo   Nombre: ERP_Consola.exe
echo ====================================================
pause
