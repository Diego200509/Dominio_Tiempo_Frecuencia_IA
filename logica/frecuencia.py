import math
import numpy as np

from logica.conversion import preparar_gris_para_frecuencia
from logica.utilidades import normalizar_a_uint8_manual, normalizar_reconstruccion_a_uint8_manual


def dft_1d_manual(vector, inversa=False):
    n = len(vector)
    salida = np.zeros(n, dtype=np.complex128)
    signo = 1 if inversa else -1

    for k in range(n):
        suma = 0 + 0j
        for indice in range(n):
            angulo = signo * 2 * math.pi * k * indice / n
            factor = complex(math.cos(angulo), math.sin(angulo))
            suma += vector[indice] * factor
        if inversa:
            suma /= n
        salida[k] = suma

    return salida


def dft_2d_manual(imagen_gris):
    alto, ancho = imagen_gris.shape
    temporal = np.zeros((alto, ancho), dtype=np.complex128)
    salida = np.zeros((alto, ancho), dtype=np.complex128)

    for y in range(alto):
        temporal[y, :] = dft_1d_manual(imagen_gris[y, :].astype(np.complex128), inversa=False)

    for x in range(ancho):
        salida[:, x] = dft_1d_manual(temporal[:, x], inversa=False)

    return salida


def dft_2d_numpy(imagen_gris):
    return np.fft.fft2(imagen_gris.astype(np.float64))


def idft_2d_manual(espectro):
    alto, ancho = espectro.shape
    temporal = np.zeros((alto, ancho), dtype=np.complex128)
    salida = np.zeros((alto, ancho), dtype=np.complex128)

    for y in range(alto):
        temporal[y, :] = dft_1d_manual(espectro[y, :], inversa=True)

    for x in range(ancho):
        salida[:, x] = dft_1d_manual(temporal[:, x], inversa=True)

    return salida


def idft_2d_numpy(espectro):
    return np.fft.ifft2(espectro)


def centrar_espectro_manual(espectro):
    alto, ancho = espectro.shape
    salida = np.zeros_like(espectro)

    for y in range(alto):
        for x in range(ancho):
            nuevo_y = (y + alto // 2) % alto
            nuevo_x = (x + ancho // 2) % ancho
            salida[nuevo_y, nuevo_x] = espectro[y, x]

    return salida


def descentrar_espectro_manual(espectro_centrado):
    alto, ancho = espectro_centrado.shape
    salida = np.zeros_like(espectro_centrado)
    desplazamiento_y = (alto + 1) // 2
    desplazamiento_x = (ancho + 1) // 2

    for y in range(alto):
        for x in range(ancho):
            nuevo_y = (y + desplazamiento_y) % alto
            nuevo_x = (x + desplazamiento_x) % ancho
            salida[nuevo_y, nuevo_x] = espectro_centrado[y, x]

    return salida


def calcular_espectro_magnitud_manual(espectro_centrado):
    alto, ancho = espectro_centrado.shape
    magnitud = np.zeros((alto, ancho), dtype=np.float64)

    for y in range(alto):
        for x in range(ancho):
            valor = abs(espectro_centrado[y, x])
            magnitud[y, x] = math.log(1 + valor)

    return normalizar_a_uint8_manual(magnitud)


def dibujar_circulo_en_espectro_manual(espectro_visible, diametro):
    alto, ancho = espectro_visible.shape
    centro_y = alto // 2
    centro_x = ancho // 2
    radio = max(1, float(diametro) / 2.0)
    salida = np.zeros((alto, ancho), dtype=np.uint8)

    for y in range(alto):
        for x in range(ancho):
            distancia = math.sqrt((x - centro_x) ** 2 + (y - centro_y) ** 2)
            valor = int(espectro_visible[y, x])

            if distancia <= radio:
                salida[y, x] = valor
            else:
                salida[y, x] = int(valor * 0.25)

            if abs(distancia - radio) <= 1.2:
                salida[y, x] = 255

    return salida


def crear_mascara_circular_manual(alto, ancho, diametro):
    centro_y = alto // 2
    centro_x = ancho // 2
    radio = max(1, float(diametro) / 2.0)
    mascara = np.zeros((alto, ancho), dtype=np.float64)

    for y in range(alto):
        for x in range(ancho):
            distancia = math.sqrt((x - centro_x) ** 2 + (y - centro_y) ** 2)
            if distancia <= radio:
                mascara[y, x] = 1.0
            else:
                mascara[y, x] = 0.0

    return mascara


def aplicar_mascara_manual(espectro_centrado, mascara):
    alto, ancho = espectro_centrado.shape
    salida = np.zeros_like(espectro_centrado)

    for y in range(alto):
        for x in range(ancho):
            salida[y, x] = espectro_centrado[y, x] * mascara[y, x]

    return salida


def preparar_transformada_frecuencia(imagen_gris, tamano=1024, usar_numpy_fft=True):
    imagen_pequena = preparar_gris_para_frecuencia(imagen_gris, tamano=tamano)

    if usar_numpy_fft:
        espectro = dft_2d_numpy(imagen_pequena)
    else:
        espectro = dft_2d_manual(imagen_pequena)

    espectro_centrado = centrar_espectro_manual(espectro)

    espectro_visible = calcular_espectro_magnitud_manual(espectro_centrado)
    return imagen_pequena, espectro_centrado, espectro_visible


def reconstruir_desde_diametro(espectro_centrado, diametro, usar_numpy_fft=True):
    alto, ancho = espectro_centrado.shape

    mascara = crear_mascara_circular_manual(alto, ancho, diametro)

    espectro_filtrado = aplicar_mascara_manual(espectro_centrado, mascara)

    espectro_sin_centrar = descentrar_espectro_manual(espectro_filtrado)

    if usar_numpy_fft:
        reconstruida_compleja = idft_2d_numpy(espectro_sin_centrar)
    else:
        reconstruida_compleja = idft_2d_manual(espectro_sin_centrar)

    reconstruida_real = np.zeros((alto, ancho), dtype=np.float64)

    for y in range(alto):
        for x in range(ancho):
            reconstruida_real[y, x] = reconstruida_compleja[y, x].real

    return normalizar_reconstruccion_a_uint8_manual(reconstruida_real)


def obtener_espectro_con_mascara_visible(espectro_centrado, diametro, espectro_visible=None):
    if espectro_visible is None:
        espectro_visible = calcular_espectro_magnitud_manual(espectro_centrado)
    return dibujar_circulo_en_espectro_manual(espectro_visible, diametro)
