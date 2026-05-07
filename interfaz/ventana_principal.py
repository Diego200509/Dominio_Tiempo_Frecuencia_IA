import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageDraw, ImageTk

from logica.binarizacion import binarizar_manual
from logica.bordes import pasa_alto_espacial_manual, sobel_componentes_manual
from logica.bounding_box import detectar_y_dibujar_bounding_box_manual
from logica.conversion import (
    arreglo_rgb_a_imagen_pil,
    convertir_gris_a_rgb,
    convertir_rgb_a_gris_manual,
)
from logica.filtros_espaciales import aplicar_filtro_manual
from logica.frecuencia import FILTRO_PASA_ALTO, FILTRO_PASA_BAJO, procesar_filtro_frecuencia
from logica.histograma import calcular_histograma_manual, normalizar_histograma_manual
from logica.ruido import agregar_ruido_sal_pimienta_manual


TAMANO_FRECUENCIA = 512
UMBRAL_BINARIZACION = 128
ANCHO_VISTA_IMAGEN = 340
ALTO_VISTA_IMAGEN = 300
ANCHO_VISTA_BBOX = 500
ALTO_VISTA_BBOX = 330
ANCHO_VISTA_HISTOGRAMA = 980
ALTO_VISTA_HISTOGRAMA = 300


class VentanaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Procesamiento Digital de Imagenes - Dominios Espacial y Frecuencia")
        self.geometry("1340x860")
        self.minsize(1120, 720)
        self.configure(bg="#f5f7fb")

        self.imagen_original = None
        self.imagen_gris = None
        self.imagen_normalizada = None
        self.grafico_histogramas = None

        self.imagen_con_ruido = None
        self.imagen_filtrada_espacial = None
        self.imagen_pasa_alto_espacial = None
        self.imagen_sobel_x_espacial = None
        self.imagen_sobel_y_espacial = None
        self.imagen_sobel_magnitud_espacial = None
        self.imagen_binaria_espacial = None
        self.imagen_bbox_espacial = None
        self.objetos_espacial = []

        self.imagen_base_frecuencia = None
        self.imagen_ruido_frecuencia = None
        self.espectro_visible = None
        self.espectro_filtrado_visible = None
        self.imagen_reconstruida_frecuencia = None
        self.imagen_sobel_x_frecuencia = None
        self.imagen_sobel_y_frecuencia = None
        self.imagen_sobel_magnitud_frecuencia = None
        self.imagen_binaria_frecuencia = None
        self.imagen_bbox_frecuencia = None
        self.objetos_frecuencia = []

        self.referencias_imagenes = {}
        self.imagenes_fuente = {}
        self.redibujado_pendiente = None
        self.lienzo_scroll_activo = None

        self._configurar_estilos()
        self._crear_interfaz()
        self.bind_all("<MouseWheel>", self._mover_scroll_activo)

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

        ttk.Label(
            barra_superior,
            text="Procesamiento digital de imagenes",
            style="Titulo.TLabel",
        ).pack(side="left")

        ttk.Button(
            barra_superior,
            text="Limpiar resultados",
            command=self.limpiar_resultados,
        ).pack(side="right", padx=(10, 0))

        ttk.Button(
            barra_superior,
            text="Cargar imagen",
            style="Accent.TButton",
            command=self.cargar_imagen,
        ).pack(side="right")

        self.pestanas = ttk.Notebook(contenedor)
        self.pestanas.pack(fill="both", expand=True)

        contenedor_pre, self.tab_preprocesamiento = self._crear_pestana_con_scroll()
        contenedor_espacial, self.tab_espacial = self._crear_pestana_con_scroll()
        contenedor_frecuencia, self.tab_frecuencia = self._crear_pestana_con_scroll()
        self.pestanas.add(contenedor_pre, text="Preprocesamiento")
        self.pestanas.add(contenedor_espacial, text="Dominio espacial")
        self.pestanas.add(contenedor_frecuencia, text="Dominio de frecuencia")
        self.pestanas.bind("<<NotebookTabChanged>>", self._programar_redibujado_imagenes)

        self._crear_tab_preprocesamiento()
        self._crear_tab_espacial()
        self._crear_tab_frecuencia()

    def _crear_pestana_con_scroll(self):
        contenedor = ttk.Frame(self.pestanas)
        lienzo = tk.Canvas(contenedor, background="#f5f7fb", highlightthickness=0)
        barra = ttk.Scrollbar(contenedor, orient="vertical", command=lienzo.yview)
        contenido = ttk.Frame(lienzo, padding=14)
        ventana = lienzo.create_window((0, 0), window=contenido, anchor="nw")

        lienzo.configure(yscrollcommand=barra.set)
        lienzo.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        def ajustar_region(_evento):
            lienzo.configure(scrollregion=lienzo.bbox("all"))

        def ajustar_ancho(evento):
            lienzo.itemconfigure(ventana, width=evento.width)

        contenido.bind("<Configure>", ajustar_region)
        lienzo.bind("<Configure>", ajustar_ancho)
        lienzo.bind("<Enter>", lambda _evento: self._activar_scroll(lienzo))
        lienzo.bind("<Leave>", lambda _evento: self._desactivar_scroll(lienzo))
        contenido.bind("<Enter>", lambda _evento: self._activar_scroll(lienzo))
        return contenedor, contenido

    def _activar_scroll(self, lienzo):
        self.lienzo_scroll_activo = lienzo

    def _desactivar_scroll(self, lienzo):
        if self.lienzo_scroll_activo == lienzo:
            self.lienzo_scroll_activo = None

    def _mover_scroll_activo(self, evento):
        if self.lienzo_scroll_activo is not None:
            self.lienzo_scroll_activo.yview_scroll(int(-1 * (evento.delta / 120)), "units")

    def _crear_tab_preprocesamiento(self):
        for columna in range(3):
            self.tab_preprocesamiento.columnconfigure(columna, weight=1, uniform="pre_columnas")
        self.tab_preprocesamiento.rowconfigure(0, weight=1, minsize=430)
        self.tab_preprocesamiento.rowconfigure(1, weight=0, minsize=360)

        self.lbl_pre_original = self._crear_panel_imagen(self.tab_preprocesamiento, 0, 0, "Imagen original RGB")
        self.lbl_pre_gris = self._crear_panel_imagen(self.tab_preprocesamiento, 0, 1, "Escala de grises")
        self.lbl_pre_normalizada = self._crear_panel_imagen(self.tab_preprocesamiento, 0, 2, "Imagen normalizada")
        self.lbl_histogramas = self._crear_panel_imagen(
            self.tab_preprocesamiento,
            1,
            0,
            "Comparativa de histogramas: gris original vs normalizado",
            columnas=3,
        )

    def _crear_tab_espacial(self):
        for columna in range(4):
            self.tab_espacial.columnconfigure(columna, weight=1, uniform="espacial_columnas")
        for fila in range(3):
            self.tab_espacial.rowconfigure(fila, weight=1, minsize=390)

        self.lbl_base_espacial = self._crear_panel_imagen(self.tab_espacial, 0, 0, "Base gris normalizada")
        self.lbl_ruido = self._crear_panel_imagen(self.tab_espacial, 0, 1, "Ruido sal y pimienta")
        self.lbl_filtrada_espacial = self._crear_panel_imagen(self.tab_espacial, 0, 2, "Filtro espacial")
        self.lbl_pasa_alto_espacial = self._crear_panel_imagen(self.tab_espacial, 0, 3, "Pasa-alto espacial")
        self.lbl_sobel_x_espacial = self._crear_panel_imagen(self.tab_espacial, 1, 0, "Sobel X")
        self.lbl_sobel_y_espacial = self._crear_panel_imagen(self.tab_espacial, 1, 1, "Sobel Y")
        self.lbl_sobel_magnitud_espacial = self._crear_panel_imagen(self.tab_espacial, 1, 2, "Magnitud Sobel")
        self.lbl_binaria_espacial = self._crear_panel_imagen(self.tab_espacial, 1, 3, "Binarizacion final")
        self.lbl_bbox_espacial = self._crear_panel_imagen(self.tab_espacial, 2, 0, "Bounding box final", columnas=3)
        self.lbl_metricas_espacial = self._crear_panel_texto(self.tab_espacial, 2, 3, "Area y perimetro")

        controles = ttk.Frame(self.tab_espacial, style="Panel.TFrame", padding=16)
        controles.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(14, 0))
        controles.columnconfigure(1, weight=1)
        controles.columnconfigure(4, weight=1)

        ttk.Label(controles, text="Ruido sal y pimienta", style="Subtitulo.TLabel").grid(row=0, column=0, sticky="w")
        self.valor_ruido = ttk.Label(controles, text="0.10", style="Valor.TLabel")
        self.valor_ruido.grid(row=0, column=2, sticky="w", padx=(10, 20))
        self.slider_ruido = ttk.Scale(controles, from_=0, to=0.40, orient="horizontal", command=self._actualizar_valor_ruido)
        self.slider_ruido.set(0.10)
        self.slider_ruido.grid(row=0, column=1, sticky="ew", padx=10)

        ttk.Label(controles, text="Filtro espacial", style="Subtitulo.TLabel").grid(row=1, column=0, sticky="w", pady=(14, 0))
        self.combo_filtro = ttk.Combobox(
            controles,
            values=("Filtro de media", "Filtro de mediana", "Filtro de moda"),
            state="readonly",
        )
        self.combo_filtro.grid(row=1, column=1, sticky="ew", padx=10, pady=(14, 0))
        self.combo_filtro.set("Filtro de mediana")

        ttk.Label(controles, text="Ventana", style="Subtitulo.TLabel").grid(row=1, column=2, sticky="e", pady=(14, 0))
        self.combo_tamano_ventana = ttk.Combobox(
            controles,
            values=("3x3", "5x5", "7x7", "11x11"),
            state="readonly",
            width=8,
        )
        self.combo_tamano_ventana.grid(row=1, column=3, sticky="w", padx=(10, 14), pady=(14, 0))
        self.combo_tamano_ventana.set("3x3")

        ttk.Label(controles, text="Umbral binarizacion", style="Subtitulo.TLabel").grid(row=2, column=0, sticky="w", pady=(14, 0))
        self.valor_umbral_espacial = ttk.Label(controles, text=str(UMBRAL_BINARIZACION), style="Valor.TLabel")
        self.valor_umbral_espacial.grid(row=2, column=2, sticky="w", padx=(10, 20), pady=(14, 0))
        self.slider_umbral_espacial = ttk.Scale(
            controles,
            from_=0,
            to=255,
            orient="horizontal",
            command=self._actualizar_umbral_espacial,
        )
        self.slider_umbral_espacial.set(UMBRAL_BINARIZACION)
        self.slider_umbral_espacial.grid(row=2, column=1, sticky="ew", padx=10, pady=(14, 0))

        ttk.Button(controles, text="Procesar dominio espacial", command=self.procesar_dominio_espacial).grid(row=0, column=3, padx=(0, 14))
        ttk.Button(controles, text="Limpiar espacial", command=self.limpiar_espacial).grid(row=2, column=3, padx=(0, 14), pady=(14, 0))

    def _crear_tab_frecuencia(self):
        for columna in range(4):
            self.tab_frecuencia.columnconfigure(columna, weight=1, uniform="frecuencia_columnas")
        for fila in range(3):
            self.tab_frecuencia.rowconfigure(fila, weight=1, minsize=390)

        self.lbl_base_frecuencia = self._crear_panel_imagen(self.tab_frecuencia, 0, 0, "Base gris normalizada")
        self.lbl_ruido_frecuencia = self._crear_panel_imagen(self.tab_frecuencia, 0, 1, "Ruido sal y pimienta")
        self.lbl_espectro = self._crear_panel_imagen(self.tab_frecuencia, 0, 2, "Espectro Fourier")
        self.lbl_espectro_filtrado = self._crear_panel_imagen(self.tab_frecuencia, 0, 3, "Espectro con mascara")
        self.lbl_reconstruida_frecuencia = self._crear_panel_imagen(self.tab_frecuencia, 1, 0, "Imagen reconstruida")
        self.lbl_sobel_x_frecuencia = self._crear_panel_imagen(self.tab_frecuencia, 1, 1, "Sobel X")
        self.lbl_sobel_y_frecuencia = self._crear_panel_imagen(self.tab_frecuencia, 1, 2, "Sobel Y")
        self.lbl_sobel_magnitud_frecuencia = self._crear_panel_imagen(self.tab_frecuencia, 1, 3, "Magnitud Sobel")
        self.lbl_binaria_frecuencia = self._crear_panel_imagen(self.tab_frecuencia, 2, 0, "Binarizacion final")
        self.lbl_bbox_frecuencia = self._crear_panel_imagen(self.tab_frecuencia, 2, 1, "Bounding box final", columnas=2)
        self.lbl_metricas_frecuencia = self._crear_panel_texto(self.tab_frecuencia, 2, 3, "Area y perimetro")

        controles = ttk.Frame(self.tab_frecuencia, style="Panel.TFrame", padding=16)
        controles.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(14, 0))
        controles.columnconfigure(1, weight=1)
        controles.columnconfigure(4, weight=1)

        ttk.Label(controles, text="Ruido sal y pimienta", style="Subtitulo.TLabel").grid(row=0, column=0, sticky="w")
        self.valor_ruido_frecuencia = ttk.Label(controles, text="0.10", style="Valor.TLabel")
        self.valor_ruido_frecuencia.grid(row=0, column=2, sticky="w", padx=(10, 20))
        self.slider_ruido_frecuencia = ttk.Scale(
            controles,
            from_=0,
            to=0.40,
            orient="horizontal",
            command=self._actualizar_valor_ruido_frecuencia,
        )
        self.slider_ruido_frecuencia.set(0.10)
        self.slider_ruido_frecuencia.grid(row=0, column=1, sticky="ew", padx=10)

        ttk.Label(controles, text="Filtro frecuencia", style="Subtitulo.TLabel").grid(row=1, column=0, sticky="w", pady=(14, 0))
        self.combo_frecuencia = ttk.Combobox(
            controles,
            values=(FILTRO_PASA_BAJO, FILTRO_PASA_ALTO),
            state="readonly",
        )
        self.combo_frecuencia.grid(row=1, column=1, sticky="ew", padx=10, pady=(14, 0))
        self.combo_frecuencia.set(FILTRO_PASA_BAJO)

        ttk.Label(controles, text="Radio mascara", style="Subtitulo.TLabel").grid(row=2, column=0, sticky="w", pady=(14, 0))
        self.valor_radio = ttk.Label(controles, text="120 px", style="Valor.TLabel")
        self.valor_radio.grid(row=2, column=2, sticky="w", padx=(10, 20), pady=(14, 0))
        self.slider_radio = ttk.Scale(controles, from_=1, to=TAMANO_FRECUENCIA // 2, orient="horizontal", command=self._actualizar_radio)
        self.slider_radio.set(120)
        self.slider_radio.grid(row=2, column=1, sticky="ew", padx=10, pady=(14, 0))

        ttk.Label(controles, text="Umbral binarizacion", style="Subtitulo.TLabel").grid(row=3, column=0, sticky="w", pady=(14, 0))
        self.valor_umbral_frecuencia = ttk.Label(controles, text=str(UMBRAL_BINARIZACION), style="Valor.TLabel")
        self.valor_umbral_frecuencia.grid(row=3, column=2, sticky="w", padx=(10, 20), pady=(14, 0))
        self.slider_umbral_frecuencia = ttk.Scale(
            controles,
            from_=0,
            to=255,
            orient="horizontal",
            command=self._actualizar_umbral_frecuencia,
        )
        self.slider_umbral_frecuencia.set(UMBRAL_BINARIZACION)
        self.slider_umbral_frecuencia.grid(row=3, column=1, sticky="ew", padx=10, pady=(14, 0))

        ttk.Button(controles, text="Procesar frecuencia", command=self.procesar_dominio_frecuencia).grid(row=0, column=3, padx=(0, 14))
        ttk.Button(controles, text="Limpiar frecuencia", command=self.limpiar_frecuencia).grid(row=1, column=3, padx=(0, 14), pady=(14, 0))

    def _crear_panel_imagen(self, padre, fila, columna, titulo, columnas=1):
        panel = ttk.Frame(padre, style="Panel.TFrame", padding=14)
        panel.grid(row=fila, column=columna, columnspan=columnas, sticky="nsew", padx=6, pady=6)
        panel.rowconfigure(1, weight=1)
        panel.columnconfigure(0, weight=1)

        ttk.Label(panel, text=titulo, style="Subtitulo.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))
        etiqueta = ttk.Label(panel, text="Sin imagen", style="Texto.TLabel", anchor="center")
        etiqueta.grid(row=1, column=0, sticky="nsew")
        return etiqueta

    def _crear_panel_texto(self, padre, fila, columna, titulo, columnas=1):
        panel = ttk.Frame(padre, style="Panel.TFrame", padding=14)
        panel.grid(row=fila, column=columna, columnspan=columnas, sticky="nsew", padx=6, pady=6)
        panel.rowconfigure(1, weight=1)
        panel.columnconfigure(0, weight=1)

        ttk.Label(panel, text=titulo, style="Subtitulo.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))
        etiqueta = ttk.Label(panel, text="Sin objetos", style="Texto.TLabel", anchor="nw", justify="left")
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
            self.imagen_normalizada = normalizar_histograma_manual(self.imagen_gris)
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo cargar o preprocesar la imagen:\n{error}")
            return

        self._reiniciar_resultados_derivados()
        self._mostrar_preprocesamiento()
        self._mostrar_imagen_gris(self.lbl_base_espacial, self.imagen_normalizada, "base_espacial")
        self._mostrar_imagen_gris(self.lbl_base_frecuencia, self.imagen_normalizada, "base_frecuencia")

    def _mostrar_preprocesamiento(self):
        self._mostrar_imagen_pil(self.lbl_pre_original, self.imagen_original, "pre_original")
        self._mostrar_imagen_gris(self.lbl_pre_gris, self.imagen_gris, "pre_gris")
        self._mostrar_imagen_gris(self.lbl_pre_normalizada, self.imagen_normalizada, "pre_normalizada")
        self.grafico_histogramas = self._crear_grafico_histogramas(
            self.imagen_gris,
            self.imagen_normalizada,
        )
        self._mostrar_imagen_pil(self.lbl_histogramas, self.grafico_histogramas, "histogramas")

    def procesar_dominio_espacial(self):
        if self.imagen_normalizada is None:
            messagebox.showwarning("Advertencia", "Primero debe cargar una imagen.")
            return

        filtro = self.combo_filtro.get()
        if not filtro:
            messagebox.showwarning("Advertencia", "Seleccione un filtro espacial.")
            return

        try:
            self.config(cursor="watch")
            self.update_idletasks()

            nivel_ruido = float(self.slider_ruido.get())
            umbral = int(round(self.slider_umbral_espacial.get()))
            tamano_ventana = int(self.combo_tamano_ventana.get().split("x")[0])
            self.imagen_con_ruido = agregar_ruido_sal_pimienta_manual(self.imagen_normalizada, nivel_ruido)
            self.imagen_filtrada_espacial = aplicar_filtro_manual(self.imagen_con_ruido, filtro, tamano_ventana)
            self.imagen_pasa_alto_espacial = pasa_alto_espacial_manual(self.imagen_filtrada_espacial)
            (
                self.imagen_sobel_x_espacial,
                self.imagen_sobel_y_espacial,
                self.imagen_sobel_magnitud_espacial,
            ) = sobel_componentes_manual(self.imagen_pasa_alto_espacial)
            self.imagen_binaria_espacial = binarizar_manual(self.imagen_sobel_magnitud_espacial, umbral)
            self.objetos_espacial, self.imagen_bbox_espacial = detectar_y_dibujar_bounding_box_manual(
                self.imagen_binaria_espacial,
                self.imagen_normalizada,
                grosor=4,
            )

            self._mostrar_imagen_gris(self.lbl_ruido, self.imagen_con_ruido, "ruido")
            self._mostrar_imagen_gris(self.lbl_filtrada_espacial, self.imagen_filtrada_espacial, "filtrada_espacial")
            self._mostrar_imagen_gris(self.lbl_pasa_alto_espacial, self.imagen_pasa_alto_espacial, "pasa_alto_espacial")
            self._mostrar_imagen_gris(self.lbl_sobel_x_espacial, self.imagen_sobel_x_espacial, "sobel_x_espacial")
            self._mostrar_imagen_gris(self.lbl_sobel_y_espacial, self.imagen_sobel_y_espacial, "sobel_y_espacial")
            self._mostrar_imagen_gris(
                self.lbl_sobel_magnitud_espacial,
                self.imagen_sobel_magnitud_espacial,
                "sobel_magnitud_espacial",
            )
            self._mostrar_imagen_gris(self.lbl_binaria_espacial, self.imagen_binaria_espacial, "binaria_espacial")
            self._mostrar_imagen_rgb(self.lbl_bbox_espacial, self.imagen_bbox_espacial, "bbox_espacial")
            self._mostrar_metricas(self.lbl_metricas_espacial, self.objetos_espacial)
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo procesar el dominio espacial:\n{error}")
        finally:
            self.config(cursor="")

    def procesar_dominio_frecuencia(self):
        if self.imagen_normalizada is None:
            messagebox.showwarning("Advertencia", "Primero debe cargar una imagen.")
            return

        tipo_filtro = self.combo_frecuencia.get()
        if not tipo_filtro:
            messagebox.showwarning("Advertencia", "Seleccione un filtro de frecuencia.")
            return

        try:
            self.config(cursor="watch")
            self.update_idletasks()

            radio = int(round(self.slider_radio.get()))
            umbral = int(round(self.slider_umbral_frecuencia.get()))
            nivel_ruido = float(self.slider_ruido_frecuencia.get())
            self.imagen_ruido_frecuencia = agregar_ruido_sal_pimienta_manual(self.imagen_normalizada, nivel_ruido)
            resultado = procesar_filtro_frecuencia(
                self.imagen_ruido_frecuencia,
                radio,
                tipo_filtro=tipo_filtro,
                tamano=TAMANO_FRECUENCIA,
            )

            self.imagen_base_frecuencia = self.imagen_normalizada
            self.espectro_visible = resultado["espectro"]
            self.espectro_filtrado_visible = resultado["espectro_mascara"]
            self.imagen_reconstruida_frecuencia = resultado["reconstruida"]
            (
                self.imagen_sobel_x_frecuencia,
                self.imagen_sobel_y_frecuencia,
                self.imagen_sobel_magnitud_frecuencia,
            ) = sobel_componentes_manual(self.imagen_reconstruida_frecuencia)
            self.imagen_binaria_frecuencia = binarizar_manual(self.imagen_sobel_magnitud_frecuencia, umbral)
            self.objetos_frecuencia, self.imagen_bbox_frecuencia = detectar_y_dibujar_bounding_box_manual(
                self.imagen_binaria_frecuencia,
                self.imagen_reconstruida_frecuencia,
                grosor=4,
            )

            self._mostrar_imagen_gris(self.lbl_base_frecuencia, self.imagen_base_frecuencia, "base_frecuencia")
            self._mostrar_imagen_gris(self.lbl_ruido_frecuencia, self.imagen_ruido_frecuencia, "ruido_frecuencia")
            self._mostrar_imagen_gris(self.lbl_espectro, self.espectro_visible, "espectro")
            self._mostrar_imagen_gris(self.lbl_espectro_filtrado, self.espectro_filtrado_visible, "espectro_filtrado")
            self._mostrar_imagen_gris(
                self.lbl_reconstruida_frecuencia,
                self.imagen_reconstruida_frecuencia,
                "reconstruida_frecuencia",
            )
            self._mostrar_imagen_gris(self.lbl_sobel_x_frecuencia, self.imagen_sobel_x_frecuencia, "sobel_x_frecuencia")
            self._mostrar_imagen_gris(self.lbl_sobel_y_frecuencia, self.imagen_sobel_y_frecuencia, "sobel_y_frecuencia")
            self._mostrar_imagen_gris(
                self.lbl_sobel_magnitud_frecuencia,
                self.imagen_sobel_magnitud_frecuencia,
                "sobel_magnitud_frecuencia",
            )
            self._mostrar_imagen_gris(self.lbl_binaria_frecuencia, self.imagen_binaria_frecuencia, "binaria_frecuencia")
            self._mostrar_imagen_rgb(self.lbl_bbox_frecuencia, self.imagen_bbox_frecuencia, "bbox_frecuencia")
            self._mostrar_metricas(self.lbl_metricas_frecuencia, self.objetos_frecuencia)
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo procesar la frecuencia:\n{error}")
        finally:
            self.config(cursor="")

    def limpiar_resultados(self):
        self.limpiar_espacial()
        self.limpiar_frecuencia()

    def limpiar_espacial(self):
        self.imagen_con_ruido = None
        self.imagen_filtrada_espacial = None
        self.imagen_pasa_alto_espacial = None
        self.imagen_sobel_x_espacial = None
        self.imagen_sobel_y_espacial = None
        self.imagen_sobel_magnitud_espacial = None
        self.imagen_binaria_espacial = None
        self.imagen_bbox_espacial = None
        self.objetos_espacial = []
        for etiqueta in (
            self.lbl_ruido,
            self.lbl_filtrada_espacial,
            self.lbl_pasa_alto_espacial,
            self.lbl_sobel_x_espacial,
            self.lbl_sobel_y_espacial,
            self.lbl_sobel_magnitud_espacial,
            self.lbl_binaria_espacial,
            self.lbl_bbox_espacial,
        ):
            self._limpiar_etiqueta_imagen(etiqueta)
        self._limpiar_etiqueta_texto(self.lbl_metricas_espacial)
        if self.imagen_normalizada is not None:
            self._mostrar_imagen_gris(self.lbl_base_espacial, self.imagen_normalizada, "base_espacial")

    def limpiar_frecuencia(self):
        self.imagen_base_frecuencia = None
        self.imagen_ruido_frecuencia = None
        self.espectro_visible = None
        self.espectro_filtrado_visible = None
        self.imagen_reconstruida_frecuencia = None
        self.imagen_sobel_x_frecuencia = None
        self.imagen_sobel_y_frecuencia = None
        self.imagen_sobel_magnitud_frecuencia = None
        self.imagen_binaria_frecuencia = None
        self.imagen_bbox_frecuencia = None
        self.objetos_frecuencia = []
        for etiqueta in (
            self.lbl_ruido_frecuencia,
            self.lbl_espectro,
            self.lbl_espectro_filtrado,
            self.lbl_reconstruida_frecuencia,
            self.lbl_sobel_x_frecuencia,
            self.lbl_sobel_y_frecuencia,
            self.lbl_sobel_magnitud_frecuencia,
            self.lbl_binaria_frecuencia,
            self.lbl_bbox_frecuencia,
        ):
            self._limpiar_etiqueta_imagen(etiqueta)
        self._limpiar_etiqueta_texto(self.lbl_metricas_frecuencia)
        if self.imagen_normalizada is not None:
            self._mostrar_imagen_gris(self.lbl_base_frecuencia, self.imagen_normalizada, "base_frecuencia")

    def _reiniciar_resultados_derivados(self):
        self.limpiar_espacial()
        self.limpiar_frecuencia()

    def _actualizar_valor_ruido(self, valor):
        self.valor_ruido.configure(text=f"{float(valor):.2f}")

    def _actualizar_valor_ruido_frecuencia(self, valor):
        self.valor_ruido_frecuencia.configure(text=f"{float(valor):.2f}")

    def _actualizar_umbral_espacial(self, valor):
        self.valor_umbral_espacial.configure(text=str(int(float(valor))))

    def _actualizar_radio(self, valor):
        self.valor_radio.configure(text=f"{int(float(valor))} px")

    def _actualizar_umbral_frecuencia(self, valor):
        self.valor_umbral_frecuencia.configure(text=str(int(float(valor))))

    def _mostrar_metricas(self, etiqueta, objetos):
        if not objetos:
            etiqueta.configure(text="No se detectaron objetos.")
            return

        lineas = ["Obj | x  y  ancho alto | area | perim."]
        for indice, objeto in enumerate(objetos, start=1):
            lineas.append(
                f"{indice:>3} | "
                f"{objeto['x']:>3} {objeto['y']:>3} "
                f"{objeto['ancho']:>5} {objeto['alto']:>4} | "
                f"{objeto['area']:>4} | {objeto['perimetro']:>5}"
            )
            if indice >= 12 and len(objetos) > 12:
                lineas.append(f"... {len(objetos) - 12} objetos mas")
                break

        etiqueta.configure(text="\n".join(lineas))

    def _limpiar_etiqueta_texto(self, etiqueta):
        etiqueta.configure(text="Sin objetos")

    def _mostrar_imagen_gris(self, etiqueta, arreglo, clave):
        imagen_rgb = convertir_gris_a_rgb(arreglo)
        imagen = arreglo_rgb_a_imagen_pil(imagen_rgb)
        self._mostrar_imagen_pil(etiqueta, imagen, clave)

    def _mostrar_imagen_rgb(self, etiqueta, arreglo_rgb, clave):
        imagen = arreglo_rgb_a_imagen_pil(arreglo_rgb)
        self._mostrar_imagen_pil(etiqueta, imagen, clave)

    def _mostrar_imagen_pil(self, etiqueta, imagen, clave):
        self.imagenes_fuente[clave] = (etiqueta, imagen)
        self._renderizar_imagen_pil(etiqueta, imagen, clave)
        self._programar_redibujado_imagenes()

    def _renderizar_imagen_pil(self, etiqueta, imagen, clave):
        if not etiqueta.winfo_ismapped():
            return

        imagen_visible = self._ajustar_imagen_para_panel(etiqueta, imagen, clave)
        foto = ImageTk.PhotoImage(imagen_visible)
        self.referencias_imagenes[clave] = foto
        etiqueta.configure(image=foto, text="")

    def _programar_redibujado_imagenes(self, _evento=None):
        if self.redibujado_pendiente is not None:
            self.after_cancel(self.redibujado_pendiente)
        self.redibujado_pendiente = self.after(120, self._redibujar_imagenes_visibles)

    def _redibujar_imagenes_visibles(self):
        self.redibujado_pendiente = None
        self.update_idletasks()
        for clave, (etiqueta, imagen) in self.imagenes_fuente.items():
            self._renderizar_imagen_pil(etiqueta, imagen, clave)

    def _crear_grafico_histogramas(self, imagen_gris, imagen_normalizada):
        histograma_gris = calcular_histograma_manual(imagen_gris)
        histograma_normalizado = calcular_histograma_manual(imagen_normalizada)

        ancho = 980
        alto = 300
        margen_izq = 56
        margen_der = 24
        margen_sup = 28
        margen_inf = 44
        ancho_grafico = ancho - margen_izq - margen_der
        alto_grafico = alto - margen_sup - margen_inf

        imagen = Image.new("RGB", (ancho, alto), "white")
        dibujo = ImageDraw.Draw(imagen)

        maximo = 1
        for valor in histograma_gris + histograma_normalizado:
            if valor > maximo:
                maximo = valor

        x0 = margen_izq
        y0 = margen_sup
        x1 = ancho - margen_der
        y1 = alto - margen_inf

        dibujo.rectangle((x0, y0, x1, y1), outline="#d0d7de", width=1)
        dibujo.line((x0, y1, x1, y1), fill="#495266", width=2)
        dibujo.line((x0, y0, x0, y1), fill="#495266", width=2)

        for marca in range(0, 256, 64):
            x = x0 + int(marca * ancho_grafico / 255)
            dibujo.line((x, y1, x, y1 + 5), fill="#495266", width=1)
            dibujo.text((x - 10, y1 + 10), str(marca), fill="#495266")

        dibujo.text((x0, 6), "Gris original", fill="#1f6feb")
        dibujo.rectangle((x0 + 92, 10, x0 + 112, 20), fill="#1f6feb")
        dibujo.text((x0 + 140, 6), "Normalizado", fill="#d97706")
        dibujo.rectangle((x0 + 232, 10, x0 + 252, 20), fill="#d97706")

        puntos_gris = []
        puntos_normalizados = []
        for intensidad in range(256):
            x = x0 + int(intensidad * ancho_grafico / 255)
            y_gris = y1 - int(histograma_gris[intensidad] * alto_grafico / maximo)
            y_norm = y1 - int(histograma_normalizado[intensidad] * alto_grafico / maximo)
            puntos_gris.append((x, y_gris))
            puntos_normalizados.append((x, y_norm))

        if len(puntos_gris) > 1:
            dibujo.line(puntos_gris, fill="#1f6feb", width=2)
            dibujo.line(puntos_normalizados, fill="#d97706", width=2)

        return imagen

    def _ajustar_imagen_para_panel(self, etiqueta, imagen, clave):
        if clave == "histogramas":
            limite_ancho = ANCHO_VISTA_HISTOGRAMA
            limite_alto = ALTO_VISTA_HISTOGRAMA
        elif clave.startswith("bbox"):
            limite_ancho = ANCHO_VISTA_BBOX
            limite_alto = ALTO_VISTA_BBOX
        else:
            limite_ancho = ANCHO_VISTA_IMAGEN
            limite_alto = ALTO_VISTA_IMAGEN

        ancho_widget = etiqueta.winfo_width() - 28
        alto_widget = etiqueta.winfo_height() - 28
        if ancho_widget > 120:
            limite_ancho = min(limite_ancho, ancho_widget)
        if alto_widget > 120:
            limite_alto = min(limite_alto, alto_widget)

        ancho, alto = imagen.size
        escala = min(limite_ancho / ancho, limite_alto / alto)
        nuevo_ancho = max(1, int(ancho * escala))
        nuevo_alto = max(1, int(alto * escala))
        return imagen.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)

    def _limpiar_etiqueta_imagen(self, etiqueta):
        claves_a_borrar = []
        for clave, (etiqueta_guardada, _imagen) in self.imagenes_fuente.items():
            if etiqueta_guardada == etiqueta:
                claves_a_borrar.append(clave)

        for clave in claves_a_borrar:
            del self.imagenes_fuente[clave]
            if clave in self.referencias_imagenes:
                del self.referencias_imagenes[clave]

        etiqueta.configure(image="", text="Sin imagen")
