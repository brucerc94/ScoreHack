@echo off
cd /d %~dp0

if not exist venv (
    python -m venv venv
)

if not exist venv\Scripts\activate.bat (
    echo ERROR: No se pudo crear el entorno virtual correctamente.
    echo Verifica tu instalación de Python y permisos de carpeta.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

REM Crear pyproject.toml si no existe
if not exist pyproject.toml (
    echo [build-system] > pyproject.toml
    echo requires = ["setuptools", "wheel"] >> pyproject.toml
    echo build-backend = "setuptools.build_meta" >> pyproject.toml
)

REM Ejecutar el script de build
python setup.py

pause 