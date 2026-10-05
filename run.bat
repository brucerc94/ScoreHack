@echo off
setlocal
cd /d %~dp0

echo ============================================
echo   Extractor de Partituras
echo ============================================
echo.

if not exist venv\Scripts\python.exe (
    echo ERROR: No se encontro el entorno virtual.
    echo.
    echo Crea el entorno con:
    echo   python -m venv venv
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: No se pudo activar el entorno virtual.
    pause
    exit /b 1
)

python -m app.main
set "EXIT_CODE=%errorlevel%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo El programa termino con codigo %EXIT_CODE%.
    pause
)

exit /b %EXIT_CODE%
