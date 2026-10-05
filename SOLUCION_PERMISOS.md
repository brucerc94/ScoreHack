# 🔐 Solución de Problemas de Permisos - Extractor de Partituras

## ❌ Error Común: "Permission denied: 'video.mp4.part'"

Este error ocurre cuando el programa no tiene permisos de escritura en el directorio actual.

## 🛠️ Soluciones Disponibles

### 1. **Ejecutar como Administrador (Recomendado)**

#### Opción A: Usar el archivo batch
```bash
# Hacer doble clic en:
run_as_admin.bat
```

#### Opción B: Usar PowerShell
```powershell
# Hacer clic derecho en:
run_as_admin.ps1
# Seleccionar "Ejecutar con PowerShell"
```

#### Opción C: Manual
1. Hacer clic derecho en `ExtracorPartituras.py`
2. Seleccionar "Ejecutar como administrador"

### 2. **Cambiar Directorio de Trabajo**

Mover el programa a un directorio con permisos garantizados:

- **Escritorio** (`C:\Users\[Usuario]\Desktop`)
- **Documentos** (`C:\Users\[Usuario]\Documents`)
- **Descargas** (`C:\Users\[Usuario]\Downloads`)

### 3. **Verificar Permisos del Directorio**

1. Hacer clic derecho en la carpeta del programa
2. Propiedades → Seguridad
3. Verificar que tu usuario tenga permisos de "Modificar" y "Escribir"

## 🔧 Mejoras Implementadas

### ✅ **Directorios Temporales del Sistema**
- El programa ahora usa directorios temporales del sistema (`%TEMP%`)
- Evita problemas de permisos en el directorio actual
- Limpieza automática al finalizar

### ✅ **Manejo Robusto de Errores**
- Verificación automática de permisos al inicio
- Mensajes informativos sobre problemas de permisos
- Fallback automático a directorios temporales

### ✅ **Verificación de Dependencias**
- Comprobación automática de Python y yt-dlp
- Instalación automática de yt-dlp si es necesario

## 📁 Estructura de Archivos

```
ExtractorPartituras/
├── ExtracorPartituras.py      # Programa principal
├── run_as_admin.bat           # Ejecutar como admin (Windows)
├── run_as_admin.ps1           # Script PowerShell
├── build_extractor.bat        # Compilador
├── requirements.txt            # Dependencias Python
└── SOLUCION_PERMISOS.md       # Este archivo
```

## 🚀 Uso Recomendado

1. **Primera vez**: Usar `run_as_admin.bat` o `run_as_admin.ps1`
2. **Uso normal**: Ejecutar directamente si no hay problemas de permisos
3. **Si hay errores**: Volver a usar los scripts de administrador

## ⚠️ Notas Importantes

- **Windows Defender**: Puede bloquear la ejecución. Agregar excepción si es necesario
- **Antivirus**: Algunos antivirus pueden bloquear yt-dlp. Agregar a lista blanca
- **Firewall**: Permitir conexiones salientes para descargas de YouTube

## 🆘 Si Nada Funciona

1. **Reinstalar Python** como administrador
2. **Verificar PATH** de Python en variables de entorno
3. **Ejecutar en modo seguro** temporalmente
4. **Contactar soporte** con logs de error

## 📝 Logs de Error

El programa ahora muestra información detallada sobre errores:
- Salida de yt-dlp
- Errores de permisos específicos
- Sugerencias de solución

---

**💡 Consejo**: Siempre ejecuta el programa desde un directorio con permisos de escritura o usa los scripts de administrador.

