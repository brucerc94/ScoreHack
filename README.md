# Extractor de Partituras

Aplicación modular para capturar partituras mostradas en videos de YouTube o videos locales y exportarlas a PDF.

## Interfaz

La aplicación usa **Qt 6 + QML** para una interfaz fluida y moderna. PySide6 es el binding oficial de Qt para Python; la versión fijada es 6.11.2. La interfaz incluye selección de fuente, arrastrar y soltar video local, vista previa, sliders de recorte/rango y exportación.

## Qué hace

- Acepta enlaces de YouTube.
- Permite seleccionar un video local.
- Extrae fotogramas cada N segundos sin cargar todos los frames en memoria.
- Corrige automáticamente pequeños desplazamientos de cámara o de la partitura usando como referencia únicamente la zona de recorte seleccionada.
- Permite previsualizar un frame y ajustar recorte superior e inferior.
- Permite definir el rango de frames a procesar.
- Permite abrir una vista previa temporal del PDF antes de guardarlo.
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
4. Ajusta recorte, frame de vista previa y rango. La corrección de movimiento usa ese recorte como región de seguimiento cuando generas el PDF.
5. Pulsa **Vista previa** para generar una copia temporal y abrirla con el visor PDF predeterminado, o **Generar PDF** para guardarlo definitivamente.
5. Define cuántas partituras deben caber por página.
6. Pulsa **Generar PDF** y elige dónde guardarlo.

## Nota técnica

El programa captura la partitura como imagen. No reconoce notas musicales ni convierte la partitura a MusicXML u otro formato vectorial.
