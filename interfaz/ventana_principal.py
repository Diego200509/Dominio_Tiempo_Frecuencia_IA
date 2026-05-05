import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from logica.binarizacion import binarizar_manual
from logica.conversion import (
    arreglo_rgb_a_imagen_pil,
    convertir_gris_a_rgb,
    convertir_rgb_a_gris_manual,
)
from logica.filtros_espaciales import aplicar_filtro_manual
from logica.frecuencia import (
    obtener_espectro_con_mascara_visible,
    preparar_transformada_frecuencia,
    reconstruir_desde_diametro,
)
from logica.histograma import normalizar_histograma_manual
from logica.ruido import agregar_ruido_sal_pimienta_manual


TAMANO_FRECUENCIA = 1024
UMBRAL_BINARIZACION = 128


class VentanaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Procesamiento Digital de Imagenes - Dominios Espacial y Frecuencia")
        self.geometry("1240x800")
        self.minsize(1060, 680)
        self.configure(bg="#f5f7fb")

        self.imagen_original = None
        self.imagen_gris = None
        self.imagen_normalizada = None
        self.imagen_binarizada = None

        self.imagen_con_ruido = None
        self.imagen_resultado_espacial = None

        self.imagen_frecuencia_base = None
        self.espectro_centrado = None
        self.espectro_visible = None
        self.imagen_resultado_frecuencia = None

        self.referencias_imagenes = {}
        self.actualizacion_ruido_pendiente = None
        self.actualizacion_frecuencia_pendiente = None
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

        titulo = ttk.Label(
            barra_superior,
            text="Procesamiento digital de imagenes",
            style="Titulo.TLabel",
        )
        titulo.pack(side="left")

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

        contenedor_pre, self.tab_preprocesamiento = self._crear_pestana_con_scroll("Preprocesamiento")
        contenedor_espacial, self.tab_espacial = self._crear_pestana_con_scroll("Dominio espacial")
        contenedor_frecuencia, self.tab_frecuencia = self._crear_pestana_con_scroll("Dominio de frecuencia")
        self.pestanas.add(contenedor_pre, text="Preprocesamiento")
        self.pestanas.add(contenedor_espacial, text="Dominio espacial")
        self.pestanas.add(contenedor_frecuencia, text="Dominio de frecuencia")

        self._crear_tab_preprocesamiento()
        self._crear_tab_espacial()
        self._crear_tab_frecuencia()

    def _crear_pestana_con_scroll(self, _nombre):
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
        for columna in range(2):
            self.tab_preprocesamiento.columnconfigure(columna, weight=1, uniform="pre_columnas")
        for fila in range(2):
            self.tab_preprocesamiento.rowconfigure(fila, weight=1, uniform="pre_filas", minsize=430)

        self.lbl_pre_original = self._crear_panel_imagen(self.tab_preprocesamiento, 0, 0, "Imagen original RGB")
        self.lbl_pre_gris = self._crear_panel_imagen(self.tab_preprocesamiento, 0, 1, "Escala de grises")
        self.lbl_pre_normalizada = self._crear_panel_imagen(self.tab_preprocesamiento, 1, 0, "Histograma normalizado")
        self.lbl_pre_binarizada = self._crear_panel_imagen(self.tab_preprocesamiento, 1, 1, "Imagen binarizada")

    def _crear_tab_espacial(self):
        for columna in range(3):
            self.tab_espacial.columnconfigure(columna, weight=1, uniform="espacial_columnas")
        self.tab_espacial.rowconfigure(0, weight=1, minsize=520)

        self.lbl_base_espacial = self._crear_panel_imagen(self.tab_espacial, 0, 0, "Base binarizada")
        self.lbl_ruido = self._crear_panel_imagen(self.tab_espacial, 0, 1, "Ruido sal y pimienta")
        self.lbl_resultado_espacial = self._crear_panel_imagen(self.tab_espacial, 0, 2, "Imagen filtrada")

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
        for columna in range(3):
            self.tab_frecuencia.columnconfigure(columna, weight=1, uniform="frecuencia_columnas")
        self.tab_frecuencia.rowconfigure(0, weight=1, minsize=520)

        self.lbl_base_frecuencia = self._crear_panel_imagen(self.tab_frecuencia, 0, 0, "Base binarizada")
        self.lbl_espectro = self._crear_panel_imagen(self.tab_frecuencia, 0, 1, "Imagen espectro")
        self.lbl_resultado_frecuencia = self._crear_panel_imagen(self.tab_frecuencia, 0, 2, "Imagen reconstruida")

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

    def _crear_panel_imagen(self, padre, fila, columna, titulo):
        panel = ttk.Frame(padre, style="Panel.TFrame", padding=14)
        panel.grid(row=fila, column=columna, sticky="nsew", padx=6, pady=6)
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
            # Esta conversion solo asegura que la imagen cargada tenga canales RGB.
            # El procesamiento principal a gris se realiza manualmente despues.
            self.imagen_original = Image.open(ruta).convert("RGB")
            self.imagen_gris = convertir_rgb_a_gris_manual(self.imagen_original)
            self.imagen_normalizada = normalizar_histograma_manual(self.imagen_gris)
            self.imagen_binarizada = binarizar_manual(self.imagen_normalizada, UMBRAL_BINARIZACION)
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo cargar o preprocesar la imagen:\n{error}")
            return

        self._reiniciar_resultados_derivados()
        self._mostrar_preprocesamiento()
        self._mostrar_imagen_gris(self.lbl_base_espacial, self.imagen_binarizada, "base_espacial")
        self._mostrar_imagen_gris(self.lbl_base_frecuencia, self.imagen_binarizada, "base_frecuencia")

    def _mostrar_preprocesamiento(self):
        self._mostrar_imagen_pil(self.lbl_pre_original, self.imagen_original, "pre_original")
        self._mostrar_imagen_gris(self.lbl_pre_gris, self.imagen_gris, "pre_gris")
        self._mostrar_imagen_gris(self.lbl_pre_normalizada, self.imagen_normalizada, "pre_normalizada")
        self._mostrar_imagen_gris(self.lbl_pre_binarizada, self.imagen_binarizada, "pre_binarizada")

    def _reiniciar_resultados_derivados(self):
        self._cancelar_actualizacion_ruido_pendiente()
        self._cancelar_actualizacion_frecuencia_pendiente()
        self.imagen_con_ruido = None
        self.imagen_resultado_espacial = None
        self.imagen_frecuencia_base = None
        self.espectro_centrado = None
        self.espectro_visible = None
        self.imagen_resultado_frecuencia = None
        self._limpiar_etiqueta_imagen(self.lbl_ruido)
        self._limpiar_etiqueta_imagen(self.lbl_resultado_espacial)
        self._limpiar_etiqueta_imagen(self.lbl_espectro)
        self._limpiar_etiqueta_imagen(self.lbl_resultado_frecuencia)

    def aplicar_ruido(self):
        if self.imagen_binarizada is None:
            messagebox.showwarning("Advertencia", "Primero debe cargar una imagen.")
            return

        porcentaje = self.slider_ruido.get()
        self.imagen_con_ruido = agregar_ruido_sal_pimienta_manual(self.imagen_binarizada, porcentaje)
        self.imagen_resultado_espacial = None
        self._mostrar_imagen_gris(self.lbl_ruido, self.imagen_con_ruido, "ruido")
        self._limpiar_etiqueta_imagen(self.lbl_resultado_espacial)

    def aplicar_filtro(self):
        if self.imagen_binarizada is None:
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
        if self.imagen_binarizada is None:
            messagebox.showwarning("Advertencia", "Primero debe cargar una imagen.")
            return

        diametro = int(round(self.slider_diametro.get()))

        try:
            self.config(cursor="watch")
            self.update_idletasks()

            if self.espectro_centrado is None:
                self.imagen_frecuencia_base, self.espectro_centrado, self.espectro_visible = preparar_transformada_frecuencia(
                    self.imagen_binarizada,
                    tamano=TAMANO_FRECUENCIA,
                )
                self._mostrar_imagen_gris(self.lbl_base_frecuencia, self.imagen_frecuencia_base, "frecuencia_base")

            self._reconstruir_frecuencia_con_diametro(diametro)
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo procesar la frecuencia:\n{error}")
        finally:
            self.config(cursor="")

    def limpiar_resultados(self):
        self.limpiar_espacial()
        self.limpiar_frecuencia()

    def limpiar_espacial(self):
        self._cancelar_actualizacion_ruido_pendiente()
        self.imagen_con_ruido = None
        self.imagen_resultado_espacial = None
        self._limpiar_etiqueta_imagen(self.lbl_ruido)
        self._limpiar_etiqueta_imagen(self.lbl_resultado_espacial)
        if self.imagen_binarizada is not None:
            self._mostrar_imagen_gris(self.lbl_base_espacial, self.imagen_binarizada, "base_espacial")

    def limpiar_frecuencia(self):
        self._cancelar_actualizacion_frecuencia_pendiente()
        self.imagen_frecuencia_base = None
        self.espectro_centrado = None
        self.espectro_visible = None
        self.imagen_resultado_frecuencia = None
        self._limpiar_etiqueta_imagen(self.lbl_espectro)
        self._limpiar_etiqueta_imagen(self.lbl_resultado_frecuencia)
        if self.imagen_binarizada is not None:
            self._mostrar_imagen_gris(self.lbl_base_frecuencia, self.imagen_binarizada, "base_frecuencia")

    def _actualizar_valor_ruido(self, valor):
        self.valor_ruido.configure(text=f"{int(float(valor))} %")
        if self.imagen_con_ruido is not None:
            self._cancelar_actualizacion_ruido_pendiente()
            self.actualizacion_ruido_pendiente = self.after(250, self._reaplicar_ruido_desde_slider)

    def _reaplicar_ruido_desde_slider(self):
        self.actualizacion_ruido_pendiente = None
        if self.imagen_binarizada is not None:
            self.aplicar_ruido()

    def _actualizar_valor_diametro(self, valor):
        diametro = int(float(valor))
        self.valor_diametro.configure(text=f"{diametro} px")
        if self.espectro_centrado is not None:
            self._cancelar_actualizacion_frecuencia_pendiente()
            self.actualizacion_frecuencia_pendiente = self.after(
                300,
                lambda: self._reconstruir_frecuencia_con_diametro(diametro),
            )

    def _procesar_frecuencia_al_soltar(self, _evento):
        if self.espectro_centrado is not None:
            self._cancelar_actualizacion_frecuencia_pendiente()
            self.procesar_frecuencia()

    def _reconstruir_frecuencia_con_diametro(self, diametro):
        self.actualizacion_frecuencia_pendiente = None
        self._mostrar_espectro_con_diametro(diametro)
        self.imagen_resultado_frecuencia = reconstruir_desde_diametro(self.espectro_centrado, diametro)
        self._mostrar_imagen_gris(
            self.lbl_resultado_frecuencia,
            self.imagen_resultado_frecuencia,
            "resultado_frecuencia",
        )

    def _mostrar_espectro_con_diametro(self, diametro):
        espectro_mascara = obtener_espectro_con_mascara_visible(
            self.espectro_centrado,
            diametro,
            self.espectro_visible,
        )
        self._mostrar_imagen_gris(self.lbl_espectro, espectro_mascara, "espectro")

    def _cancelar_actualizacion_ruido_pendiente(self):
        if self.actualizacion_ruido_pendiente is not None:
            self.after_cancel(self.actualizacion_ruido_pendiente)
            self.actualizacion_ruido_pendiente = None

    def _cancelar_actualizacion_frecuencia_pendiente(self):
        if self.actualizacion_frecuencia_pendiente is not None:
            self.after_cancel(self.actualizacion_frecuencia_pendiente)
            self.actualizacion_frecuencia_pendiente = None

    def _mostrar_imagen_gris(self, etiqueta, arreglo, clave):
        # La conversion a RGB para presentacion no recupera los colores originales;
        # unicamente duplica el canal gris o binario en R, G y B para mostrarlo.
        imagen_rgb = convertir_gris_a_rgb(arreglo)
        imagen = arreglo_rgb_a_imagen_pil(imagen_rgb)
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
            max_alto = 320

        ancho, alto = imagen.size
        escala = min(max_ancho / ancho, max_alto / alto)
        nuevo_ancho = max(1, int(ancho * escala))
        nuevo_alto = max(1, int(alto * escala))
        return imagen.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)

    def _limpiar_etiqueta_imagen(self, etiqueta):
        etiqueta.configure(image="", text="Sin imagen")
