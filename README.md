# Extractor de Partituras

Aplicación modular para capturar partituras mostradas en videos de YouTube o videos locales y exportarlas a PDF.

## Interfaz

La aplicación usa **Qt 6 + QML** para una interfaz fluida y moderna. PySide6 es el binding oficial de Qt para Python; la versión fijada es 6.11.2. La interfaz incluye selección de fuente, arrastrar y soltar video local, vista previa, sliders de recorte/rango y exportación.

## Qué hace

- Acepta enlaces de YouTube.
- Permite seleccionar un video local.
- Extrae fotogramas cada N segundos sin cargar todos los frames en memoria.
- Corrige automáticamente pequeños desplazamientos de cámara o de la partitura usando como referencia únicamente la zona de recorte seleccionada.
- Elimina opcionalmente resaltadores o cursores de reproducción coloreados que se mueven sobre la partitura.
- Permite previsualizar un frame y ajustar recorte superior e inferior.
- Permite definir el rango de frames a procesar.
- Permite abrir una vista previa temporal del PDF antes de guardarlo.
- Permite seleccionar manualmente frames concretos y ver en la UI la secuencia elegida.
- Permite unir frames horizontalmente para reconstruir partituras con desplazamiento lateral y ver el montaje en vivo antes de exportarlo a A4 apaisado.
- Elimina frames consecutivos visualmente repetidos mediante SSIM después de estabilizarlos.
- Genera páginas A4 con una cantidad configurable de partituras por página.
- Guarda únicamente el PDF final en la ruta elegida.
- No necesita privilegios de administrador.

## Arquitectura

```text
app/
├── core/
│   ├── crop.py
│   ├── deduplicator.py
│   ├── downloader.py
│   ├── frame_extractor.py
│   ├── motion_tracker.py
│   ├── stitcher.py
│   ├── models.py
│   ├── pdf_exporter.py
│   ├── pipeline.py
│   └── workspace.py
├── ui/
│   ├── launcher.py
│   ├── controller.py
│   └── qml/
│       ├── Main.qml
│       └── components/
└── main.py
```

La interfaz está hecha con Qt 6 + QML mediante PySide6. El núcleo no conoce Qt/QML y puede probarse de forma independiente.

## Instalación

Se recomienda Python 3.10+.

```bash
python -m venv venv
venv\\Scripts\\activate
python -m pip install -r requirements.txt
python -m app.main
```

Con `run.bat`, la consola muestra el avance por etapas y porcentajes sin bloquear la interfaz.

## Build de Windows

```bat
build_extractor.bat
```

Genera `dist\\ExtractorPartituras.exe`. PySide6/Qt 6, la interfaz QML y `yt-dlp` se incluyen en el empaquetado.

## Pruebas

```bash
python -m pytest
```

## Flujo de uso

1. Selecciona **YouTube** o **Video local**.
2. Pega la URL o pulsa **Subir video**.
3. Pulsa **Analizar video** para extraer los frames sin fijar todavía la zona de seguimiento.
4. Ajusta recorte, frame de vista previa y rango. La corrección de movimiento usa ese recorte como región de seguimiento cuando generas el PDF y puedes activar **Quitar resaltado móvil**.
5. Selecciona manualmente los frames que quieras conservar. En **Unir horizontal**, selecciona al menos dos frames consecutivos que tengan zona de solape.
6. Define cuántas partituras deben caber por página cuando uses el modo individual.
7. Pulsa **Vista previa** para comprobar el resultado, o **Generar PDF** para guardarlo definitivamente.

## Nota técnica

El programa captura la partitura como imagen. No reconoce notas musicales ni convierte la partitura a MusicXML u otro formato vectorial.
