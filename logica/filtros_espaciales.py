import numpy as np


def agregar_padding_replicado_manual(imagen_gris, radio=1):
    """
    Agrega padding por replicacion de bordes.
    Para una ventana 3x3 se usa radio=1.
    """
    alto, ancho = imagen_gris.shape
    salida = np.zeros((alto + 2 * radio, ancho + 2 * radio), dtype=np.uint8)

    for y in range(alto + 2 * radio):
        origen_y = y - radio
        if origen_y < 0:
            origen_y = 0
        if origen_y >= alto:
            origen_y = alto - 1

        for x in range(ancho + 2 * radio):
            origen_x = x - radio
            if origen_x < 0:
                origen_x = 0
            if origen_x >= ancho:
                origen_x = ancho - 1
            salida[y, x] = imagen_gris[origen_y, origen_x]

    return salida


def obtener_ventana_3x3(imagen_con_padding, y, x):
    valores = []
    for dy in range(3):
        for dx in range(3):
            valores.append(int(imagen_con_padding[y + dy, x + dx]))
    return valores


def filtro_media_manual(imagen_gris):
    alto, ancho = imagen_gris.shape
    padding = agregar_padding_replicado_manual(imagen_gris, radio=1)
    salida = np.zeros((alto, ancho), dtype=np.uint8)

    for y in range(alto):
        for x in range(ancho):
            suma = 0
            for dy in range(3):
                for dx in range(3):
                    suma += int(padding[y + dy, x + dx])
            salida[y, x] = int(round(suma / 9))

    return salida


def filtro_mediana_manual(imagen_gris):
    alto, ancho = imagen_gris.shape
    padding = agregar_padding_replicado_manual(imagen_gris, radio=1)
    salida = np.zeros((alto, ancho), dtype=np.uint8)

    for y in range(alto):
        for x in range(ancho):
            valores = obtener_ventana_3x3(padding, y, x)
            valores_ordenados = sorted(valores)
            salida[y, x] = valores_ordenados[4]

    return salida


def filtro_moda_manual(imagen_gris):
    alto, ancho = imagen_gris.shape
    padding = agregar_padding_replicado_manual(imagen_gris, radio=1)
    salida = np.zeros((alto, ancho), dtype=np.uint8)

    for y in range(alto):
        for x in range(ancho):
            valores = obtener_ventana_3x3(padding, y, x)
            frecuencias = {}

            for valor in valores:
                if valor not in frecuencias:
                    frecuencias[valor] = 0
                frecuencias[valor] += 1

            mejor_valor = valores[4]
            mejor_frecuencia = -1
            for valor in valores:
                frecuencia = frecuencias[valor]
                if frecuencia > mejor_frecuencia:
                    mejor_valor = valor
                    mejor_frecuencia = frecuencia

            salida[y, x] = mejor_valor

    return salida


def aplicar_filtro_manual(imagen_gris, nombre_filtro):
    if nombre_filtro == "Filtro de media":
        return filtro_media_manual(imagen_gris)
    if nombre_filtro == "Filtro de mediana":
        return filtro_mediana_manual(imagen_gris)
    if nombre_filtro == "Filtro de moda":
        return filtro_moda_manual(imagen_gris)
    raise ValueError("Filtro no reconocido")
