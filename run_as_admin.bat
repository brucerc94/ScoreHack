@echo off
echo Ejecutando Extractor de Partituras con permisos de administrador...
echo.

REM Verificar si ya se ejecuta como administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Ya se ejecuta como administrador.
    python ExtracorPartituras.py
) else (
    echo Solicitando permisos de administrador...
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d \"%~dp0\" && python ExtracorPartituras.py && pause' -Verb RunAs"
)

pause

