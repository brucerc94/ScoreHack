# Extractor de Partituras

Aplicación modular para capturar partituras mostradas en videos de YouTube o videos locales y exportarlas a PDF.

## Qué hace

- Acepta enlaces de YouTube.
- Permite seleccionar un video local.
- Extrae fotogramas cada N segundos sin cargar todos los frames en memoria.
- Permite previsualizar un frame y ajustar recorte superior e inferior.
- Permite definir el rango de frames a procesar.
- Elimina frames consecutivos visualmente repetidos mediante SSIM.
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
│   ├── models.py
│   ├── pdf_exporter.py
│   ├── pipeline.py
│   └── workspace.py
├── ui/
│   └── main_window.py
└── main.py
```

La interfaz no contiene la lógica de procesamiento. El núcleo no conoce Tkinter y puede probarse de forma independiente.

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

Genera `dist\\ExtractorPartituras.exe`. `yt-dlp` y CustomTkinter se incluyen en el empaquetado.

## Pruebas

```bash
python -m pytest
```

## Flujo de uso

1. Selecciona **YouTube** o **Video local**.
2. Pega la URL o pulsa **Subir video**.
3. Pulsa **Analizar video**.
4. Ajusta recorte, frame de vista previa y rango.
5. Define cuántas partituras deben caber por página.
6. Pulsa **Generar PDF** y elige dónde guardarlo.

## Nota técnica

El programa captura la partitura como imagen. No reconoce notas musicales ni convierte la partitura a MusicXML u otro formato vectorial.
