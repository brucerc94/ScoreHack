import os
import cv2
import subprocess
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim
from fpdf import FPDF
import tkinter as tk
from tkinter import simpledialog, messagebox
from matplotlib.widgets import Button
import matplotlib.pyplot as plt


# === CONFIGURACIÓN ===
FRAME_DIR = 'frames'
PARTITURA_DIR = 'partituras'
FRAME_INTERVAL = 1  # segundos

# === 1. DESCARGAR VIDEO DE YOUTUBE CON yt-dlp ===
def descargar_video(url, filename):
    print("⏳ Descargando video con yt-dlp...")
    try:
        subprocess.run([
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]",
            "-o", filename,
            url
        ], check=True)
        print("✅ Video descargado correctamente.")
    except subprocess.CalledProcessError:
        print("❌ Error al descargar el video. Verifique la URL o instalación de yt-dlp.")

# === 2. EXTRAER FOTOGRAMAS ===
def extraer_fotogramas(video_path, output_dir, intervalo):
    print(f"⏳ Extrayendo Fotogramas......")
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("❌ No se pudo abrir el video. Verifique el archivo.")
        return
    fps = cap.get(cv2.CAP_PROP_FPS)
    count = 0
    saved = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if int(count % (fps * intervalo)) == 0:
            path = os.path.join(output_dir, f'frame_{saved:04d}.jpg')
            cv2.imwrite(path, frame)
            saved += 1
        count += 1
    cap.release()
    print(f"✅ Extraídos {saved} fotogramas.")



# === 2.5. PREVIEW DE CORTE ===
def mostrar_preview_recorte_interactivo(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        messagebox.showerror("Error", "No se pudo abrir el video.")
        return None, None

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_top = None
    frame_bottom = None
    confirmed = False

    # Función para manejar confirmación de recorte
    def confirmar_recorte(event):
        nonlocal confirmed
        confirmed = True
        plt.close()

    # Función para cancelar el recorte
    def cancelar_recorte(event):
        nonlocal confirmed
        confirmed = False
        plt.close()

    while True:
        # Pedir valores interactivos
        top_pixels = simpledialog.askinteger("Recorte Superior", "Ingrese los píxeles a recortar arriba:", minvalue=0)
        bottom_pixels = simpledialog.askinteger("Recorte Inferior", "Ingrese los píxeles a recortar abajo:", minvalue=0)

        if top_pixels is None or bottom_pixels is None:
            messagebox.showwarning("Cancelado", "Operación cancelada por el usuario.")
            cap.release()
            return None, None

        # Obtener el primer y último frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame_top = cap.read()
        if not ret:
            continue

        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
        ret, frame_bottom = cap.read()
        if not ret:
            continue

        # Mostrar los frames con líneas de recorte
        fig, ax = plt.subplots(1, 2, figsize=(12, 6))
        fig.subplots_adjust(bottom=0.2)

        # Dibujar líneas de recorte
        for i, (frame, title) in enumerate(zip([frame_top, frame_bottom], ["Primer Frame", "Último Frame"])):
            ax[i].imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            ax[i].axhline(y=top_pixels, color='red', linestyle='--', linewidth=2)
            ax[i].axhline(y=frame.shape[0] - bottom_pixels, color='red', linestyle='--', linewidth=2)
            ax[i].set_title(title)
            ax[i].axis('off')

        # Agregar botones interactivos
        ax_confirm = plt.axes([0.25, 0.05, 0.2, 0.075])
        ax_cancel = plt.axes([0.55, 0.05, 0.2, 0.075])

        btn_confirm = Button(ax_confirm, 'Aceptar')
        btn_cancel = Button(ax_cancel, 'Rechazar')

        btn_confirm.on_clicked(confirmar_recorte)
        btn_cancel.on_clicked(cancelar_recorte)

        plt.show()

        if confirmed:
            cap.release()
            return top_pixels, bottom_pixels
        else:
            messagebox.showinfo("Reintentar", "Por favor, ajuste los valores de recorte.")

    

# === 3. RECORTAR PARTITURAS ===
def recortar_partituras(frame_dir, output_dir, top_pixels=200, bottom_pixels=200):
    """
    Recorta las partituras eliminando un número fijo de píxeles desde la parte superior e inferior.
    - top_pixels: número de píxeles a eliminar desde la parte superior.
    - bottom_pixels: número de píxeles a eliminar desde la parte inferior.
    """

    print(f"⏳ Recortando Partituras......")
    os.makedirs(output_dir, exist_ok=True)
    
    for fname in sorted(os.listdir(frame_dir)):
        img_path = os.path.join(frame_dir, fname)
        img = cv2.imread(img_path)
        
        if img is None:
            print(f"❌ No se pudo cargar la imagen {fname}.")
            continue
        
        height, width = img.shape[:2]
        
        # Calcular los índices de recorte
        y1 = top_pixels
        y2 = height - bottom_pixels
        
        # Recortar la imagen
        part = img[y1:y2, :]
        
        # Guardar la imagen recortada
        cv2.imwrite(os.path.join(output_dir, fname), part)
        

    print("✅ Recorte de partituras completo.")

# === 4. ELIMINAR IMÁGENES DUPLICADAS ===
def eliminar_duplicados(input_dir):
    print(f"⏳ Eliminando Imagenes Duplicadas......")
    files = sorted(os.listdir(input_dir))
    unique = []
    prev = None
    for fname in files:
        path = os.path.join(input_dir, fname)
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if prev is None:
            unique.append(path)
            prev = img
            continue
        similarity = ssim(prev, img)
        if similarity < 0.97:  # Umbral ajustable
            unique.append(path)
            prev = img
    print(f"Reducido a {len(unique)} partituras únicas.")
    return unique

# === 5. UNIR TODAS EN UNA SOLA IMAGEN ===
def unir_imagenes_por_hojas(img_paths, output_basename, max_por_hoja=4):
    if not img_paths:
        print("❌ No hay imágenes para unir.")
        return []

    # Agrupar las imágenes por hojas
    hojas = [img_paths[i:i + max_por_hoja] for i in range(0, len(img_paths), max_por_hoja)]
    hoja_paths = []
    print(f"⏳ Uniendo imagenes......")
    
    for i, grupo in enumerate(hojas):
        imgs = [Image.open(p) for p in grupo]
        w, h = imgs[0].size
        total_height = sum(im.size[1] for im in imgs)
        hoja = Image.new('RGB', (w, total_height))
        y_offset = 0
        for img in imgs:
            hoja.paste(img, (0, y_offset))
            y_offset += img.size[1]
        nombre_hoja = f"{output_basename}_hoja{i+1:02d}.jpg"
        hoja.save(nombre_hoja)
        hoja_paths.append(nombre_hoja)
        print(f"✅ Guardada {nombre_hoja}")
    
    return hoja_paths

# === 6. CREAR PDF ===
def crear_pdf(img_paths, output_pdf):
    print(f"⏳ Creando PDF......")
    pdf = FPDF(unit="pt")  # Usar puntos como unidad
    for img_path in img_paths:
        with Image.open(img_path) as img:
            width, height = img.size  # Obtener el tamaño de la imagen
            pdf.add_page(format=(width, height))  # Ajustar la página al tamaño de la imagen
            pdf.image(img_path, x=0, y=0, w=width, h=height)  # Imagen ocupa toda la página
    pdf.output(output_pdf)
    print(f"✅ PDF creado: {output_pdf}")

## === 7. LIMPIAR CARPETAS Y VIDEOS ===
def limpiar_carpetas(video_filename, hoja_paths):
    if os.path.exists(FRAME_DIR):
        for file in os.listdir(FRAME_DIR):
            os.remove(os.path.join(FRAME_DIR, file))
        os.rmdir(FRAME_DIR)
    if os.path.exists(PARTITURA_DIR):
        for file in os.listdir(PARTITURA_DIR):
            os.remove(os.path.join(PARTITURA_DIR, file))
        os.rmdir(PARTITURA_DIR)
    if os.path.exists(video_filename):
        os.remove(video_filename)
    
    # Eliminar las imágenes de las hojas
    for hoja in hoja_paths:
        if os.path.exists(hoja):
            os.remove(hoja)
            print(f"✅ Imagen de hoja eliminada: {hoja}")
    
    print("✅ Carpetas, video y hojas eliminados.")

# === INTERFAZ GRÁFICA ===
def interfaz_grafica():
    def procesar():
        # Validaciones
        try:
            url = url_var.get().strip()
            nombre_pdf = nombre_var.get().strip()
            por_hoja = int(por_hoja_var.get())
            intervalo = int(intervalo_var.get())

            if not url or not nombre_pdf:
                raise ValueError("Campos vacíos.")
        except Exception as e:
            messagebox.showerror("Error", f"Datos inválidos: {e}")
            return

        ventana.destroy()  # Cerrar la ventana principal

        output_pdf = f"{nombre_pdf}.pdf"
        video_filename = "video.mp4"
        hojas = []  # Inicializar la variable para evitar errores

        try:
            descargar_video(url, video_filename)
            extraer_fotogramas(video_filename, FRAME_DIR, intervalo)
            top, bottom = mostrar_preview_recorte_interactivo(video_filename)
            if top is None or bottom is None:
                return  # Usuario canceló
            recortar_partituras(FRAME_DIR, PARTITURA_DIR, top_pixels=top, bottom_pixels=bottom)

            únicas = eliminar_duplicados(PARTITURA_DIR)
            hojas = unir_imagenes_por_hojas(únicas, "partitura", max_por_hoja=por_hoja)
            crear_pdf(hojas, output_pdf)
            print(f"✅ PDF creado Con Extio: {output_pdf}")
       
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error: {e}")
        finally:
            limpiar_carpetas(video_filename, hojas if hojas else [])


    ventana = tk.Tk()
    ventana.title("Generador de Partituras Youtube a PDF")

    tk.Label(ventana, text="URL del video de YouTube:").grid(row=0, column=0, sticky="e")
    tk.Label(ventana, text="Nombre del PDF (sin .pdf):").grid(row=1, column=0, sticky="e")
    tk.Label(ventana, text="Partituras por hoja:").grid(row=2, column=0, sticky="e")
    tk.Label(ventana, text="Intervalo entre frames (s):").grid(row=3, column=0, sticky="e")

    url_var = tk.StringVar()
    nombre_var = tk.StringVar()
    por_hoja_var = tk.StringVar(value="4")
    intervalo_var = tk.StringVar(value="1")


    tk.Entry(ventana, textvariable=url_var, width=50).grid(row=0, column=1)
    tk.Entry(ventana, textvariable=nombre_var, width=50).grid(row=1, column=1)
    tk.Entry(ventana, textvariable=por_hoja_var, width=10).grid(row=2, column=1)
    tk.Entry(ventana, textvariable=intervalo_var, width=10).grid(row=3, column=1)


    tk.Button(ventana, text="Generar PDF", command=procesar, bg="green", fg="white").grid(row=6, column=0, columnspan=2, pady=10)

    ventana.mainloop()

# === EJECUCIÓN ===
if __name__ == '__main__':
    interfaz_grafica() 
