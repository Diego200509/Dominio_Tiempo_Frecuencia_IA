import numpy as np


def limitar_uint8(valor):
    return max(0, min(255, int(round(valor))))


def normalizar_a_uint8_manual(imagen):
    """
    Escala cualquier arreglo numerico al rango 0..255 recorriendo sus valores.
    Se usa para visualizar espectros de magnitud.
    """
    alto, ancho = imagen.shape
    minimo = float(imagen[0, 0])
    maximo = float(imagen[0, 0])

    for y in range(alto):
        for x in range(ancho):
            valor = float(imagen[y, x])
            if valor < minimo:
                minimo = valor
            if valor > maximo:
                maximo = valor

    salida = np.zeros((alto, ancho), dtype=np.uint8)
    rango = maximo - minimo
    if rango == 0:
        valor_constante = limitar_uint8(minimo)
        for y in range(alto):
            for x in range(ancho):
                salida[y, x] = valor_constante
        return salida

    for y in range(alto):
        for x in range(ancho):
            salida[y, x] = limitar_uint8((float(imagen[y, x]) - minimo) * 255 / rango)

    return salida


def normalizar_reconstruccion_a_uint8_manual(imagen):
    """
    Normaliza una imagen reconstruida al rango 0..255.
    Si el rango es casi constante, conserva ese valor en vez de volverla negra.
    """
    alto, ancho = imagen.shape
    minimo = float(imagen[0, 0])
    maximo = float(imagen[0, 0])

    for y in range(alto):
        for x in range(ancho):
            valor = float(imagen[y, x])
            if valor < minimo:
                minimo = valor
            if valor > maximo:
                maximo = valor

    salida = np.zeros((alto, ancho), dtype=np.uint8)
    rango = maximo - minimo

    if rango < 1e-9:
        valor_constante = limitar_uint8(minimo)
        for y in range(alto):
            for x in range(ancho):
                salida[y, x] = valor_constante
        return salida

    for y in range(alto):
        for x in range(ancho):
            valor_normalizado = (float(imagen[y, x]) - minimo) * 255 / rango
            salida[y, x] = limitar_uint8(valor_normalizado)

    return salida


def recortar_a_uint8_manual(imagen):
    alto, ancho = imagen.shape
    salida = np.zeros((alto, ancho), dtype=np.uint8)

    for y in range(alto):
        for x in range(ancho):
            salida[y, x] = limitar_uint8(float(imagen[y, x]))

    return salida
