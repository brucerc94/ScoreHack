@echo off
setlocal
cd /d %~dp0

echo ============================================
echo   Extractor de Partituras - Build
echo ============================================
echo.

if not exist venv\Scripts\python.exe (
    python -m venv venv
    if errorlevel 1 goto :error
)

call venv\Scripts\activate.bat
if errorlevel 1 goto :error

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
if errorlevel 1 goto :error

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

python -m PyInstaller --noconfirm --clean --onefile --windowed --name ExtractorPartituras --icon icon.ico --collect-all PySide6 --collect-all yt_dlp --add-data "app\ui\qml;app\ui\qml" app\main.py
if errorlevel 1 goto :error

echo.
echo BUILD COMPLETADO: dist\ExtractorPartituras.exe
echo.
pause
exit /b 0

:error
echo.
echo ERROR: el build no pudo completarse.
pause
exit /b 1
