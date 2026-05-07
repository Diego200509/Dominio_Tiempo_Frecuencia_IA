import numpy as np

from logica.conversion import convertir_gris_a_rgb


def calcular_bounding_box_manual(imagen_binaria):
    alto, ancho = imagen_binaria.shape
    x_min = ancho
    x_max = -1
    y_min = alto
    y_max = -1

    for y in range(alto):
        for x in range(ancho):
            if int(imagen_binaria[y, x]) == 255:
                if x < x_min:
                    x_min = x
                if x > x_max:
                    x_max = x
                if y < y_min:
                    y_min = y
                if y > y_max:
                    y_max = y

    if x_max == -1:
        return None

    return x_min, y_min, x_max, y_max


def calcular_bounding_box_objeto_principal_manual(imagen_binaria):
    alto, ancho = imagen_binaria.shape
    visitado = np.zeros((alto, ancho), dtype=np.uint8)
    mejor_caja = None
    mejor_area = 0

    for y in range(alto):
        for x in range(ancho):
            if visitado[y, x] == 1 or int(imagen_binaria[y, x]) != 255:
                continue

            pila = [(x, y)]
            visitado[y, x] = 1
            x_min = x
            x_max = x
            y_min = y
            y_max = y
            area = 0

            while pila:
                actual_x, actual_y = pila.pop()
                area += 1

                if actual_x < x_min:
                    x_min = actual_x
                if actual_x > x_max:
                    x_max = actual_x
                if actual_y < y_min:
                    y_min = actual_y
                if actual_y > y_max:
                    y_max = actual_y

                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        if dx == 0 and dy == 0:
                            continue

                        vecino_x = actual_x + dx
                        vecino_y = actual_y + dy
                        if vecino_x < 0 or vecino_x >= ancho or vecino_y < 0 or vecino_y >= alto:
                            continue
                        if visitado[vecino_y, vecino_x] == 1:
                            continue
                        if int(imagen_binaria[vecino_y, vecino_x]) != 255:
                            continue

                        visitado[vecino_y, vecino_x] = 1
                        pila.append((vecino_x, vecino_y))

            if area > mejor_area:
                mejor_area = area
                mejor_caja = (x_min, y_min, x_max, y_max)

    return mejor_caja


def calcular_bounding_box_componentes_significativos_manual(imagen_binaria, fraccion_minima=0.08):
    alto, ancho = imagen_binaria.shape
    visitado = np.zeros((alto, ancho), dtype=np.uint8)
    componentes = []
    mayor_area = 0

    for y in range(alto):
        for x in range(ancho):
            if visitado[y, x] == 1 or int(imagen_binaria[y, x]) != 255:
                continue

            pila = [(x, y)]
            visitado[y, x] = 1
            x_min = x
            x_max = x
            y_min = y
            y_max = y
            area = 0

            while pila:
                actual_x, actual_y = pila.pop()
                area += 1

                if actual_x < x_min:
                    x_min = actual_x
                if actual_x > x_max:
                    x_max = actual_x
                if actual_y < y_min:
                    y_min = actual_y
                if actual_y > y_max:
                    y_max = actual_y

                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        if dx == 0 and dy == 0:
                            continue

                        vecino_x = actual_x + dx
                        vecino_y = actual_y + dy
                        if vecino_x < 0 or vecino_x >= ancho or vecino_y < 0 or vecino_y >= alto:
                            continue
                        if visitado[vecino_y, vecino_x] == 1:
                            continue
                        if int(imagen_binaria[vecino_y, vecino_x]) != 255:
                            continue

                        visitado[vecino_y, vecino_x] = 1
                        pila.append((vecino_x, vecino_y))

            componentes.append((area, x_min, y_min, x_max, y_max))
            if area > mayor_area:
                mayor_area = area

    if mayor_area == 0:
        return None

    area_minima = max(4, int(mayor_area * float(fraccion_minima)))
    caja_final = None

    for area, x_min, y_min, x_max, y_max in componentes:
        if area < area_minima:
            continue

        if caja_final is None:
            caja_final = [x_min, y_min, x_max, y_max]
        else:
            if x_min < caja_final[0]:
                caja_final[0] = x_min
            if y_min < caja_final[1]:
                caja_final[1] = y_min
            if x_max > caja_final[2]:
                caja_final[2] = x_max
            if y_max > caja_final[3]:
                caja_final[3] = y_max

    if caja_final is None:
        return calcular_bounding_box_objeto_principal_manual(imagen_binaria)

    return tuple(caja_final)


def calcular_perimetro_componente_manual(imagen_binaria, pixeles):
    alto, ancho = imagen_binaria.shape
    perimetro = 0

    for x, y in pixeles:
        es_borde = False
        vecinos = ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))

        for vecino_x, vecino_y in vecinos:
            if vecino_x < 0 or vecino_x >= ancho or vecino_y < 0 or vecino_y >= alto:
                es_borde = True
            elif int(imagen_binaria[vecino_y, vecino_x]) != 255:
                es_borde = True

        if es_borde:
            perimetro += 1

    return perimetro


def detectar_objetos_manual(imagen_binaria, fraccion_minima=0.08):
    alto, ancho = imagen_binaria.shape
    visitado = np.zeros((alto, ancho), dtype=np.uint8)
    componentes = []
    mayor_area = 0

    for y in range(alto):
        for x in range(ancho):
            if visitado[y, x] == 1 or int(imagen_binaria[y, x]) != 255:
                continue

            pila = [(x, y)]
            pixeles = []
            visitado[y, x] = 1
            x_min = x
            x_max = x
            y_min = y
            y_max = y

            while pila:
                actual_x, actual_y = pila.pop()
                pixeles.append((actual_x, actual_y))

                if actual_x < x_min:
                    x_min = actual_x
                if actual_x > x_max:
                    x_max = actual_x
                if actual_y < y_min:
                    y_min = actual_y
                if actual_y > y_max:
                    y_max = actual_y

                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        if dx == 0 and dy == 0:
                            continue

                        vecino_x = actual_x + dx
                        vecino_y = actual_y + dy
                        if vecino_x < 0 or vecino_x >= ancho or vecino_y < 0 or vecino_y >= alto:
                            continue
                        if visitado[vecino_y, vecino_x] == 1:
                            continue
                        if int(imagen_binaria[vecino_y, vecino_x]) != 255:
                            continue

                        visitado[vecino_y, vecino_x] = 1
                        pila.append((vecino_x, vecino_y))

            area = len(pixeles)
            if area > mayor_area:
                mayor_area = area
            componentes.append((area, x_min, y_min, x_max, y_max, pixeles))

    if mayor_area == 0:
        return []

    area_minima = max(4, int(mayor_area * float(fraccion_minima)))
    objetos = []

    for area, x_min, y_min, x_max, y_max, pixeles in componentes:
        if area < area_minima:
            continue

        objetos.append(
            {
                "x": x_min,
                "y": y_min,
                "ancho": x_max - x_min + 1,
                "alto": y_max - y_min + 1,
                "area": area,
                "perimetro": calcular_perimetro_componente_manual(imagen_binaria, pixeles),
            }
        )

    objetos.sort(key=lambda objeto: (objeto["y"], objeto["x"]))
    return objetos


def dibujar_bounding_box_manual(imagen_base, caja, color=(255, 0, 0), grosor=3):
    if imagen_base.ndim == 2:
        salida = convertir_gris_a_rgb(imagen_base)
    else:
        salida = np.copy(imagen_base).astype(np.uint8)

    if caja is None:
        return salida

    alto, ancho, _ = salida.shape
    x_min, y_min, x_max, y_max = caja

    x_min = max(0, min(ancho - 1, int(x_min)))
    x_max = max(0, min(ancho - 1, int(x_max)))
    y_min = max(0, min(alto - 1, int(y_min)))
    y_max = max(0, min(alto - 1, int(y_max)))
    mitad = max(0, int(grosor) // 2)

    for desplazamiento in range(-mitad, mitad + 1):
        y_arriba = y_min + desplazamiento
        y_abajo = y_max + desplazamiento
        if 0 <= y_arriba < alto:
            for x in range(x_min, x_max + 1):
                salida[y_arriba, x, 0] = color[0]
                salida[y_arriba, x, 1] = color[1]
                salida[y_arriba, x, 2] = color[2]
        if 0 <= y_abajo < alto:
            for x in range(x_min, x_max + 1):
                salida[y_abajo, x, 0] = color[0]
                salida[y_abajo, x, 1] = color[1]
                salida[y_abajo, x, 2] = color[2]

        x_izquierda = x_min + desplazamiento
        x_derecha = x_max + desplazamiento
        if 0 <= x_izquierda < ancho:
            for y in range(y_min, y_max + 1):
                salida[y, x_izquierda, 0] = color[0]
                salida[y, x_izquierda, 1] = color[1]
                salida[y, x_izquierda, 2] = color[2]
        if 0 <= x_derecha < ancho:
            for y in range(y_min, y_max + 1):
                salida[y, x_derecha, 0] = color[0]
                salida[y, x_derecha, 1] = color[1]
                salida[y, x_derecha, 2] = color[2]

    return salida.astype(np.uint8)


def dibujar_bounding_boxes_manual(imagen_base, objetos, color=(255, 0, 0), grosor=3):
    if imagen_base.ndim == 2:
        salida = convertir_gris_a_rgb(imagen_base)
    else:
        salida = np.copy(imagen_base).astype(np.uint8)

    for objeto in objetos:
        caja = (
            objeto["x"],
            objeto["y"],
            objeto["x"] + objeto["ancho"] - 1,
            objeto["y"] + objeto["alto"] - 1,
        )
        salida = dibujar_bounding_box_manual(salida, caja, color=color, grosor=grosor)

    return salida.astype(np.uint8)


def detectar_y_dibujar_bounding_box_manual(imagen_binaria, imagen_base, grosor=3):
    objetos = detectar_objetos_manual(imagen_binaria)
    imagen_con_caja = dibujar_bounding_boxes_manual(imagen_base, objetos, grosor=grosor)
    return objetos, imagen_con_caja
