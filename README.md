# Procesamiento Digital de Imagenes

Proyecto academico en Python para demostrar procesamiento digital de imagenes
en preprocesamiento, dominio espacial/tiempo y dominio de frecuencia.

La interfaz esta hecha con Tkinter. Pillow se usa para cargar y mostrar imagenes.
NumPy se usa como apoyo matematico y para manejar matrices, pero la logica
principal de los filtros, binarizacion, ruido, bordes y deteccion se implementa
manualmente.

## Flujo Corregido

El flujo fue corregido para que los filtros trabajen sobre la imagen en escala
de grises normalizada, conservando la informacion de intensidad. La
binarizacion ya no se usa como entrada de los filtros; ahora se aplica al final.

```text
RGB original
-> conversion manual a escala de grises
-> normalizacion manual de intensidades 0..255
-> tratamiento de ruido o filtro de frecuencia
-> acentuado de bordes
-> gradiente con Sobel
-> binarizacion final
-> deteccion del objeto
-> bounding box final
```

## Instalacion

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecucion

```bash
python main.py
```

Luego presiona **Cargar imagen** y selecciona un archivo `.png`, `.jpg`,
`.jpeg`, `.bmp`, `.tif` o `.tiff`.

## Preprocesamiento Inicial

La primera pestana muestra:

- Imagen original RGB.
- Imagen en escala de grises.
- Imagen normalizada.
- Comparativa de histogramas.

La conversion RGB a gris se calcula pixel por pixel:

```text
gris = 0.299R + 0.587G + 0.114B
```

La normalizacion se implementa manualmente calculando minimo y maximo:

```text
valor_normalizado = (valor - minimo) * 255 / (maximo - minimo)
```

La imagen normalizada es la base para el dominio espacial y para el dominio de
frecuencia.

## Dominio Espacial / Tiempo

El flujo espacial es:

```text
imagen gris normalizada
-> ruido sal y pimienta
-> filtro espacial 3x3
-> pasa-alto espacial
-> Sobel
-> binarizacion final
-> bounding box
```

El ruido sal y pimienta se agrega manualmente sobre la imagen gris normalizada.
El control de ruido usa un valor entre `0` y `0.40` para evitar degradar
excesivamente la imagen:

- Pimienta: algunos pixeles cambian a `0`.
- Sal: algunos pixeles cambian a `255`.

Los filtros espaciales se aplican recorriendo ventanas `3x3` con padding por
replicacion de bordes:

- Media: suma los 9 valores y divide para 9.
- Mediana: ordena los 9 valores y toma el central.
- Moda: cuenta frecuencias y toma el valor mas repetido.

Despues del suavizado se aplica un pasa-alto espacial manual con la mascara:

```text
-1 -1 -1
-1  8 -1
-1 -1 -1
```

La salida del pasa-alto se normaliza manualmente a `0..255`.

## Sobel Manual

Sobel se aplica sobre una imagen procesada en escala de grises, no sobre una
imagen binaria.

Kernel X:

```text
-1  0  1
-2  0  2
-1  0  1
```

Kernel Y:

```text
-1 -2 -1
 0  0  0
 1  2  1
```

Para cada pixel se calcula:

```text
G = sqrt(Gx^2 + Gy^2)
```

La interfaz muestra tres resultados para que el proceso sea mas claro:

- `Sobel X`: valor absoluto de la respuesta del kernel horizontal.
- `Sobel Y`: valor absoluto de la respuesta del kernel vertical.
- `Magnitud Sobel`: combinacion `sqrt(Gx^2 + Gy^2)`.

Para visualizar `Sobel X` y `Sobel Y` se usa valor absoluto porque las
respuestas originales pueden ser positivas o negativas. Cada resultado se
normaliza manualmente a `0..255`.

## Dominio de Frecuencia

El dominio de frecuencia tambien parte de la imagen gris normalizada:

```text
imagen gris normalizada
-> Fourier
-> centrar espectro
-> mascara circular pasa-bajo o pasa-alto
-> transformada inversa
-> reconstruccion en escala de grises
-> Sobel
-> binarizacion final
-> bounding box
```

Se permite y se usa `numpy.fft` para la transformada:

- `np.fft.fft2`
- `np.fft.ifft2`

El centrado/descentrado y las mascaras se calculan manualmente en la logica del
proyecto.

La mascara circular se calcula con:

```text
distancia = sqrt((x - centro_x)^2 + (y - centro_y)^2)
```

Pasa-bajo:

```text
si distancia <= radio -> 1
si distancia > radio  -> 0
```

Pasa-alto:

```text
si distancia <= radio -> 0
si distancia > radio  -> 1
```

El espectro se visualiza con magnitud logaritmica:

```text
espectro = log(1 + abs(F))
```

Luego se normaliza manualmente al rango `0..255`. La interfaz tambien muestra
la mascara circular aplicada.

## Binarizacion Final

La binarizacion se ejecuta al final del flujo, despues del filtrado y de Sobel.
El umbral se controla con un slider:

```text
si valor >= umbral -> 255
si valor < umbral  -> 0
```

## Bounding Box

El bounding box se calcula manualmente agrupando los componentes blancos
significativos de la imagen binaria final. Esto permite rodear objetos formados
por varias partes separadas, como letras, y descartar puntos pequenos de ruido:

- `x_min`
- `x_max`
- `y_min`
- `y_max`

Luego se dibuja una caja roja sobre la imagen procesada para visualizar el
objeto detectado.

## Restricciones

No se usan funciones automaticas que resuelvan directamente las etapas
principales:

- No `cv2.cvtColor`.
- No `cv2.threshold`.
- No `cv2.blur`.
- No `cv2.medianBlur`.
- No `cv2.GaussianBlur`.
- No `cv2.filter2D`.
- No `scipy.ndimage`.
- No `skimage.filters`.
- No `imnoise`.

## Estructura

```text
main.py
requirements.txt
README.md

interfaz/
    __init__.py
    ventana_principal.py

logica/
    __init__.py
    binarizacion.py
    bordes.py
    bounding_box.py
    conversion.py
    filtros_espaciales.py
    frecuencia.py
    histograma.py
    ruido.py
    utilidades.py

recursos/
    imagenes/
```

## Funciones Manuales Implementadas

- Conversion RGB a escala de grises.
- Normalizacion de intensidades por minimo y maximo.
- Calculo de histogramas.
- Ruido sal y pimienta.
- Padding por replicacion.
- Filtros de media, mediana y moda con ventana `3x3`.
- Pasa-alto espacial con mascara `3x3`.
- Sobel X, Sobel Y y magnitud con kernels manuales.
- Binarizacion por umbral.
- Mascara circular pasa-bajo en frecuencia.
- Mascara circular pasa-alto en frecuencia.
- Visualizacion del espectro con la mascara aplicada.
- Aplicacion manual de mascara al espectro.
- Normalizacion manual de espectro y reconstruccion.
- Calculo manual del bounding box.
