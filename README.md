# Procesamiento Digital de Imagenes

Proyecto academico en Python para mostrar procesamiento de imagenes en el
dominio espacial y en el dominio de frecuencia, con una interfaz grafica clara
hecha en Tkinter.

## Objetivo

El programa permite cargar una imagen RGB desde el equipo, mostrarla en la
interfaz y trabajar internamente con una version en escala de grises calculada
manualmente con:

```text
gris = 0.299R + 0.587G + 0.114B
```

La conversion no usa `cv2.cvtColor`; se recorre cada pixel y se calcula el
valor gris con la formula anterior.

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

Desde la interfaz se debe presionar **Cargar imagen** y seleccionar cualquier
archivo `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tif` o `.tiff`.

## Dominio espacial

El dominio espacial trabaja directamente sobre los pixeles de la imagen.
Primero se convierte la imagen RGB a escala de grises de forma manual. Luego
se puede agregar ruido sal y pimienta usando el slider de porcentaje.

El ruido sal y pimienta se implementa modificando pixeles aleatorios:

- Pimienta: el pixel se cambia a 0.
- Sal: el pixel se cambia a 255.

Despues se puede aplicar uno de estos filtros, todos con ventana 3x3:

- Filtro de media: suma los 9 vecinos y divide para 9.
- Filtro de mediana: ordena los 9 valores y toma el valor central.
- Filtro de moda: cuenta frecuencias y toma el valor mas repetido.

Tambien se implementa manualmente el padding por replicacion de bordes. No se
usan `cv2.blur`, `cv2.medianBlur`, `cv2.GaussianBlur`, `cv2.filter2D`,
`scipy.ndimage` ni `skimage.filters`.

## Dominio de frecuencia

El dominio de frecuencia analiza la imagen mediante la Transformada Discreta
de Fourier. Para mejorar la calidad visual, la imagen se prepara a 512x512
con interpolacion bilineal manual antes de calcular Fourier.

La transformada tiene dos rutas en `logica/frecuencia.py`:

- Ruta optimizada principal: usa `numpy.fft.fft2` y `numpy.fft.ifft2` para
  obtener mejor calidad y velocidad con imagenes mas grandes.
- Ruta manual didactica: conserva una DFT/IDFT propia separable por filas y
  columnas, util para explicar el procedimiento en la defensa academica.

En la version manual se usa el siguiente proceso:

1. DFT manual por filas.
2. DFT manual por columnas.
3. Desplazamiento manual del espectro hacia el centro.
4. Visualizacion del espectro de magnitud con escala logaritmica.
5. Mascara circular central creada pixel por pixel.
6. IDFT manual para reconstruir la imagen.

El circulo central conserva principalmente bajas frecuencias. Si el diametro
es pequeno, la imagen reconstruida se ve mas suavizada o borrosa. Al aumentar
el diametro, se conservan mas componentes frecuenciales, incluyendo detalles y
bordes.

En la interfaz, el panel del espectro muestra la mascara circular actual: la
zona dentro del circulo queda resaltada, la zona externa se oscurece y el borde
blanco indica el diametro seleccionado. Asi se puede observar visualmente que
parte del espectro se conserva, de forma similar a una mascara pasa bajo ideal
en MATLAB.

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
- Ruido sal y pimienta.
- Padding por replicacion.
- Filtro de media 3x3.
- Filtro de mediana 3x3.
- Filtro de moda 3x3.
- Redimensionamiento por vecino mas cercano e interpolacion bilineal manual.
- DFT 1D, DFT 2D e IDFT 2D manuales como referencia didactica.
- DFT 2D e IDFT 2D optimizadas con `numpy.fft` para la interfaz principal.
- Centrando del espectro.
- Mascara circular central.
- Visualizacion del espectro con mascara circular resaltada.
- Aplicacion de la mascara en frecuencia.
