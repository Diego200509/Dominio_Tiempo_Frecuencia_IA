import numpy as np


def normalizar_histograma_manual(imagen_gris):
    """
    Normaliza el contraste llevando los valores de la imagen al rango 0..255.
    No usa cv2.equalizeHist; calcula minimo y maximo recorriendo pixeles.
    """
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
