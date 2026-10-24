"""Datos de la gráfica: puntos de la curva, rango del eje, marcas y área sombreada."""

import math


CHART_POINTS = 200


def chart_ticks(start, end):
    raw_step = (end - start) / 10
    power = 10 ** math.floor(math.log10(raw_step))
    for multiple in (1, 2, 5, 10):
        step = multiple * power
        if step >= raw_step:
            break
    ticks = []
    for i in range(math.ceil(start / step), math.floor(end / step) + 1):
        ticks.append(round(i * step, 10))
    return ticks


def make_chart(dist, shaded, marks):
    if dist.symmetric:
        # El eje va de -limit a limit: lo justo para ver las marcas, entre 4 y 8
        farthest = 0
        for mark in marks:
            farthest = max(farthest, abs(mark))
        limit = min(max(4, math.ceil(farthest + 1)), 8)
        start, end = -limit, limit
    else:
        # χ² y F empiezan en 0. Se muestra hasta un poco después de las marcas,
        # pero sin pasar del punto que deja el 99.9% del área a la izquierda
        start = 0
        end = max(dist.quantile(0.99), max(marks) * 1.15)
        end = min(end, dist.quantile(0.999))

    xs = []
    for i in range(CHART_POINTS + 1):
        xs.append(start + (end - start) * i / CHART_POINTS)
    # Las marcas se agregan como puntos para que el área sombreada empiece justo en ellas
    for mark in marks:
        if start <= mark <= end and mark not in xs:
            xs.append(mark)
    xs.sort()

    points = []
    for x in xs:
        points.append([x, dist.curve(x)])
    return {
        "axis": dist.axis,
        "start": start,
        "end": end,
        "ticks": chart_ticks(start, end),
        "points": points,
        "shaded": shaded,
        "marks": marks,
    }
