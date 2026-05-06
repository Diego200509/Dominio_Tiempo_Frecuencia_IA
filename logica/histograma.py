import numpy as np


def normalizar_histograma_manual(imagen_gris):
    alto, ancho = imagen_gris.shape
    minimo = int(imagen_gris[0, 0])
    maximo = int(imagen_gris[0, 0])

    for y in range(alto):
        for x in range(ancho):
            valor = int(imagen_gris[y, x])
            if valor < minimo:
                minimo = valor
            if valor > maximo:
                maximo = valor

    salida = np.zeros((alto, ancho), dtype=np.uint8)
    rango = maximo - minimo

    if rango == 0:
        for y in range(alto):
            for x in range(ancho):
                salida[y, x] = imagen_gris[y, x]
        return salida

    for y in range(alto):
        for x in range(ancho):
            valor = (int(imagen_gris[y, x]) - minimo) * 255 / rango
            salida[y, x] = max(0, min(255, int(round(valor))))

    return salida


def calcular_histograma_manual(imagen_gris):
    alto, ancho = imagen_gris.shape
    histograma = [0] * 256

    for y in range(alto):
        for x in range(ancho):
            valor = int(imagen_gris[y, x])
            histograma[valor] += 1

    return histograma
