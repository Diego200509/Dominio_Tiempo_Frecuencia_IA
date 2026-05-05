# Procesamiento Digital de Imagenes

Proyecto academico en Python para procesamiento digital de imagenes en:

- Preprocesamiento.
- Dominio espacial.
- Dominio de frecuencia.

La interfaz esta hecha con Tkinter y el codigo esta organizado separando la
interfaz de la logica de procesamiento.

## Objetivo

El programa permite cargar una imagen RGB desde el equipo y demostrar un flujo
completo de tratamiento de imagenes:

```text
RGB original
-> escala de grises
-> normalizacion de histograma
-> binarizacion
-> ruido sal y pimienta
-> filtros espaciales o procesamiento en frecuencia
```

Las imagenes de un canal se muestran en formato RGB duplicando el valor en los
tres canales:

```text
gris -> RGB = (gris, gris, gris)
binaria -> RGB = (valor, valor, valor)
```

Esto no recupera colores originales; solo permite presentar resultados en un
formato RGB visible en la interfaz.

El sistema procesa la imagen en RGB, escala de grises y binarizacion. Para la
presentacion final, las imagenes de un solo canal se convierten nuevamente a RGB
duplicando el valor del pixel en los tres canales, permitiendo visualizarlas
correctamente en la interfaz.

## Instalacion

Se recomienda crear un entorno virtual:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecucion

```bash
python main.py
```

Luego presiona **Cargar imagen** y selecciona cualquier archivo `.png`, `.jpg`,
`.jpeg`, `.bmp`, `.tif` o `.tiff`.

## Preprocesamiento

La primera pestaña muestra:

- Imagen original RGB.
- Imagen en escala de grises.
- Imagen con histograma normalizado.
- Imagen binarizada.
- Grafico comparativo del histograma original en grises y el histograma normalizado.

La conversion RGB a escala de grises se realiza manualmente pixel por pixel:

```text
gris = 0.299R + 0.587G + 0.114B
```

La normalizacion de histograma se implementa manualmente calculando minimo y
maximo de la imagen y llevando los valores al rango `0..255`.
Tambien se calcula manualmente una comparativa de histogramas contando cuantos
pixeles pertenecen a cada nivel de intensidad entre `0` y `255`.

La binarizacion se implementa manualmente con un umbral fijo de `128`:

```text
si valor >= 128 -> 255
si valor < 128  -> 0
```

## Dominio espacial

El dominio espacial usa como base la imagen ya procesada en background:

```text
RGB -> gris -> normalizacion -> binarizacion
```

Sobre esa imagen binarizada se agrega ruido sal y pimienta manualmente:

- Pimienta: pixeles cambiados a `0`.
- Sal: pixeles cambiados a `255`.

No se usa `imnoise` ni equivalentes automaticos.

Luego se aplica un filtro manual sobre la imagen con ruido:

- Filtro de media: recorre una ventana `3x3`, suma los 9 valores y divide para 9.
- Filtro de mediana: ordena los 9 valores de la ventana y toma el central.
- Filtro de moda: cuenta frecuencias de los 9 valores y toma el mas repetido.

El padding se realiza manualmente por replicacion de bordes.

## Dominio de frecuencia

El dominio de frecuencia tambien usa como base la imagen procesada:

```text
RGB -> gris -> normalizacion -> binarizacion
```

El flujo aplicado es:

```text
imagen base binarizada
-> Fourier
-> centrar espectro
-> mascara circular central
-> espectro centrado * mascara
-> descentrar espectro
-> transformada inversa
-> parte real
-> normalizacion 0..255
-> imagen reconstruida
```

La interfaz principal usa `numpy.fft.fft2` y `numpy.fft.ifft2` para calcular
Fourier con buena calidad visual y tiempos razonables. No se usa OpenCV ni
`cv2.dft`.

Tambien se conserva una DFT/IDFT manual separable por filas y columnas en
`logica/frecuencia.py` como referencia didactica para explicar el procedimiento.

La mascara circular central se calcula manualmente:

```text
distancia = sqrt((x - centro_x)^2 + (y - centro_y)^2)
si distancia <= radio -> 1
si distancia > radio  -> 0
```

El radio es:

```text
radio = diametro / 2
```

El diametro se controla con un slider. Si el diametro es pequeno, se conservan
principalmente bajas frecuencias y la imagen se ve mas suavizada. Si el
diametro aumenta, se conservan mas componentes y se recuperan detalles y bordes.

El espectro se visualiza con magnitud logaritmica `log(1 + magnitud)` y
normalizacion manual a `0..255`. La interfaz muestra un circulo blanco sobre el
espectro para indicar que parte se conserva.

## Restricciones cumplidas

No se usan funciones automaticas para los calculos principales:

- No `cv2.cvtColor`.
- No `cv2.equalizeHist`.
- No `cv2.threshold`.
- No `cv2.blur`.
- No `cv2.medianBlur`.
- No `cv2.GaussianBlur`.
- No `cv2.filter2D`.
- No `scipy.ndimage`.
- No `skimage.filters`.
- No `imnoise`.

Las librerias se usan para:

- Cargar imagenes con Pillow.
- Mostrar imagenes con Pillow/Tkinter.
- Crear la interfaz con Tkinter.
- Manejo basico de arreglos con NumPy.
- Fourier optimizado con `numpy.fft` en la ruta principal de frecuencia.

## Estructura

```text
proyecto_procesamiento_imagenes/
|
|-- main.py
|-- requirements.txt
|-- README.md
|
|-- interfaz/
|   |-- __init__.py
|   `-- ventana_principal.py
|
|-- logica/
|   |-- __init__.py
|   |-- conversion.py
|   |-- histograma.py
|   |-- binarizacion.py
|   |-- ruido.py
|   |-- filtros_espaciales.py
|   |-- frecuencia.py
|   `-- utilidades.py
|
`-- recursos/
    `-- imagenes/
```

## Funciones implementadas manualmente

- Conversion RGB a escala de grises.
- Normalizacion de histograma por minimo y maximo.
- Calculo manual de histogramas para la comparativa visual.
- Binarizacion por umbral.
- Conversion de gris/binaria a RGB duplicando canales.
- Ruido sal y pimienta.
- Padding por replicacion.
- Filtro de media `3x3`.
- Filtro de mediana `3x3`.
- Filtro de moda `3x3`.
- Redimensionamiento por vecino mas cercano e interpolacion bilineal manual.
- DFT 1D, DFT 2D e IDFT 2D manuales como referencia didactica.
- Centrado y descentrado manual del espectro.
- Mascara circular central.
- Aplicacion manual de la mascara en frecuencia.
- Normalizacion manual de espectro y reconstruccion.
