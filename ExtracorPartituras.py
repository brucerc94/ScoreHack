import os
import cv2
import subprocess
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim
from fpdf import FPDF
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from matplotlib.widgets import Button
import matplotlib.pyplot as plt
import threading
from tkinter import ttk
import tempfile
import shutil


# === CONFIGURACIÓN ===
FRAME_DIR = 'frames'
PARTITURA_DIR = 'partituras'
FRAME_INTERVAL = 1  # segundos

def verificar_permisos():
    """Verifica que el programa tenga permisos de escritura en el directorio actual"""
    try:
        # Intentar crear un archivo de prueba
        test_file = "test_permisos.tmp"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        return True
    except PermissionError:
        return False
    except Exception:
        return False

def crear_directorios_trabajo():
    """Crea directorios de trabajo con permisos garantizados"""
    try:
        # Usar directorio temporal del sistema para evitar problemas de permisos
        base_dir = tempfile.mkdtemp(prefix="extractor_partituras_")
        
        # Crear subdirectorios
        frames_dir = os.path.join(base_dir, 'frames')
        partituras_dir = os.path.join(base_dir, 'partituras')
        
        os.makedirs(frames_dir, exist_ok=True)
        os.makedirs(partituras_dir, exist_ok=True)
        
        return base_dir, frames_dir, partituras_dir
    except Exception as e:
        print(f"❌ Error creando directorios de trabajo: {e}")
        # Fallback a directorio actual
        os.makedirs(FRAME_DIR, exist_ok=True)
        os.makedirs(PARTITURA_DIR, exist_ok=True)
        return None, FRAME_DIR, PARTITURA_DIR

# === 1. DESCARGAR VIDEO DE YOUTUBE CON yt-dlp ===
def descargar_video(url, filename):
    print("⏳ Descargando video con yt-dlp...")
    try:
        # Crear un directorio temporal con permisos garantizados
        temp_dir = tempfile.mkdtemp(prefix="extractor_")
        temp_filename = os.path.join(temp_dir, "video.mp4")
        
        # Descargar en el directorio temporal
        result = subprocess.run([
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]",
            "-o", temp_filename,
            url
        ], check=True, capture_output=True, text=True)
        
        # Mover el archivo descargado al directorio actual
        if os.path.exists(temp_filename):
            shutil.move(temp_filename, filename)
            print("✅ Video descargado correctamente.")
        else:
            # Si no se pudo mover, usar directamente el archivo temporal
            shutil.copy2(temp_filename, filename)
            print("✅ Video descargado correctamente (copia).")
        
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al descargar el video: {e}")
        print(f"Salida de error: {e.stderr}")
        raise
    except PermissionError as e:
        print(f"❌ Error de permisos: {e}")
        print("💡 Intenta ejecutar el programa como administrador o en un directorio con permisos de escritura")
        raise
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        raise

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
def eliminar_duplicados(input_dir: str) -> list[str]:
    """
    Elimina imágenes duplicadas en el directorio dado usando SSIM.
    Devuelve una lista de rutas a imágenes únicas.
    """
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
        # Calcular la similitud estructural (SSIM)
        similarity, *_ = ssim(prev, img, full=True)
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
    # Verificar permisos antes de iniciar
    if not verificar_permisos():
        messagebox.showwarning(
            "Advertencia de Permisos", 
            "⚠️ No tienes permisos de escritura en este directorio.\n\n"
            "💡 Soluciones:\n"
            "• Ejecuta el programa como administrador\n"
            "• Mueve el programa a un directorio con permisos\n"
            "• Usa el escritorio o documentos\n\n"
            "El programa intentará usar directorios temporales del sistema."
        )
    
    class ProcesoPartitura:
        def __init__(self, ventana, barra, mensajes, canvas, slider_top, slider_bot, slider_frame, slider_start, slider_end, btn_continuar, btn_generar):
            self.ventana = ventana
            self.barra = barra
            self.mensajes = mensajes
            self.canvas = canvas
            self.slider_top = slider_top
            self.slider_bot = slider_bot
            self.slider_frame = slider_frame
            self.slider_start = slider_start
            self.slider_end = slider_end
            self.btn_continuar = btn_continuar
            self.btn_generar = btn_generar
            self.frames = []
            self.img_tk = None
            self.top_pixels = 0
            self.bottom_pixels = 0
            self.video_path = None
            self.total_steps = 6
            self.step = 0
            self.frame_index = 0
            self.frame_count = 0

        def log(self, msg):
            self.mensajes.config(state='normal')
            self.mensajes.insert('end', msg + '\n')
            self.mensajes.see('end')
            self.mensajes.config(state='disabled')
            self.ventana.update_idletasks()

        def set_progress(self, step):
            self.barra['value'] = (step / self.total_steps) * 100
            # Cambia color según progreso
            if step == self.total_steps:
                self.barra.configure(style='green.Horizontal.TProgressbar')
            else:
                self.barra.configure(style='blue.Horizontal.TProgressbar')
            self.ventana.update_idletasks()

        def descargar_video(self, url, filename):
            self.log('⏳ Descargando video...')
            self.set_progress(1)
            try:
                # Crear un directorio temporal con permisos garantizados
                temp_dir = tempfile.mkdtemp(prefix="extractor_")
                temp_filename = os.path.join(temp_dir, "video.mp4")
                
                # Descargar en el directorio temporal
                result = subprocess.run([
                    "yt-dlp",
                    "-f", "bestvideo[ext=mp4]",
                    "-o", temp_filename,
                    url
                ], check=True, capture_output=True, text=True)
                
                # Mover el archivo descargado al directorio actual
                if os.path.exists(temp_filename):
                    shutil.move(temp_filename, filename)
                    self.log('✅ Video descargado correctamente.')
                else:
                    # Si no se pudo mover, usar directamente el archivo temporal
                    shutil.copy2(temp_filename, filename)
                    self.log('✅ Video descargado correctamente (copia).')
                
                # Limpiar directorio temporal
                shutil.rmtree(temp_dir, ignore_errors=True)
                
            except subprocess.CalledProcessError as e:
                self.log(f'❌ Error al descargar el video: {e}')
                self.log(f'Salida de error: {e.stderr}')
                raise
            except PermissionError as e:
                self.log(f'❌ Error de permisos: {e}')
                self.log('💡 Intenta ejecutar el programa como administrador o en un directorio con permisos de escritura')
                raise
            except Exception as e:
                self.log(f'❌ Error inesperado: {e}')
                raise

        def extraer_fotogramas(self, video_path, output_dir, intervalo):
            self.log('⏳ Extrayendo fotogramas...')
            self.set_progress(2)
            os.makedirs(output_dir, exist_ok=True)
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                self.log('❌ No se pudo abrir el video. Verifique el archivo.')
                raise Exception('No se pudo abrir el video.')
            fps = cap.get(cv2.CAP_PROP_FPS)
            count = 0
            saved = 0
            self.frames = []
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                if int(count % (fps * intervalo)) == 0:
                    path = os.path.join(output_dir, f'frame_{saved:04d}.jpg')
                    cv2.imwrite(path, frame)
                    self.frames.append(frame)
                    saved += 1
                count += 1
            cap.release()
            self.frame_count = len(self.frames)
            self.log(f'✅ Extraídos {saved} fotogramas.')

        def cargar_frames_para_recorte(self, video_path):
            # Ya se cargaron en extraer_fotogramas
            self.slider_frame.config(to=self.frame_count-1)
            self.slider_start.config(to=self.frame_count-1)
            self.slider_end.config(to=self.frame_count-1)
            self.slider_start.set(0)
            self.slider_end.set(self.frame_count-1)
            self.frame_index = 0
            return True

        def previsualizar_recorte(self):
            import PIL.Image, PIL.ImageTk
            from PIL import ImageDraw
            if not self.frames or self.frames[self.frame_index] is None:
                return
            top = self.slider_top.get()
            bot = self.slider_bot.get()
            self.top_pixels = top
            self.bottom_pixels = bot
            frame = self.frames[self.frame_index]
            im = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = PIL.Image.fromarray(im)
            draw = ImageDraw.Draw(pil_img)
            w, h = pil_img.size
            draw.line([(0, top), (w, top)], fill='red', width=3)
            draw.line([(0, h-bot), (w, h-bot)], fill='red', width=3)
            # Ajustar a tamaño del canvas manteniendo proporción
            canvas_w, canvas_h = 500, 250
            ratio = min(canvas_w / w, canvas_h / h)
            new_w, new_h = int(w * ratio), int(h * ratio)
            pil_img = pil_img.resize((new_w, new_h), PIL.Image.LANCZOS)
            self.img_tk = PIL.ImageTk.PhotoImage(pil_img)
            self.canvas.delete('all')
            # Centrar la imagen en el canvas
            x_offset = (canvas_w - new_w) // 2
            y_offset = (canvas_h - new_h) // 2
            self.canvas.create_image(x_offset, y_offset, anchor='nw', image=self.img_tk)
            label = f'Frame {self.frame_index+1} de {self.frame_count}'
            self.canvas.create_text(canvas_w//2, canvas_h-10, text=label, fill='black', font=('Arial', 12, 'bold'))

        def on_frame_slider(self, event=None):
            self.frame_index = self.slider_frame.get()
            self.previsualizar_recorte()

        def on_range_slider(self, event=None):
            # Asegura que el inicio no sea mayor que el fin
            start = self.slider_start.get()
            end = self.slider_end.get()
            if start > end:
                self.slider_start.set(end)
            self.previsualizar_recorte()

        def recortar_partituras(self, frame_dir, output_dir):
            self.log('⏳ Recortando partituras...')
            self.set_progress(3)
            os.makedirs(output_dir, exist_ok=True)
            start = self.slider_start.get()
            end = self.slider_end.get()
            for i, fname in enumerate(sorted(os.listdir(frame_dir))):
                if i < start or i > end:
                    continue
                img_path = os.path.join(frame_dir, fname)
                img = cv2.imread(img_path)
                if img is None:
                    self.log(f'❌ No se pudo cargar la imagen {fname}.')
                    continue
                height, width = img.shape[:2]
                y1 = self.top_pixels
                y2 = height - self.bottom_pixels
                part = img[y1:y2, :]
                cv2.imwrite(os.path.join(output_dir, fname), part)
            self.log('✅ Recorte de partituras completo.')

        def eliminar_duplicados(self, input_dir):
            self.log('⏳ Eliminando imágenes duplicadas...')
            self.set_progress(4)
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
                similarity, *_ = ssim(prev, img, full=True)
                if similarity < 0.97:
                    unique.append(path)
                    prev = img
            self.log(f'Reducido a {len(unique)} partituras únicas.')
            return unique

        def unir_imagenes_por_hojas(self, img_paths, output_basename, max_por_hoja):
            self.log('⏳ Uniendo imágenes...')
            self.set_progress(5)
            if not img_paths:
                self.log('❌ No hay imágenes para unir.')
                return []
            hojas = [img_paths[i:i + max_por_hoja] for i in range(0, len(img_paths), max_por_hoja)]
            hoja_paths = []
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
                self.log(f'✅ Guardada {nombre_hoja}')
            return hoja_paths

        def crear_pdf(self, img_paths, output_pdf):
            self.log('⏳ Creando PDF...')
            self.set_progress(6)
            pdf = FPDF(unit="pt")
            for img_path in img_paths:
                with Image.open(img_path) as img:
                    width, height = img.size
                    pdf.add_page(format=(width, height))
                    pdf.image(img_path, x=0, y=0, w=width, h=height)
            pdf.output(output_pdf)
            self.log(f'✅ PDF creado: {output_pdf}')

        def limpiar_carpetas(self, video_filename, hoja_paths):
            # Limpiar directorios temporales si existen
            if hasattr(self, 'base_dir') and self.base_dir and os.path.exists(self.base_dir):
                try:
                    shutil.rmtree(self.base_dir, ignore_errors=True)
                    self.log('✅ Directorios temporales eliminados.')
                except Exception as e:
                    self.log(f'⚠️ No se pudieron eliminar directorios temporales: {e}')
            
            # Limpiar directorios del directorio actual si existen
            if os.path.exists(FRAME_DIR):
                for file in os.listdir(FRAME_DIR):
                    try:
                        os.remove(os.path.join(FRAME_DIR, file))
                    except:
                        pass
                try:
                    os.rmdir(FRAME_DIR)
                except:
                    pass
            if os.path.exists(PARTITURA_DIR):
                for file in os.listdir(PARTITURA_DIR):
                    try:
                        os.remove(os.path.join(PARTITURA_DIR, file))
                    except:
                        pass
                try:
                    os.rmdir(PARTITURA_DIR)
                except:
                    pass
            
            # Eliminar video
            if os.path.exists(video_filename):
                try:
                    os.remove(video_filename)
                except:
                    pass
            
            # Eliminar hojas
            for hoja in hoja_paths:
                if os.path.exists(hoja):
                    try:
                        os.remove(hoja)
                        self.log(f'✅ Imagen de hoja eliminada: {hoja}')
                    except:
                        pass
            
            self.log('✅ Limpieza completada.')

        def ejecutar(self, url, nombre_pdf, por_hoja, intervalo, ruta_pdf):
            try:
                self.btn_generar.config(state='disabled')
                self.btn_continuar.config(state='disabled')
                
                # Crear directorios de trabajo temporales
                self.base_dir, self.frames_dir, self.partituras_dir = crear_directorios_trabajo()
                
                video_filename = "video.mp4"
                self.descargar_video(url, video_filename)
                self.extraer_fotogramas(video_filename, self.frames_dir, intervalo)
                self.video_path = video_filename
                if not self.cargar_frames_para_recorte(video_filename):
                    return
                self.previsualizar_recorte()
                self.btn_continuar.config(state='normal')
                self.log('Ajusta los sliders y elige el frame a previsualizar. Luego presiona "Continuar" para seguir.')
            except Exception as e:
                self.log(f'❌ Error: {e}')
                self.btn_generar.config(state='normal')
                return

        def continuar_proceso(self, nombre_pdf, por_hoja, intervalo, ruta_pdf):
            try:
                self.btn_continuar.config(state='disabled')
                self.recortar_partituras(self.frames_dir, self.partituras_dir)
                unicas = self.eliminar_duplicados(self.partituras_dir)
                hojas = self.unir_imagenes_por_hojas(unicas, "partitura", max_por_hoja=por_hoja)
                self.crear_pdf(hojas, ruta_pdf)
                self.log(f'✅ PDF creado con éxito: {ruta_pdf}')
            except Exception as e:
                self.log(f'❌ Error: {e}')
            finally:
                self.limpiar_carpetas("video.mp4", hojas if 'hojas' in locals() else [])
                self.btn_generar.config(state='normal')

    # --- Interfaz principal ---
    ventana = tk.Tk()
    ventana.title("Extractor de video YouTube a PDF by Bruno")
    ventana.geometry("600x820")
    ventana.resizable(False, False)
    style = ttk.Style(ventana)
    style.theme_use('clam')
    style.configure('blue.Horizontal.TProgressbar', thickness=18, troughcolor='#e0e0e0', background='#2196f3')
    style.configure('green.Horizontal.TProgressbar', thickness=18, troughcolor='#e0e0e0', background='#4caf50')

    # --- Layout mejorado ---
    main_frame = tk.Frame(ventana)
    main_frame.pack(padx=10, pady=10, fill='both', expand=True)

    tk.Label(main_frame, text="URL del video de YouTube:").grid(row=0, column=0, sticky="e", pady=3)
    tk.Label(main_frame, text="Nombre del PDF (sin .pdf):").grid(row=1, column=0, sticky="e", pady=3)
    tk.Label(main_frame, text="Partituras por hoja:").grid(row=2, column=0, sticky="e", pady=3)
    tk.Label(main_frame, text="Intervalo entre frames (s):").grid(row=3, column=0, sticky="e", pady=3)

    url_var = tk.StringVar()
    nombre_var = tk.StringVar()
    por_hoja_var = tk.StringVar(value="4")
    intervalo_var = tk.StringVar(value="1")
    ruta_pdf_var = tk.StringVar(value="partitura.pdf")

    tk.Entry(main_frame, textvariable=url_var, width=45).grid(row=0, column=1, columnspan=2, sticky='w', pady=3)
    tk.Entry(main_frame, textvariable=nombre_var, width=25).grid(row=1, column=1, sticky='w', pady=3)
    tk.Entry(main_frame, textvariable=por_hoja_var, width=8).grid(row=2, column=1, sticky='w', pady=3)
    tk.Entry(main_frame, textvariable=intervalo_var, width=8).grid(row=3, column=1, sticky='w', pady=3)

    # Selector de ruta de guardado
    def seleccionar_ruta_pdf():
        ruta = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[('PDF files', '*.pdf')], title='Guardar PDF como...')
        if ruta:
            ruta_pdf_var.set(ruta)

    tk.Label(main_frame, text="Ruta de guardado del PDF:").grid(row=4, column=0, sticky="e", pady=3)
    tk.Entry(main_frame, textvariable=ruta_pdf_var, width=25, state='readonly').grid(row=4, column=1, sticky='w', pady=3)
    tk.Button(main_frame, text="Elegir ruta...", command=seleccionar_ruta_pdf).grid(row=4, column=2, sticky='w', pady=3)

    barra = ttk.Progressbar(main_frame, orient='horizontal', length=500, mode='determinate', style='blue.Horizontal.TProgressbar')
    barra.grid(row=5, column=0, columnspan=3, pady=10)

    mensajes = tk.Text(main_frame, height=5, width=70, state='disabled', bg='#f4f4f4')
    mensajes.grid(row=6, column=0, columnspan=3, padx=5, pady=5)

    tk.Label(main_frame, text="Recorte superior (px):").grid(row=7, column=0, sticky="e", pady=3)
    tk.Label(main_frame, text="Recorte inferior (px):").grid(row=8, column=0, sticky="e", pady=3)
    slider_top = tk.Scale(main_frame, from_=0, to=700, orient='horizontal', length=250)
    slider_top.grid(row=7, column=1, columnspan=2, sticky='w', pady=3)
    slider_bot = tk.Scale(main_frame, from_=0, to=700, orient='horizontal', length=250)
    slider_bot.grid(row=8, column=1, columnspan=2, sticky='w', pady=3)

    tk.Label(main_frame, text="Frame para previsualizar:").grid(row=9, column=0, sticky="e", pady=3)
    slider_frame = tk.Scale(main_frame, from_=0, to=2, orient='horizontal', length=400, showvalue=True)
    slider_frame.grid(row=9, column=1, columnspan=2, sticky='w', pady=3)

    tk.Label(main_frame, text="Rango de frames a procesar:").grid(row=10, column=0, sticky="e", pady=3)
    slider_start = tk.Scale(main_frame, from_=0, to=2, orient='horizontal', length=120, showvalue=True, label='Inicio')
    slider_start.grid(row=10, column=1, sticky='w', pady=3)
    slider_end = tk.Scale(main_frame, from_=0, to=2, orient='horizontal', length=120, showvalue=True, label='Fin')
    slider_end.grid(row=10, column=2, sticky='w', pady=3)

    canvas = tk.Canvas(main_frame, width=500, height=250, bg='white', bd=2, relief='sunken')
    canvas.grid(row=11, column=0, columnspan=3, padx=5, pady=10)

    btn_continuar = tk.Button(main_frame, text="Continuar", state='disabled', width=16)
    btn_continuar.grid(row=12, column=0, pady=10, sticky='e')

    btn_reiniciar = tk.Button(main_frame, text="Reiniciar", width=16)
    btn_reiniciar.grid(row=12, column=1, pady=10)

    btn_generar = tk.Button(main_frame, text="Generar PDF", bg="green", fg="white", width=16)
    btn_generar.grid(row=12, column=2, pady=10, sticky='w')

    proceso = ProcesoPartitura(ventana, barra, mensajes, canvas, slider_top, slider_bot, slider_frame, slider_start, slider_end, btn_continuar, btn_generar)

    def on_slider_change(event=None):
        proceso.previsualizar_recorte()

    slider_top.config(command=on_slider_change)
    slider_bot.config(command=on_slider_change)
    slider_frame.config(command=proceso.on_frame_slider)
    slider_start.config(command=proceso.on_range_slider)
    slider_end.config(command=proceso.on_range_slider)

    def on_generar():
        proceso.btn_generar.config(state='disabled')
        proceso.btn_continuar.config(state='disabled')
        threading.Thread(target=lambda: proceso.ejecutar(
            url_var.get().strip(),
            nombre_var.get().strip(),
            int(por_hoja_var.get()),
            int(intervalo_var.get()),
            ruta_pdf_var.get().strip()
        )).start()

    def on_continuar():
        proceso.btn_continuar.config(state='disabled')
        threading.Thread(target=lambda: proceso.continuar_proceso(
            nombre_var.get().strip(),
            int(por_hoja_var.get()),
            int(intervalo_var.get()),
            ruta_pdf_var.get().strip()
        )).start()

    def on_reiniciar():
        proceso.btn_continuar.config(state='disabled')
        proceso.btn_generar.config(state='disabled')
        slider_top.config(state='normal')
        slider_bot.config(state='normal')
        slider_frame.config(state='normal')
        slider_start.config(state='normal')
        slider_end.config(state='normal')
        proceso.frames = []
        proceso.img_tk = None
        proceso.top_pixels = 0
        proceso.bottom_pixels = 0
        proceso.video_path = None
        proceso.step = 0
        proceso.frame_index = 0
        proceso.frame_count = 0
        proceso.slider_frame.config(state='normal')
        proceso.slider_start.config(state='normal')
        proceso.slider_end.config(state='normal')
        proceso.slider_start.set(0)
        proceso.slider_end.set(0)
        proceso.canvas.delete('all')
        proceso.log('✅ Proceso reiniciado.')

    btn_generar.config(command=on_generar)
    btn_continuar.config(command=on_continuar)
    btn_reiniciar.config(command=on_reiniciar)

    ventana.mainloop()

# === EJECUCIÓN ===
if __name__ == '__main__':
    print("🎵 Extractor de Partituras de YouTube")
    print("=====================================")
    print("💡 Si tienes problemas de permisos, usa:")
    print("   - run_as_admin.bat (Windows)")
    print("   - run_as_admin.ps1 (PowerShell)")
    print("   - Ver SOLUCION_PERMISOS.md para más detalles")
    print()
    
    interfaz_grafica() 
