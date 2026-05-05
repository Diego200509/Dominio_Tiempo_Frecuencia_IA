import numpy as np
from PIL import Image


def convertir_rgb_a_gris_manual(imagen_rgb):
    """
    Convierte una imagen RGB a escala de grises usando la formula indicada:
    gris = 0.299R + 0.587G + 0.114B

    La conversion se hace recorriendo pixel por pixel para que el proceso sea
    claro y defendible academicamente.
    """
    imagen_rgb = imagen_rgb.convert("RGB")
    datos = np.array(imagen_rgb, dtype=np.uint8)
    alto, ancho, _ = datos.shape
    gris = np.zeros((alto, ancho), dtype=np.uint8)

    for y in range(alto):
        for x in range(ancho):
            r = int(datos[y, x, 0])
            g = int(datos[y, x, 1])
            b = int(datos[y, x, 2])
            valor = int(round(0.299 * r + 0.587 * g + 0.114 * b))
            gris[y, x] = max(0, min(255, valor))

    return gris


def redimensionar_gris_vecino_manual(imagen_gris, nuevo_ancho, nuevo_alto):
    """
    Redimensiona una imagen en escala de grises con vecino mas cercano.
    Se implementa manualmente para evitar filtros automaticos de librerias.
    """
    alto, ancho = imagen_gris.shape
    salida = np.zeros((nuevo_alto, nuevo_ancho), dtype=np.uint8)

    for y in range(nuevo_alto):
        origen_y = int(y * alto / nuevo_alto)
        if origen_y >= alto:
            origen_y = alto - 1
        for x in range(nuevo_ancho):
            origen_x = int(x * ancho / nuevo_ancho)
            if origen_x >= ancho:
                origen_x = ancho - 1
            salida[y, x] = imagen_gris[origen_y, origen_x]

    return salida


def redimensionar_gris_bilineal_manual(imagen_gris, nuevo_ancho, nuevo_alto):
    """
    Redimensiona una imagen en escala de grises con interpolacion bilineal.
    Se calcula manualmente para mejorar la calidad frente al vecino mas cercano.
    """
    alto, ancho = imagen_gris.shape
    salida = np.zeros((nuevo_alto, nuevo_ancho), dtype=np.uint8)

    if nuevo_ancho == 1:
        escala_x = 0
    else:
        escala_x = (ancho - 1) / (nuevo_ancho - 1)

    if nuevo_alto == 1:
        escala_y = 0
    else:
        escala_y = (alto - 1) / (nuevo_alto - 1)

    for y in range(nuevo_alto):
        origen_y = y * escala_y
        y0 = int(origen_y)
        y1 = min(y0 + 1, alto - 1)
        peso_y = origen_y - y0

        for x in range(nuevo_ancho):
            origen_x = x * escala_x
            x0 = int(origen_x)
            x1 = min(x0 + 1, ancho - 1)
            peso_x = origen_x - x0

            arriba = (1 - peso_x) * float(imagen_gris[y0, x0]) + peso_x * float(imagen_gris[y0, x1])
            abajo = (1 - peso_x) * float(imagen_gris[y1, x0]) + peso_x * float(imagen_gris[y1, x1])
            valor = (1 - peso_y) * arriba + peso_y * abajo
            salida[y, x] = max(0, min(255, int(round(valor))))

    return salida


def preparar_gris_para_frecuencia(imagen_gris, tamano=512):
    """
    Genera una version cuadrada para el dominio de frecuencia.
    Usa interpolacion bilineal manual para evitar una vista pixelada.
    """
    return redimensionar_gris_bilineal_manual(imagen_gris, tamano, tamano)


def arreglo_gris_a_imagen_pil(imagen_gris):
    return Image.fromarray(imagen_gris.astype(np.uint8), mode="L")
