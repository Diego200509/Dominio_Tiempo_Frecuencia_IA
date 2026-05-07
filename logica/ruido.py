import random
import numpy as np


def agregar_ruido_sal_pimienta_manual(imagen_gris, nivel_ruido):
    alto, ancho = imagen_gris.shape
    salida = np.copy(imagen_gris)
    valor = float(nivel_ruido)
    if valor > 1.0:
        probabilidad = max(0.0, min(100.0, valor)) / 100.0
    else:
        probabilidad = max(0.0, min(1.0, valor))

    for y in range(alto):
        for x in range(ancho):
            azar = random.random()
            if azar < probabilidad / 2:
                salida[y, x] = 0
            elif azar < probabilidad:
                salida[y, x] = 255

    return salida.astype(np.uint8)
