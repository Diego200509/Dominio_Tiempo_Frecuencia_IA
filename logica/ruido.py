import random
import numpy as np


def agregar_ruido_sal_pimienta_manual(imagen_gris, porcentaje):
    alto, ancho = imagen_gris.shape
    salida = np.copy(imagen_gris)
    probabilidad = max(0.0, min(100.0, float(porcentaje))) / 100.0

    for y in range(alto):
        for x in range(ancho):
            azar = random.random()
            if azar < probabilidad / 2:
                salida[y, x] = 0
            elif azar < probabilidad:
                salida[y, x] = 255

    return salida.astype(np.uint8)
