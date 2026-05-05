import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from logica.conversion import arreglo_gris_a_imagen_pil, convertir_rgb_a_gris_manual
from logica.filtros_espaciales import aplicar_filtro_manual
from logica.frecuencia import (
    obtener_espectro_con_mascara_visible,
    preparar_transformada_frecuencia,
    reconstruir_desde_diametro,
)
from logica.ruido import agregar_ruido_sal_pimienta_manual


TAMANO_FRECUENCIA = 1024


class VentanaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Procesamiento Digital de Imagenes - Dominios Espacial y Frecuencia")
        self.geometry("1180x760")
        self.minsize(980, 650)
        self.configure(bg="#f5f7fb")

        self.imagen_original = None
        self.imagen_gris = None
        self.imagen_con_ruido = None
        self.imagen_resultado_espacial = None

        self.imagen_frecuencia_base = None
        self.espectro_centrado = None
        self.espectro_visible = None
        self.imagen_resultado_frecuencia = None

        self.referencias_imagenes = {}
        self.actualizacion_espectro_pendiente = None

        self._configurar_estilos()
        self._crear_interfaz()

    def _configurar_estilos(self):
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("TFrame", background="#f5f7fb")
        estilo.configure("Panel.TFrame", background="#ffffff", relief="flat")
        estilo.configure("Titulo.TLabel", background="#f5f7fb", foreground="#172033", font=("Segoe UI", 18, "bold"))
        estilo.configure("Subtitulo.TLabel", background="#ffffff", foreground="#172033", font=("Segoe UI", 11, "bold"))
        estilo.configure("Texto.TLabel", background="#ffffff", foreground="#495266", font=("Segoe UI", 10))
        estilo.configure("Valor.TLabel", background="#ffffff", foreground="#1f6feb", font=("Segoe UI", 10, "bold"))
        estilo.configure("TButton", font=("Segoe UI", 10, "bold"), padding=(14, 8))
        estilo.configure("Accent.TButton", background="#1f6feb", foreground="#ffffff")
        estilo.map("Accent.TButton", background=[("active", "#1557ba")])
        estilo.configure("TNotebook", background="#f5f7fb", borderwidth=0)
        estilo.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=(18, 9))
        estilo.map("TNotebook.Tab", background=[("selected", "#ffffff")], foreground=[("selected", "#1f6feb")])

    def _crear_interfaz(self):
        contenedor = ttk.Frame(self, padding=18)
        contenedor.pack(fill="both", expand=True)

        barra_superior = ttk.Frame(contenedor)
        barra_superior.pack(fill="x", pady=(0, 14))

        titulo = ttk.Label(
            barra_superior,
            text="Procesamiento digital de imagenes",
            style="Titulo.TLabel",
        )
        titulo.pack(side="left")

        boton_cargar = ttk.Button(
            barra_superior,
            text="Cargar imagen",
            style="Accent.TButton",
            command=self.cargar_imagen,
        )
        boton_cargar.pack(side="right")

        self.pestanas = ttk.Notebook(contenedor)
        self.pestanas.pack(fill="both", expand=True)

        self.tab_espacial = ttk.Frame(self.pestanas, padding=14)
        self.tab_frecuencia = ttk.Frame(self.pestanas, padding=14)
        self.pestanas.add(self.tab_espacial, text="Dominio espacial")
        self.pestanas.add(self.tab_frecuencia, text="Dominio de frecuencia")

        self._crear_tab_espacial()
        self._crear_tab_frecuencia()

    def _crear_tab_espacial(self):
        self.tab_espacial.columnconfigure((0, 1, 2), weight=1, uniform="imagenes")
        self.tab_espacial.rowconfigure(0, weight=1)

        self.lbl_original_espacial = self._crear_panel_imagen(self.tab_espacial, 0, "Imagen original")
        self.lbl_ruido = self._crear_panel_imagen(self.tab_espacial, 1, "Imagen sal y pimienta")
        self.lbl_resultado_espacial = self._crear_panel_imagen(self.tab_espacial, 2, "Imagen resultante")

        controles = ttk.Frame(self.tab_espacial, style="Panel.TFrame", padding=16)
        controles.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(14, 0))
        controles.columnconfigure(1, weight=1)
        controles.columnconfigure(4, weight=1)

        ttk.Label(controles, text="Ruido sal y pimienta", style="Subtitulo.TLabel").grid(row=0, column=0, sticky="w")
        self.valor_ruido = ttk.Label(controles, text="10 %", style="Valor.TLabel")
        self.valor_ruido.grid(row=0, column=2, sticky="w", padx=(10, 20))
        self.slider_ruido = ttk.Scale(controles, from_=0, to=40, orient="horizontal", command=self._actualizar_valor_ruido)
        self.slider_ruido.set(10)
        self.slider_ruido.grid(row=0, column=1, sticky="ew", padx=10)

        ttk.Button(controles, text="Aplicar ruido", command=self.aplicar_ruido).grid(row=0, column=3, padx=(0, 14))

        ttk.Label(controles, text="Filtro", style="Subtitulo.TLabel").grid(row=1, column=0, sticky="w", pady=(14, 0))
        self.combo_filtro = ttk.Combobox(
            controles,
            values=("Filtro de media", "Filtro de mediana", "Filtro de moda"),
            state="readonly",
        )
        self.combo_filtro.grid(row=1, column=1, sticky="ew", padx=10, pady=(14, 0))
        self.combo_filtro.set("Filtro de mediana")

        ttk.Button(controles, text="Aplicar filtro", command=self.aplicar_filtro).grid(row=1, column=3, padx=(0, 14), pady=(14, 0))
        ttk.Button(controles, text="Limpiar resultados", command=self.limpiar_espacial).grid(row=1, column=4, sticky="e", pady=(14, 0))

    def _crear_tab_frecuencia(self):
        self.tab_frecuencia.columnconfigure((0, 1, 2), weight=1, uniform="imagenes")
        self.tab_frecuencia.rowconfigure(0, weight=1)

        self.lbl_original_frecuencia = self._crear_panel_imagen(self.tab_frecuencia, 0, "Imagen original en grises")
        self.lbl_espectro = self._crear_panel_imagen(self.tab_frecuencia, 1, "Imagen espectro")
        self.lbl_resultado_frecuencia = self._crear_panel_imagen(self.tab_frecuencia, 2, "Imagen reconstruida")

        controles = ttk.Frame(self.tab_frecuencia, style="Panel.TFrame", padding=16)
        controles.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(14, 0))
        controles.columnconfigure(1, weight=1)

        ttk.Label(controles, text="Diametro del circulo central", style="Subtitulo.TLabel").grid(row=0, column=0, sticky="w")
        self.valor_diametro = ttk.Label(controles, text="360 px", style="Valor.TLabel")
        self.valor_diametro.grid(row=0, column=2, sticky="w", padx=(10, 20))
        self.slider_diametro = ttk.Scale(
            controles,
            from_=2,
            to=TAMANO_FRECUENCIA,
            orient="horizontal",
            command=self._actualizar_valor_diametro,
        )
        self.slider_diametro.set(360)
        self.slider_diametro.grid(row=0, column=1, sticky="ew", padx=10)
        self.slider_diametro.bind("<ButtonRelease-1>", self._procesar_frecuencia_al_soltar)

        ttk.Button(controles, text="Procesar frecuencia", command=self.procesar_frecuencia).grid(row=0, column=3, padx=(0, 14))
        ttk.Button(controles, text="Limpiar resultados", command=self.limpiar_frecuencia).grid(row=0, column=4, sticky="e")

    def _crear_panel_imagen(self, padre, columna, titulo):
        panel = ttk.Frame(padre, style="Panel.TFrame", padding=14)
        panel.grid(row=0, column=columna, sticky="nsew", padx=6)
        panel.rowconfigure(1, weight=1)
        panel.columnconfigure(0, weight=1)

        ttk.Label(panel, text=titulo, style="Subtitulo.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))
        etiqueta = ttk.Label(panel, text="Sin imagen", style="Texto.TLabel", anchor="center")
        etiqueta.grid(row=1, column=0, sticky="nsew")
        return etiqueta

    def cargar_imagen(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar imagen RGB",
            filetypes=(
                ("Imagenes", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
                ("Todos los archivos", "*.*"),
            ),
        )
        if not ruta:
            return

        try:
            self.imagen_original = Image.open(ruta).convert("RGB")
            self.imagen_gris = convertir_rgb_a_gris_manual(self.imagen_original)
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo cargar la imagen:\n{error}")
            return

        self.imagen_con_ruido = None
        self.imagen_resultado_espacial = None
        self.imagen_frecuencia_base = None
        self.espectro_centrado = None
        self.espectro_visible = None
        self.imagen_resultado_frecuencia = None

        self._mostrar_imagen_pil(self.lbl_original_espacial, self.imagen_original, "original_espacial")
        self._mostrar_imagen_gris(self.lbl_original_frecuencia, self.imagen_gris, "original_frecuencia")
        self._limpiar_etiqueta_imagen(self.lbl_ruido)
        self._limpiar_etiqueta_imagen(self.lbl_resultado_espacial)
        self._limpiar_etiqueta_imagen(self.lbl_espectro)
        self._limpiar_etiqueta_imagen(self.lbl_resultado_frecuencia)

    def aplicar_ruido(self):
        if self.imagen_gris is None:
            messagebox.showwarning("Advertencia", "Primero debe cargar una imagen.")
            return

        porcentaje = self.slider_ruido.get()
        self.imagen_con_ruido = agregar_ruido_sal_pimienta_manual(self.imagen_gris, porcentaje)
        self.imagen_resultado_espacial = None
        self._mostrar_imagen_gris(self.lbl_ruido, self.imagen_con_ruido, "ruido")
        self._limpiar_etiqueta_imagen(self.lbl_resultado_espacial)

    def aplicar_filtro(self):
        if self.imagen_gris is None:
            messagebox.showwarning("Advertencia", "Primero debe cargar una imagen.")
            return
        if self.imagen_con_ruido is None:
            messagebox.showwarning("Advertencia", "Primero debe aplicar ruido sal y pimienta.")
            return

        filtro = self.combo_filtro.get()
        if not filtro:
            messagebox.showwarning("Advertencia", "Seleccione un filtro.")
            return

        try:
            self.config(cursor="watch")
            self.update_idletasks()
            self.imagen_resultado_espacial = aplicar_filtro_manual(self.imagen_con_ruido, filtro)
            self._mostrar_imagen_gris(self.lbl_resultado_espacial, self.imagen_resultado_espacial, "resultado_espacial")
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo aplicar el filtro:\n{error}")
        finally:
            self.config(cursor="")

    def procesar_frecuencia(self):
        if self.imagen_gris is None:
            messagebox.showwarning("Advertencia", "Primero debe cargar una imagen.")
            return

        diametro = int(round(self.slider_diametro.get()))

        try:
            self.config(cursor="watch")
            self.update_idletasks()

            if self.espectro_centrado is None:
                self.imagen_frecuencia_base, self.espectro_centrado, self.espectro_visible = preparar_transformada_frecuencia(
                    self.imagen_gris,
                    tamano=TAMANO_FRECUENCIA,
                )
                self._mostrar_imagen_gris(self.lbl_original_frecuencia, self.imagen_frecuencia_base, "frecuencia_base")

            self._mostrar_espectro_con_diametro(diametro)
            self.imagen_resultado_frecuencia = reconstruir_desde_diametro(self.espectro_centrado, diametro)
            self._mostrar_imagen_gris(
                self.lbl_resultado_frecuencia,
                self.imagen_resultado_frecuencia,
                "resultado_frecuencia",
            )
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo procesar la frecuencia:\n{error}")
        finally:
            self.config(cursor="")

    def _procesar_frecuencia_al_soltar(self, _evento):
        if self.espectro_centrado is not None:
            self.procesar_frecuencia()

    def limpiar_espacial(self):
        self.imagen_con_ruido = None
        self.imagen_resultado_espacial = None
        self._limpiar_etiqueta_imagen(self.lbl_ruido)
        self._limpiar_etiqueta_imagen(self.lbl_resultado_espacial)

    def limpiar_frecuencia(self):
        self.imagen_frecuencia_base = None
        self.espectro_centrado = None
        self.espectro_visible = None
        self.imagen_resultado_frecuencia = None
        if self.imagen_gris is not None:
            self._mostrar_imagen_gris(self.lbl_original_frecuencia, self.imagen_gris, "original_frecuencia")
        else:
            self._limpiar_etiqueta_imagen(self.lbl_original_frecuencia)
        self._limpiar_etiqueta_imagen(self.lbl_espectro)
        self._limpiar_etiqueta_imagen(self.lbl_resultado_frecuencia)

    def _actualizar_valor_ruido(self, valor):
        self.valor_ruido.configure(text=f"{int(float(valor))} %")

    def _actualizar_valor_diametro(self, valor):
        diametro = int(float(valor))
        self.valor_diametro.configure(text=f"{diametro} px")
        if self.espectro_centrado is not None:
            if self.actualizacion_espectro_pendiente is not None:
                self.after_cancel(self.actualizacion_espectro_pendiente)
            self.actualizacion_espectro_pendiente = self.after(
                180,
                lambda: self._mostrar_espectro_con_diametro(diametro),
            )

    def _mostrar_espectro_con_diametro(self, diametro):
        self.actualizacion_espectro_pendiente = None
        espectro_mascara = obtener_espectro_con_mascara_visible(self.espectro_centrado, diametro)
        self._mostrar_imagen_gris(self.lbl_espectro, espectro_mascara, "espectro")

    def _mostrar_imagen_gris(self, etiqueta, arreglo, clave):
        imagen = arreglo_gris_a_imagen_pil(arreglo)
        self._mostrar_imagen_pil(etiqueta, imagen, clave)

    def _mostrar_imagen_pil(self, etiqueta, imagen, clave):
        imagen_visible = self._ajustar_imagen_para_panel(etiqueta, imagen)
        foto = ImageTk.PhotoImage(imagen_visible)
        self.referencias_imagenes[clave] = foto
        etiqueta.configure(image=foto, text="")

    def _ajustar_imagen_para_panel(self, etiqueta, imagen):
        max_ancho = etiqueta.winfo_width() - 30
        max_alto = etiqueta.winfo_height() - 30

        if max_ancho < 220:
            max_ancho = 360
        if max_alto < 220:
            max_alto = 420

        ancho, alto = imagen.size
        escala = min(max_ancho / ancho, max_alto / alto)
        nuevo_ancho = max(1, int(ancho * escala))
        nuevo_alto = max(1, int(alto * escala))
        return imagen.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)

    def _limpiar_etiqueta_imagen(self, etiqueta):
        etiqueta.configure(image="", text="Sin imagen")
