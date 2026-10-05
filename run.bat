@echo off
setlocal
cd /d %~dp0

echo ============================================
echo   Extractor de Partituras
echo ============================================
echo.

if not exist venv\Scripts\python.exe (
    echo No se encontro el entorno virtual. Creandolo...
    python -m venv venv
    if errorlevel 1 goto :error
)

call venv\Scripts\activate.bat
if errorlevel 1 goto :error

echo Verificando dependencias...
venv\Scripts\python.exe -c "import PySide6, cv2, PIL, skimage, fpdf, yt_dlp; assert PySide6.__version__ == '6.11.2'" >nul 2>&1
if errorlevel 1 (
    echo Dependencias faltantes. Instalando...
    venv\Scripts\python.exe -m pip install --upgrade pip
    if errorlevel 1 goto :error
    venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 goto :error
)

echo.
echo Iniciando programa...
echo.

venv\Scripts\python.exe -u -m app.main
set "EXIT_CODE=%errorlevel%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo El programa termino con codigo %EXIT_CODE%.
    goto :error_pause
)

exit /b 0

:error
echo.
echo ERROR: No se pudo preparar o iniciar el programa.
:error_pause
pause
exit /b 1
