# Script de PowerShell para ejecutar con permisos de administrador
Write-Host "Extractor de Partituras - Script de PowerShell" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# Verificar si ya se ejecuta como administrador
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Solicitando permisos de administrador..." -ForegroundColor Yellow
    Start-Process powershell.exe "-File", "$PSCommandPath" -Verb RunAs
    exit
}

Write-Host "Ejecutando con permisos de administrador..." -ForegroundColor Green
Write-Host "Directorio actual: $(Get-Location)" -ForegroundColor Cyan

# Verificar que Python esté instalado
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Python no está instalado o no está en el PATH" -ForegroundColor Red
    Write-Host "Instala Python desde: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Verificar que yt-dlp esté instalado
try {
    $ytdlpVersion = yt-dlp --version 2>&1
    Write-Host "yt-dlp encontrado: $ytdlpVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Advertencia: yt-dlp no está instalado" -ForegroundColor Yellow
    Write-Host "Instalando yt-dlp..." -ForegroundColor Cyan
    pip install yt-dlp
}

# Ejecutar el programa principal
Write-Host "Iniciando Extractor de Partituras..." -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

try {
    python ExtracorPartituras.py
} catch {
    Write-Host "❌ Error al ejecutar el programa: $_" -ForegroundColor Red
}

Write-Host "Programa terminado." -ForegroundColor Green
Read-Host "Presiona Enter para salir"

