import numpy as np


def agregar_padding_replicado_manual(imagen_gris, radio=1):
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


def obtener_ventana_manual(imagen_con_padding, y, x, tamano_ventana=3):
    valores = []
    for dy in range(tamano_ventana):
        for dx in range(tamano_ventana):
            valores.append(int(imagen_con_padding[y + dy, x + dx]))
    return valores


def validar_tamano_ventana(tamano_ventana):
    tamano = int(tamano_ventana)
    if tamano not in (3, 5, 7, 11):
        raise ValueError("El tamano de ventana debe ser 3, 5, 7 u 11")
    return tamano


def filtro_media_manual(imagen_gris, tamano_ventana=3):
    tamano_ventana = validar_tamano_ventana(tamano_ventana)
    radio = tamano_ventana // 2
    alto, ancho = imagen_gris.shape
    padding = agregar_padding_replicado_manual(imagen_gris, radio=radio)
    salida = np.zeros((alto, ancho), dtype=np.uint8)
    cantidad_valores = tamano_ventana * tamano_ventana

    for y in range(alto):
        for x in range(ancho):
            suma = 0
            for dy in range(tamano_ventana):
                for dx in range(tamano_ventana):
                    suma += int(padding[y + dy, x + dx])
            salida[y, x] = int(round(suma / cantidad_valores))

    return salida


def filtro_mediana_manual(imagen_gris, tamano_ventana=3):
    tamano_ventana = validar_tamano_ventana(tamano_ventana)
    radio = tamano_ventana // 2
    alto, ancho = imagen_gris.shape
    padding = agregar_padding_replicado_manual(imagen_gris, radio=radio)
    salida = np.zeros((alto, ancho), dtype=np.uint8)
    indice_central = (tamano_ventana * tamano_ventana) // 2

    for y in range(alto):
        for x in range(ancho):
            valores = obtener_ventana_manual(padding, y, x, tamano_ventana)
            valores_ordenados = sorted(valores)
            salida[y, x] = valores_ordenados[indice_central]

    return salida


def filtro_moda_manual(imagen_gris, tamano_ventana=3):
    tamano_ventana = validar_tamano_ventana(tamano_ventana)
    radio = tamano_ventana // 2
    alto, ancho = imagen_gris.shape
    padding = agregar_padding_replicado_manual(imagen_gris, radio=radio)
    salida = np.zeros((alto, ancho), dtype=np.uint8)
    indice_central = (tamano_ventana * tamano_ventana) // 2

    for y in range(alto):
        for x in range(ancho):
            valores = obtener_ventana_manual(padding, y, x, tamano_ventana)
            frecuencias = {}

            for valor in valores:
                if valor not in frecuencias:
                    frecuencias[valor] = 0
                frecuencias[valor] += 1

            mejor_valor = valores[indice_central]
            mejor_frecuencia = -1
            for valor in valores:
                frecuencia = frecuencias[valor]
                if frecuencia > mejor_frecuencia:
                    mejor_valor = valor
                    mejor_frecuencia = frecuencia

            salida[y, x] = mejor_valor

    return salida


def aplicar_filtro_manual(imagen_gris, nombre_filtro, tamano_ventana=3):
    if nombre_filtro == "Filtro de media":
        return filtro_media_manual(imagen_gris, tamano_ventana)
    if nombre_filtro == "Filtro de mediana":
        return filtro_mediana_manual(imagen_gris, tamano_ventana)
    if nombre_filtro == "Filtro de moda":
        return filtro_moda_manual(imagen_gris, tamano_ventana)
    raise ValueError("Filtro no reconocido")
