import numpy as np


def binarizar_manual(imagen_gris, umbral=128):
    alto, ancho = imagen_gris.shape
    salida = np.zeros((alto, ancho), dtype=np.uint8)

    for y in range(alto):
        for x in range(ancho):
            if int(imagen_gris[y, x]) >= umbral:
                salida[y, x] = 255
            else:
                salida[y, x] = 0

    return salida
