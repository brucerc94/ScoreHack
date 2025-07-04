# Extractor de Partituras de YouTube a PDF

Este proyecto permite descargar videos de YouTube, extraer partituras desde los fotogramas y generar un PDF listo para imprimir.

## Requisitos
- Python 3.8+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (se instala automáticamente)

## Instalación

1. Clona el repositorio o descarga los archivos.
2. Crea un entorno virtual e instala las dependencias:

```bash
python -m venv venv
venv\Scripts\activate  # En Windows
# o
source venv/bin/activate  # En Linux/Mac
pip install --upgrade pip
pip install -r requirements.txt
```

## Uso

1. Ejecuta el script principal:

```bash
python ExtracorPartituras.py
```

2. Ingresa la URL del video de YouTube, el nombre del PDF y los parámetros solicitados en la interfaz gráfica.

3. El PDF generado estará en la misma carpeta.

## Notas
- El script limpia automáticamente los archivos temporales tras la generación del PDF.
- Puedes ajustar el umbral de similitud en la función `eliminar_duplicados` si necesitas mayor o menor sensibilidad.

---

¡Disfruta digitalizando tus partituras! 