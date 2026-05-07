import math
import numpy as np

from logica.filtros_espaciales import agregar_padding_replicado_manual
from logica.utilidades import normalizar_a_uint8_manual


MASCARA_PASA_ALTO = np.array(
    [
        [-1, -1, -1],
        [-1, 8, -1],
        [-1, -1, -1],
    ],
    dtype=np.float64,
)

KERNEL_SOBEL_X = np.array(
    [
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1],
    ],
    dtype=np.float64,
)

KERNEL_SOBEL_Y = np.array(
    [
        [-1, -2, -1],
        [0, 0, 0],
        [1, 2, 1],
    ],
    dtype=np.float64,
)


def aplicar_mascara_3x3_manual(imagen_gris, mascara):
    alto, ancho = imagen_gris.shape
    padding = agregar_padding_replicado_manual(imagen_gris, radio=1)
    salida = np.zeros((alto, ancho), dtype=np.float64)

    for y in range(alto):
        for x in range(ancho):
            suma = 0.0
            for dy in range(3):
                for dx in range(3):
                    suma += float(padding[y + dy, x + dx]) * float(mascara[dy, dx])
            salida[y, x] = suma

    return salida


def pasa_alto_espacial_manual(imagen_gris):
    respuesta = aplicar_mascara_3x3_manual(imagen_gris, MASCARA_PASA_ALTO)
    return normalizar_a_uint8_manual(respuesta)


def sobel_manual(imagen_gris):
    _sobel_x, _sobel_y, magnitud = sobel_componentes_manual(imagen_gris)
    return magnitud


def sobel_componentes_manual(imagen_gris):
    alto, ancho = imagen_gris.shape
    padding = agregar_padding_replicado_manual(imagen_gris, radio=1)
    respuesta_x = np.zeros((alto, ancho), dtype=np.float64)
    respuesta_y = np.zeros((alto, ancho), dtype=np.float64)
    magnitud = np.zeros((alto, ancho), dtype=np.float64)

    for y in range(alto):
        for x in range(ancho):
            gx = 0.0
            gy = 0.0
            for dy in range(3):
                for dx in range(3):
                    valor = float(padding[y + dy, x + dx])
                    gx += valor * float(KERNEL_SOBEL_X[dy, dx])
                    gy += valor * float(KERNEL_SOBEL_Y[dy, dx])
            respuesta_x[y, x] = gx
            respuesta_y[y, x] = gy
            magnitud[y, x] = math.sqrt(gx * gx + gy * gy)

    return (
        normalizar_a_uint8_manual(np.abs(respuesta_x)),
        normalizar_a_uint8_manual(np.abs(respuesta_y)),
        normalizar_a_uint8_manual(magnitud),
    )
