import numpy as np
from PIL import Image


def convertir_rgb_a_gris_manual(imagen_rgb):
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


def convertir_gris_a_rgb(imagen_gris):
    alto, ancho = imagen_gris.shape
    salida = np.zeros((alto, ancho, 3), dtype=np.uint8)

    for y in range(alto):
        for x in range(ancho):
            valor = int(imagen_gris[y, x])
            salida[y, x, 0] = valor
            salida[y, x, 1] = valor
            salida[y, x, 2] = valor

    return salida


def arreglo_rgb_a_imagen_pil(imagen_rgb):
    return Image.fromarray(imagen_rgb.astype(np.uint8), mode="RGB")


def arreglo_gris_a_imagen_pil(imagen_gris):
    return Image.fromarray(imagen_gris.astype(np.uint8), mode="L")
